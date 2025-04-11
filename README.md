# Affectra Emotion Tracking Web UI

This application provides a web-based user interface for emotion tracking using computer vision. It detects faces, analyzes emotions, and visualizes the emotion statistics over time.

## Features

- Real-time face detection and emotion analysis
- Tracks emotion sessions and calculates statistics
- Web UI for monitoring and visualization
- Stores historical emotion data
- Counts total number of visitors (sessions)
- Option to clear stored data when needed
- Support for multiple camera sources:
  - Local webcam 
  - ESP32-CAM external camera

## Requirements

- Python 3.7+
- OpenCV
- DeepFace
- Flask
- Pandas
- NumPy

## Setup

1. Install the required dependencies:

```bash
pip install flask pandas numpy opencv-python deepface requests
```

2. Make sure your webcam is connected and accessible

3. (Optional) To use an ESP32-CAM:
   - Flash the ESP32-CAM with the code from `esp32_cam/esp32_cam_streaming.ino`
   - Update the WiFi credentials in the ESP32-CAM code
   - Connect the ESP32-CAM to your network
   - Note the IP address of the ESP32-CAM

## Running the Application

Run the application with:

```bash
python run_app.py
```

Then open your browser and visit:

```
http://localhost:5000
```

## Using the Interface

- The left panel shows the live camera feed with face detection and emotion labeling
- The right panel displays statistics calculated from the stored emotion data:
  - Total number of visitors (sessions)
  - Dominant emotion across all sessions
  - Average session duration
  - Distribution of emotions as percentages
- Data Management section:
  - "Refresh Statistics" button updates the statistics from the latest data
  - "Clear All Data" button removes all stored emotion data (with confirmation)
- Camera Selection section:
  - Switch between webcam and ESP32-CAM sources
  - Add new ESP32-CAM sources by providing their stream URL

## Using ESP32-CAM

1. Flash the ESP32-CAM with the provided Arduino code
2. Connect the ESP32-CAM to the same network as the computer running Affectra
3. Note the IP address displayed on the ESP32-CAM's serial monitor
4. In the Affectra web interface, click "Add ESP32-CAM" and enter the stream URL:
   `http://<ESP32-CAM_IP>/stream`
5. Select the ESP32-CAM from the camera list to switch to it

## How It Works

1. The camera captures video frames from either webcam or ESP32-CAM
2. DeepFace analyzes each frame to detect faces and emotions
3. Emotion data is tracked in sessions and saved to a CSV file
4. The web UI reads this data and calculates statistics for display

## Project Structure

- `server/`: Contains the Flask web server
  - `app.py`: Main server code
  - `templates/`: HTML templates
  - `static/`: CSS and JavaScript files
  - `storage/`: CSV data storage
- `client/`: Contains the emotion tracking code
  - `camera_tracker.py`: Analyzes emotions from video frames
  - `camera_provider.py`: Manages different camera sources
  - `emotion_utils.py`: Utilities for emotion tracking
- `esp32_cam/`: Contains Arduino code for ESP32-CAM streaming

## Troubleshooting

- If the camera doesn't start, make sure it's not being used by another application
- If emotions aren't detected, try adjusting lighting or positioning
- If the web interface doesn't display, check that the server is running correctly
