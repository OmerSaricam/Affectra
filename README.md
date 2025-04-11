# Affectra Emotion Tracking Web UI

This application provides a web-based user interface for emotion tracking using computer vision. It detects faces, analyzes emotions, and visualizes the emotion statistics over time.

## Features

- Real-time face detection and emotion analysis
- Tracks emotion sessions and calculates statistics
- Web UI for monitoring and visualization
- Stores historical emotion data

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
  - Dominant emotion across all sessions
  - Average session duration
  - Distribution of emotions as percentages
- The "Refresh Statistics" button updates the statistics from the latest data

## How It Works

1. The camera captures video frames
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
  - `camera_tracker.py`: Camera and emotion detection
  - `emotion_utils.py`: Session tracking utilities

## Troubleshooting

- If the camera doesn't start, make sure it's not being used by another application
- If emotions aren't detected, try adjusting lighting or positioning
- If the web interface doesn't display, check that the server is running correctly
