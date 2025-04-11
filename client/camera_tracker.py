import cv2
import time
from deepface import DeepFace
from client.emotion_utils import EmotionSession
import requests
import numpy as np

class CameraTracker:
    """
    Main class for tracking faces, detecting emotions, and managing emotion sessions.
    Uses computer vision and DeepFace for real-time emotion analysis.
    """
    def __init__(self):
        # Session tracking variables
        self.session = None
        self.session_counter = 0
        
        # Timing configuration
        self.detection_interval = 2  # seconds between emotion detections
        self.last_detection_time = 0
        self.no_face_start_time = None
        self.no_face_threshold = 1.5  # seconds until session ends after face disappears
        
        # State variables
        self.face_detected = False
        self.current_frame = None
        self.current_emotion = None
        self.face_region = None

    def process_frame(self, frame):
        """
        Process a single video frame for emotion detection and tracking.
        
        Args:
            frame: Video frame from camera feed (numpy array)
            
        Returns:
            Processed frame with visualization elements added
        """
        # Store current frame for reference
        self.current_frame = frame.copy()
        current_time = time.time()

        try:
            # Detect face and analyze emotions using DeepFace
            result = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=True)
            dominant_emotion = result[0]['dominant_emotion']
            self.current_emotion = dominant_emotion
            region = result[0].get('region')
            self.face_region = region
            self.face_detected = True

            # Start a new session if none exists
            if self.session is None:
                self.session_counter += 1
                self.session = EmotionSession()
                self.session.start()
                print(f"📍 Session started.")
                print(f"👤 New person detected → Session #{self.session_counter} started.")

            # Draw face rectangle and emotion label on the frame
            if region:
                x, y, w, h = region['x'], region['y'], region['w'], region['h']
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, dominant_emotion, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # Add emotion to session at regular intervals
            if current_time - self.last_detection_time >= self.detection_interval:
                self.session.add_emotion(dominant_emotion)
                print(f"🧠 Detected Emotion: {dominant_emotion}")
                self.last_detection_time = current_time

            # Reset no-face timer since face is detected
            self.no_face_start_time = None  

        except Exception:
            # No face detected in this frame
            self.face_detected = False
            self.current_emotion = None
            self.face_region = None

            # Handle session end if face disappears for too long
            if self.session:
                # Start or continue tracking time without a face
                if self.no_face_start_time is None:
                    self.no_face_start_time = time.time()
                # End session if face has been absent beyond threshold
                elif time.time() - self.no_face_start_time > self.no_face_threshold:
                    self.session.end()
                    print(f"📍 Session ended.")
                    summary = self.session.get_summary()
                    if summary:
                        # Send data to the Flask server
                        try:
                            response = requests.post("http://localhost:5000/log", json=summary)
                            if response.status_code == 200:
                                print("✅ Session data sent to server.")
                            else:
                                print(f"⚠️ Failed to send data. Status: {response.status_code}")
                        except Exception as e:
                            print(f"⚠️ Error sending data to server: {e}")

                        # Print session summary to console
                        print(f"\n📋 Session #{self.session_counter} Summary:")
                        print(f"🧾 Timestamp: {summary['timestamp']}")
                        print(f"⏱ Duration: {summary['duration_seconds']} sec")
                        print(f"😶 Dominant Emotion: {summary['dominant_emotion']}")
                        print("📊 Emotion Percentages:")
                        for emotion, pct in summary['emotion_percentages'].items():
                            print(f"   - {emotion}: {pct}%")
                    else:
                        print(f"\n📋 Session #{self.session_counter} Summary: ⚠️ No emotion data.")
                    print("—" * 40)

                    # Reset session after ending
                    self.session = None
                    self.no_face_start_time = None

        return frame

    def get_current_frame(self):
        """
        Return the current processed frame.
        
        Returns:
            The last processed video frame or blank frame if none exists
        """
        if self.current_frame is not None:
            return self.current_frame
        return np.zeros((480, 640, 3), dtype=np.uint8)  # Return blank frame if none available

    def get_current_emotion(self):
        """
        Return the current detected emotion.
        
        Returns:
            String representing the current emotion or None if no face detected
        """
        return self.current_emotion

def start_camera():
    """
    Standalone function to start the camera and emotion tracking.
    Creates a window showing the processed camera feed with emotions.
    """
    # Initialize camera
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot access the camera.")
        return

    print("🎥 Affectra session tracking (DeepFace-based) started. Press 'q' to quit.")
    
    # Create tracker instance
    tracker = CameraTracker()

    # Main processing loop
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to grab frame.")
            break

        # Process frame with emotion detection
        processed_frame = tracker.process_frame(frame)
        cv2.imshow("Affectra Camera Feed", processed_frame)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("👋 Exiting...")
            break

    # Clean up resources
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_camera()
