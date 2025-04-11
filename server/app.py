from flask import Flask, request, jsonify, render_template, Response, session, abort
import os
import pandas as pd
from datetime import datetime
import json
import cv2
import numpy as np
import sys
import time
import secrets
import logging

# Get the absolute path for the logs directory
current_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(current_dir, "logs")
log_file = os.path.join(log_dir, "app.log")

# Ensure logs directory exists before setting up logging
os.makedirs(log_dir, exist_ok=True)

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("affectra")

# Add the project root to the path so we can import the client modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from client.camera_tracker import CameraTracker
from client.security import get_api_key, verify_signature, DataEncryption
from client.camera_provider import CameraManager, create_webcam_source, create_esp32cam_source

# Initialize Flask application with proper folder configuration
app = Flask(__name__, 
            static_folder="static",
            template_folder="templates")

# Set a secret key for session management
app.secret_key = secrets.token_hex(16)

# Generate a CSRF token on first visit and store in session
def get_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(16)
    return session['csrf_token']

# Path to the CSV file for storing emotion session data
storage_dir = os.path.join(current_dir, "storage")
LOG_PATH = os.path.join(storage_dir, "affectra_log.csv")

# Create the CSV file with headers if it doesn't exist
if not os.path.exists(LOG_PATH):
    os.makedirs(storage_dir, exist_ok=True)
    df = pd.DataFrame(columns=[
        "timestamp",
        "duration_seconds",
        "dominant_emotion",
        "emotion_percentages"
    ])
    df.to_csv(LOG_PATH, index=False)

# Initialize encryption
encryption = DataEncryption()

@app.after_request
def add_security_headers(response):
    """Add security headers to all responses."""
    # Prevent content type sniffing
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # Block XSS attacks
    response.headers['X-XSS-Protection'] = '1; mode=block'
    # Prevent clickjacking
    response.headers['X-Frame-Options'] = 'DENY'
    # Set content security policy
    response.headers['Content-Security-Policy'] = "default-src 'self'; img-src 'self' data:; style-src 'self' https://cdn.jsdelivr.net; script-src 'self' https://cdn.jsdelivr.net;"
    return response

@app.route("/log", methods=["POST"])
def log_emotion():
    """
    API endpoint for receiving and logging emotion data from the client.
    Accepts JSON data containing emotion session information and saves it to CSV.
    
    Expected JSON data:
        - timestamp: When the session occurred
        - duration_seconds: How long the session lasted
        - dominant_emotion: Most frequent emotion detected
        - emotion_percentages: Distribution of emotions as percentages
    
    Returns:
        JSON response indicating success or failure
    """
    try:
        data = request.get_json()
        if not data:
            logger.warning("Received empty request data")
            return jsonify({"status": "error", "message": "No data received"}), 400

        # Validate required fields
        required_fields = ["timestamp", "duration_seconds", "dominant_emotion", "emotion_percentages"]
        for field in required_fields:
            if field not in data:
                logger.warning(f"Missing required field: {field}")
                return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400

        # Convert emotion percentages dictionary to string format for CSV storage
        percentages = data.get("emotion_percentages", {})
        percentages_str = ", ".join([f"{k}: {v}%" for k, v in percentages.items()])

        # Prepare row data for CSV
        row = {
            "timestamp": data.get("timestamp", datetime.now().isoformat()),
            "duration_seconds": data.get("duration_seconds", 0),
            "dominant_emotion": data.get("dominant_emotion", "unknown"),
            "emotion_percentages": percentages_str
        }

        # Append the new data to the CSV file
        df = pd.read_csv(LOG_PATH)
        df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
        df.to_csv(LOG_PATH, index=False)

        logger.info(f"Logged emotion session: {row['dominant_emotion']}, duration: {row['duration_seconds']}s")
        return jsonify({"status": "ok", "message": "Session logged"})
    except Exception as e:
        logger.error(f"Error logging emotion data: {str(e)}")
        return jsonify({"status": "error", "message": f"Server error: {str(e)}"}), 500

@app.route('/')
def index():
    """
    Serve the main web interface for the application.
    
    Returns:
        Rendered HTML template for the UI
    """
    # Include CSRF token in the template
    return render_template('index.html', csrf_token=get_csrf_token())

@app.route('/api/emotion_stats')
def emotion_stats():
    """
    API endpoint to retrieve analyzed emotion statistics.
    Reads from the CSV log file and calculates aggregate statistics.
    
    Returns:
        JSON containing:
        - Average session duration
        - Overall dominant emotion
        - Average percentages for each emotion
        - Total visitor count
        - Empty state flag
    """
    try:
        df = pd.read_csv(LOG_PATH)
        
        if df.empty:
            # Return default values for empty data instead of an error
            return jsonify({
                "status": "ok",
                "avg_duration": 0,
                "overall_dominant_emotion": "none",
                "avg_emotion_percentages": {},
                "visitor_count": 0,
                "is_empty": True
            })
        
        # Calculate average duration
        avg_duration = df['duration_seconds'].mean()
        
        # Find overall dominant emotion
        dominant_emotions = df['dominant_emotion'].value_counts()
        overall_dominant = dominant_emotions.idxmax() if not dominant_emotions.empty else "unknown"
        
        # Parse and aggregate emotion percentages
        # This needs to be fixed to ensure percentages are calculated correctly
        all_emotions = {}
        total_observations = 0
        
        # First pass: collect all emotions and count total observations
        for percentages_str in df['emotion_percentages']:
            for item in percentages_str.split(','):
                parts = item.strip().split(':')
                if len(parts) == 2:
                    emotion = parts[0].strip()
                    value_str = parts[1].strip(' %')
                    try:
                        value = float(value_str)
                        # Initialize emotion counter if not exists
                        if emotion not in all_emotions:
                            all_emotions[emotion] = 0
                        # Add weighted value based on percentage
                        all_emotions[emotion] += value
                        total_observations += value
                    except ValueError:
                        logger.warning(f"Could not parse emotion value: {value_str}")
        
        # Calculate final percentages
        if total_observations > 0:
            avg_percentages = {
                emotion: round((count / total_observations) * 100, 1) 
                for emotion, count in all_emotions.items()
            }
        else:
            avg_percentages = {}
        
        # Count number of visitors (rows in CSV)
        visitor_count = len(df)
        
        return jsonify({
            "status": "ok",
            "avg_duration": round(avg_duration, 2),
            "overall_dominant_emotion": overall_dominant,
            "avg_emotion_percentages": avg_percentages,
            "visitor_count": visitor_count,
            "is_empty": False
        })
    
    except Exception as e:
        logger.error(f"Error retrieving emotion stats: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/clear_data', methods=["POST"])
def clear_data():
    """
    API endpoint to clear all stored emotion data.
    Creates a new empty CSV file with only the headers.
    
    Returns:
        JSON response indicating success or failure
    """
    try:
        # Verify CSRF token for protection against CSRF attacks
        csrf_token = request.headers.get('X-CSRF-Token')
        if not csrf_token or csrf_token != session.get('csrf_token'):
            logger.warning("CSRF verification failed")
            return jsonify({"status": "error", "message": "Invalid request"}), 403
        
        # Create an empty DataFrame with the same columns
        df = pd.DataFrame(columns=[
            "timestamp",
            "duration_seconds",
            "dominant_emotion",
            "emotion_percentages"
        ])
        # Write the empty DataFrame to the CSV file
        df.to_csv(LOG_PATH, index=False)
        
        logger.info("Data cleared successfully")
        return jsonify({
            "status": "ok",
            "message": "Data cleared successfully"
        })
    except Exception as e:
        logger.error(f"Error clearing data: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Initialize camera tracker
camera_tracker = None

def init_camera_tracker():
    """
    Initialize or return the existing camera tracker instance.
    Uses a global variable to maintain the same tracker across requests.
    
    Returns:
        An instance of CameraTracker
    """
    global camera_tracker
    if camera_tracker is None:
        camera_tracker = CameraTracker()
    return camera_tracker

# Camera manager for different video sources
camera_manager = None

def init_camera_manager():
    """
    Initialize or return the existing camera manager instance.
    Uses a global variable to maintain the same camera manager across requests.
    
    Returns:
        An instance of CameraManager
    """
    global camera_manager
    if camera_manager is None:
        camera_manager = CameraManager()
        # Add default webcam source
        webcam = create_webcam_source(0, "Default_Webcam")
        camera_manager.add_source(webcam)
        camera_manager.set_active_source("Default_Webcam")
        
        # Load any configured camera sources from settings
        # For now, we'll add a placeholder for ESP32-CAM if URL is in environment
        esp32_url = os.environ.get('ESP32_CAM_URL')
        if esp32_url:
            try:
                esp32 = create_esp32cam_source(esp32_url)
                camera_manager.add_source(esp32)
                logger.info(f"Added ESP32-CAM source: {esp32.name}")
            except Exception as e:
                logger.error(f"Failed to initialize ESP32-CAM: {e}")
    
    return camera_manager

def gen_frames():
    """
    Generator function to continuously yield video frames.
    Processes each frame with emotion detection before yielding.
    Used by the video_feed route to implement streaming.
    
    Yields:
        JPEG image data of each processed frame
    """
    manager = init_camera_manager()
    tracker = init_camera_tracker()
    
    while True:
        success, frame = manager.read()
        if not success:
            # Wait briefly before trying again
            time.sleep(0.1)
            continue
        else:
            try:
                # Process frame with emotion tracker
                processed_frame = tracker.process_frame(frame)
                
                # Add current emotion text if available
                current_emotion = tracker.get_current_emotion()
                if current_emotion:
                    cv2.putText(processed_frame, 
                                f"Current: {current_emotion}", 
                                (10, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 
                                1, 
                                (0, 255, 0), 
                                2)
                
                # Add camera source info
                active_camera = manager.active_source_name
                if active_camera:
                    cv2.putText(processed_frame, 
                                f"Camera: {active_camera}", 
                                (10, processed_frame.shape[0] - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 
                                0.6, 
                                (255, 255, 255), 
                                1)
                
                # Convert frame to jpg format
                ret, buffer = cv2.imencode('.jpg', processed_frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                logger.error(f"Error generating frame: {e}")
                time.sleep(0.1)

@app.route('/video_feed')
def video_feed():
    """
    Endpoint to stream the processed video feed.
    Uses multipart response to continuously stream JPEG images.
    
    Returns:
        Streaming response with processed camera frames
    """
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/cameras')
def list_cameras():
    """
    List available camera sources
    
    Returns:
        JSON list of available cameras and the active camera
    """
    manager = init_camera_manager()
    sources = list(manager.sources.keys())
    active = manager.active_source_name
    
    return jsonify({
        "available_cameras": sources,
        "active_camera": active
    })

@app.route('/select_camera', methods=['POST'])
def select_camera():
    """
    Select a camera source
    
    Returns:
        JSON response indicating success or failure
    """
    # Verify CSRF token
    token = request.form.get('csrf_token')
    if not token or token != session.get('csrf_token'):
        abort(403)
    
    camera_name = request.form.get('camera_name')
    if not camera_name:
        return jsonify({"success": False, "error": "No camera name provided"}), 400
    
    manager = init_camera_manager()
    if camera_name not in manager.sources:
        return jsonify({"success": False, "error": f"Camera '{camera_name}' not found"}), 404
    
    success = manager.set_active_source(camera_name)
    
    if success:
        return jsonify({"success": True, "message": f"Switched to camera: {camera_name}"})
    else:
        return jsonify({"success": False, "error": f"Failed to switch to camera: {camera_name}"}), 500

@app.route('/add_esp32_camera', methods=['POST'])
def add_esp32_camera():
    """
    Add a new ESP32-CAM source
    
    Returns:
        JSON response indicating success or failure
    """
    # Verify CSRF token
    token = request.form.get('csrf_token')
    if not token or token != session.get('csrf_token'):
        abort(403)
    
    url = request.form.get('url')
    name = request.form.get('name')
    
    if not url:
        return jsonify({"success": False, "error": "No camera URL provided"}), 400
    
    try:
        manager = init_camera_manager()
        
        # Create ESP32-CAM source
        esp32 = create_esp32cam_source(url, name)
        
        # Check if a source with this name already exists
        if esp32.name in manager.sources:
            return jsonify({"success": False, "error": f"Camera '{esp32.name}' already exists"}), 400
        
        # Add the source
        manager.add_source(esp32)
        
        return jsonify({
            "success": True, 
            "message": f"Added ESP32-CAM source: {esp32.name}",
            "camera_name": esp32.name
        })
    
    except Exception as e:
        logger.error(f"Error adding ESP32-CAM: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    logger.info("Starting Affectra application server")
    app.run(port=5000, debug=True)
