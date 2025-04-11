# Affectra - AI-Powered Emotional Analytics for Art Engagement

![Affectra Logo](assets/affectra-logo.png)

**Affectra** is an AI-powered interactive system that observes and interprets the emotional engagement of individuals while they view visual art.  
Leveraging real-time facial expression analysis and session-based emotion tracking, Affectra captures subtle affective responses, measures viewing duration, and compiles emotion distributions for each viewer interaction.

The system is designed for environments such as galleries, exhibitions, or interactive installations, where understanding human emotional resonance with art is valuable.  
By bridging machine learning with art perception, Affectra aims to create a dialogue between human emotion and digital observation — offering artists, curators, and researchers novel insights into audience experience.

It also provides a foundation for future work in affective computing, audience analytics, and human-centered AI in cultural spaces.

---

## 🖼️ Design Concept

> The following image illustrates how Affectra could appear in a real-world setting.

<!-- ![Affectra Screenshot](assets/affectra-image.png) -->
<img src="assets/affectra-image.png" alt="Affectra Screenshot" width="500"/>

---

## ✨ Features

- Real-time face detection and emotion analysis  
- Session tracking with emotion distribution summary  
- Web UI for live monitoring and data visualization  
- CSV-based logging of historical emotion data  
- Tracks total number of visitors (sessions)  
- Option to clear stored data when needed  


---

## 🔐 Security Features

This project includes several application-level security measures:

- CSRF protection for all form submissions  
- Secure HTTP headers (CSP, HSTS, X-Content-Type-Options, X-Frame-Options)  
- Input validation and sanitization to prevent injection attacks  
- Symmetric encryption using Fernet for sensitive data  
- Robust error handling and sanitized structured logging  
- Directory permission checks and secure file operations  

---

## ⚙️ Requirements

- Python 3.7+
- Flask
- OpenCV
- DeepFace
- Pandas
- NumPy

---

## 🚀 Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Ensure your webcam is connected and accessible.


---

## 🖥️ Running the Application


```bash
python run_app.py
```


Then open your browser and visit:

[http://localhost:5000](http://localhost:5000)

---

## 🎛️ Using the Interface

- **Live Feed**: Left panel shows real-time camera feed with face and emotion labels  
- **Session Statistics**: Right panel shows:
  - Total number of visitors
  - Most frequent emotion
  - Average session duration
  - Emotion distribution as percentages
- **Controls**:
  - 🔄 Refresh Statistics
  - 🧹 Clear All Data (with confirmation)

---


## 🧠 How It Works

1. Camera captures frames from webcam
2. DeepFace detects faces and classifies emotions  
3. Affectra tracks each viewer session and logs:
   - Session start/end time
   - Duration in seconds
   - Emotion percentages
4. Web UI reads from CSV and updates statistics in real-time

---




![It works on my machine](assets/it-works-badge.png)