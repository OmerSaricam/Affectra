import cv2
import time
import requests
import numpy as np
import logging
import threading
import queue
from abc import ABC, abstractmethod
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("camera_provider")

class CameraSource(ABC):
    """
    Abstract base class for different camera sources.
    All camera implementations must extend this class.
    """
    def __init__(self, name="Camera"):
        self.name = name
        self.is_connected = False
        self._lock = threading.Lock()
    
    @abstractmethod
    def connect(self):
        """Connect to the camera source"""
        pass
    
    @abstractmethod
    def read(self):
        """
        Read a frame from the camera
        
        Returns:
            Tuple (success, frame) where success is a boolean and frame is a numpy array
        """
        pass
    
    @abstractmethod
    def release(self):
        """Release the camera resources"""
        pass
    
    def is_valid_frame(self, frame):
        """Check if a frame is valid"""
        return frame is not None and frame.size > 0 and len(frame.shape) == 3

class WebcamSource(CameraSource):
    """Camera source implementation for local webcam using OpenCV"""
    
    def __init__(self, camera_index=0, name="Webcam"):
        """
        Initialize webcam source
        
        Args:
            camera_index: Index of the webcam (default 0 for built-in webcam)
            name: Name identifier for this camera
        """
        super().__init__(name)
        self.camera_index = camera_index
        self.cap = None
    
    def connect(self):
        with self._lock:
            # Initialize camera
            if self.cap is None:
                self.cap = cv2.VideoCapture(self.camera_index)
                # Wait for the camera to initialize
                time.sleep(1)
                self.is_connected = self.cap.isOpened()
                if not self.is_connected:
                    logger.error(f"Failed to connect to webcam at index {self.camera_index}")
                else:
                    logger.info(f"Connected to webcam at index {self.camera_index}")
            return self.is_connected
    
    def read(self):
        with self._lock:
            if not self.is_connected or self.cap is None:
                if not self.connect():
                    return False, None
            
            success, frame = self.cap.read()
            if not success:
                logger.warning("Failed to read frame from webcam")
                # Try to reconnect
                self.release()
                time.sleep(0.5)
                self.connect()
                return False, None
            
            return success, frame
    
    def release(self):
        with self._lock:
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            self.is_connected = False
            logger.info("Webcam released")

class ESP32CamSource(CameraSource):
    """Camera source implementation for ESP32-CAM using HTTP streaming"""
    
    def __init__(self, url, name="ESP32-CAM", connection_timeout=10, read_timeout=5):
        """
        Initialize ESP32-CAM source
        
        Args:
            url: URL of the ESP32-CAM stream (e.g., 'http://192.168.1.123:81/stream')
            name: Name identifier for this camera
            connection_timeout: Timeout in seconds for connection attempts
            read_timeout: Timeout in seconds for read operations
        """
        super().__init__(name)
        self.url = url
        self.connection_timeout = connection_timeout
        self.read_timeout = read_timeout
        self.stream = None
        self.bytes_buffer = bytes()
        self._frame_queue = queue.Queue(maxsize=2)  # Small queue to avoid lag
        self._running = False
        self._thread = None
    
    def _stream_reader(self):
        """Background thread to read frames from the stream"""
        while self._running:
            try:
                if self.stream is None:
                    # Try to connect to the stream
                    self.stream = requests.get(
                        self.url, 
                        stream=True, 
                        timeout=(self.connection_timeout, self.read_timeout)
                    )
                    
                    if self.stream.status_code != 200:
                        logger.error(f"Failed to connect to ESP32-CAM at {self.url}. Status: {self.stream.status_code}")
                        self.stream = None
                        time.sleep(1)
                        continue
                    
                    with self._lock:
                        self.is_connected = True
                        logger.info(f"Connected to ESP32-CAM at {self.url}")
                
                # Process the multipart stream
                for chunk in self.stream.iter_content(chunk_size=1024):
                    if not self._running:
                        break
                    
                    if not chunk:
                        continue
                    
                    # Add the chunk to our buffer
                    self.bytes_buffer += chunk
                    
                    # Check for JPEG frame boundaries
                    a = self.bytes_buffer.find(b'\xff\xd8')  # JPEG start
                    b = self.bytes_buffer.find(b'\xff\xd9')  # JPEG end
                    
                    if a != -1 and b != -1 and a < b:
                        # Extract the JPEG image
                        jpg_data = self.bytes_buffer[a:b+2]
                        self.bytes_buffer = self.bytes_buffer[b+2:]
                        
                        # Decode the image
                        frame = cv2.imdecode(np.frombuffer(jpg_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                        
                        if self.is_valid_frame(frame):
                            # Put frame in queue, replacing old frame if queue is full
                            if self._frame_queue.full():
                                try:
                                    self._frame_queue.get_nowait()
                                except queue.Empty:
                                    pass
                            self._frame_queue.put(frame)
            
            except requests.RequestException as e:
                logger.error(f"Connection error with ESP32-CAM: {str(e)}")
                with self._lock:
                    self.is_connected = False
                    self.stream = None
                time.sleep(2)  # Wait before retry
            
            except Exception as e:
                logger.error(f"Error processing ESP32-CAM stream: {str(e)}")
                with self._lock:
                    self.is_connected = False
                    self.stream = None
                time.sleep(2)  # Wait before retry
    
    def connect(self):
        with self._lock:
            if self._running:
                return self.is_connected
            
            self._running = True
            self._thread = threading.Thread(target=self._stream_reader, daemon=True)
            self._thread.start()
            
            # Wait a bit for initial connection attempt
            time.sleep(1)
            return self.is_connected
    
    def read(self):
        if not self._running:
            if not self.connect():
                return False, None
        
        try:
            # Get the latest frame with a timeout
            frame = self._frame_queue.get(timeout=1.0)
            return True, frame
        except queue.Empty:
            return False, None
    
    def release(self):
        with self._lock:
            self._running = False
            
            if self.stream is not None:
                self.stream.close()
                self.stream = None
            
            self.is_connected = False
            
            # Clear the queue
            while not self._frame_queue.empty():
                try:
                    self._frame_queue.get_nowait()
                except queue.Empty:
                    break
            
            if self._thread and self._thread.is_alive():
                self._thread.join(timeout=1.0)
            
            logger.info(f"ESP32-CAM at {self.url} released")

class CameraManager:
    """
    Manager class to handle multiple camera sources.
    Provides a unified interface for accessing different camera types.
    """
    def __init__(self):
        self.sources = {}
        self.active_source = None
        self.active_source_name = None
    
    def add_source(self, source):
        """
        Add a camera source
        
        Args:
            source: CameraSource instance
        """
        self.sources[source.name] = source
        logger.info(f"Added camera source: {source.name}")
    
    def set_active_source(self, name):
        """
        Set the active camera source by name
        
        Args:
            name: Name of the camera source to activate
        
        Returns:
            bool: True if successful, False otherwise
        """
        if name not in self.sources:
            logger.error(f"Camera source '{name}' not found")
            return False
        
        # Release the current active source if different
        if self.active_source and self.active_source_name != name:
            self.active_source.release()
        
        # Set the new active source
        self.active_source = self.sources[name]
        self.active_source_name = name
        
        # Connect to the new source
        success = self.active_source.connect()
        if success:
            logger.info(f"Switched to camera source: {name}")
        return success
    
    def read(self):
        """
        Read a frame from the active camera source
        
        Returns:
            Tuple (success, frame) where success is a boolean and frame is a numpy array
        """
        if not self.active_source:
            logger.warning("No active camera source")
            return False, None
        
        return self.active_source.read()
    
    def release_all(self):
        """Release all camera sources"""
        for name, source in self.sources.items():
            source.release()
        self.active_source = None
        self.active_source_name = None
        logger.info("All camera sources released")

def create_webcam_source(camera_index=0, name=None):
    """
    Create a webcam source
    
    Args:
        camera_index: Index of the webcam
        name: Optional name for the source (default: Webcam_<index>)
    
    Returns:
        WebcamSource instance
    """
    if name is None:
        name = f"Webcam_{camera_index}"
    return WebcamSource(camera_index, name)

def create_esp32cam_source(url, name=None):
    """
    Create an ESP32-CAM source
    
    Args:
        url: URL of the ESP32-CAM stream
        name: Optional name for the source (default: ESP32CAM_<host>)
    
    Returns:
        ESP32CamSource instance
    """
    if name is None:
        # Extract hostname for default name
        try:
            parsed_url = urlparse(url)
            host = parsed_url.netloc.split(':')[0]
            name = f"ESP32CAM_{host}"
        except:
            name = "ESP32CAM"
    
    return ESP32CamSource(url, name) 