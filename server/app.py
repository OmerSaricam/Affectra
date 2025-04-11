from flask import Flask, request, jsonify, render_template, Response
import os
import pandas as pd
from datetime import datetime
import json
import cv2
import numpy as np
import sys
import time

# Add the project root to the path so we can import the client modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from client.camera_tracker import CameraTracker

app = Flask(__name__, 
            static_folder="static",
            template_folder="templates")

LOG_PATH = "server/storage/affectra_log.csv"

# CSV dosyası yoksa başlıkla oluştur
if not os.path.exists(LOG_PATH):
    df = pd.DataFrame(columns=[
        "timestamp",
        "duration_seconds",
        "dominant_emotion",
        "emotion_percentages"
    ])
    df.to_csv(LOG_PATH, index=False)

@app.route("/log", methods=["POST"])
def log_emotion():
    data = request.get_json()
    if not data:
        return jsonify({"status": "error", "message": "No data received"}), 400

    # Yüzdeleri string'e çevir (JSON.stringify'den gelen dict)
    percentages = data.get("emotion_percentages", {})
    percentages_str = ", ".join([f"{k}: {v}%" for k, v in percentages.items()])

    row = {
        "timestamp": data.get("timestamp", datetime.now().isoformat()),
        "duration_seconds": data.get("duration_seconds", 0),
        "dominant_emotion": data.get("dominant_emotion", "unknown"),
        "emotion_percentages": percentages_str
    }

    df = pd.read_csv(LOG_PATH)
    df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)
    df.to_csv(LOG_PATH, index=False)

    return jsonify({"status": "ok", "message": "Session logged"})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/emotion_stats')
def emotion_stats():
    try:
        df = pd.read_csv(LOG_PATH)
        
        if df.empty:
            return jsonify({
                "status": "error",
                "message": "No data available"
            }), 404
        
        # Calculate average duration
        avg_duration = df['duration_seconds'].mean()
        
        # Find overall dominant emotion
        dominant_emotions = df['dominant_emotion'].value_counts()
        overall_dominant = dominant_emotions.idxmax() if not dominant_emotions.empty else "unknown"
        
        # Parse and aggregate emotion percentages
        emotion_totals = {}
        for percentages_str in df['emotion_percentages']:
            percentages = {}
            for item in percentages_str.split(','):
                emotion, value = item.strip().split(':')
                emotion = emotion.strip()
                value = float(value.strip(' %'))
                if emotion not in emotion_totals:
                    emotion_totals[emotion] = []
                emotion_totals[emotion].append(value)
        
        # Calculate average percentage for each emotion
        avg_percentages = {emotion: sum(values)/len(values) for emotion, values in emotion_totals.items()}
        
        return jsonify({
            "status": "ok",
            "avg_duration": round(avg_duration, 2),
            "overall_dominant_emotion": overall_dominant,
            "avg_emotion_percentages": avg_percentages
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Initialize camera tracker
camera_tracker = None

def init_camera_tracker():
    global camera_tracker
    if camera_tracker is None:
        camera_tracker = CameraTracker()
    return camera_tracker

# Initialize camera
camera = None

def get_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0)
        # Wait for the camera to initialize
        time.sleep(1)
    return camera

def gen_frames():
    camera = get_camera()
    tracker = init_camera_tracker()
    
    while True:
        success, frame = camera.read()
        if not success:
            break
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
                
                # Convert frame to jpg format
                ret, buffer = cv2.imencode('.jpg', processed_frame)
                frame = buffer.tobytes()
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except Exception as e:
                print(f"Error generating frame: {e}")
                break

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(port=5000, debug=True)
