import cv2
import time
from deepface import DeepFace
from client.emotion_utils import EmotionSession
import requests
import numpy as np

class CameraTracker:
    def __init__(self):
        self.session = None
        self.session_counter = 0
        self.detection_interval = 2  # seconds
        self.last_detection_time = 0
        self.no_face_start_time = None
        self.no_face_threshold = 1.5
        self.face_detected = False
        self.current_frame = None
        self.current_emotion = None
        self.face_region = None

    def process_frame(self, frame):
        """Process a single frame, detect emotions, and update session data."""
        self.current_frame = frame.copy()
        current_time = time.time()

        try:
            result = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=True)
            dominant_emotion = result[0]['dominant_emotion']
            self.current_emotion = dominant_emotion
            region = result[0].get('region')
            self.face_region = region
            self.face_detected = True

            # Eğer aktif bir session yoksa yeni başlat
            if self.session is None:
                self.session_counter += 1
                self.session = EmotionSession()
                self.session.start()
                print(f"📍 Session started.")
                print(f"👤 New person detected → Session #{self.session_counter} started.")

            # Duygu metni ve çerçeve çizimi
            if region:
                x, y, w, h = region['x'], region['y'], region['w'], region['h']
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, dominant_emotion, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # Her 2 saniyede bir duygu ekle
            if current_time - self.last_detection_time >= self.detection_interval:
                self.session.add_emotion(dominant_emotion)
                print(f"🧠 Detected Emotion: {dominant_emotion}")
                self.last_detection_time = current_time

            self.no_face_start_time = None  # yüz görünüyor

        except Exception:
            self.face_detected = False
            self.current_emotion = None
            self.face_region = None

            if self.session:
                if self.no_face_start_time is None:
                    self.no_face_start_time = time.time()
                elif time.time() - self.no_face_start_time > self.no_face_threshold:
                    self.session.end()
                    print(f"📍 Session ended.")
                    summary = self.session.get_summary()
                    if summary:
                        # Veriyi Flask sunucusuna POST et
                        try:
                            response = requests.post("http://localhost:5000/log", json=summary)
                            if response.status_code == 200:
                                print("✅ Session data sent to server.")
                            else:
                                print(f"⚠️ Failed to send data. Status: {response.status_code}")
                        except Exception as e:
                            print(f"⚠️ Error sending data to server: {e}")

                        # Terminale yazdırmaya devam
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

                    self.session = None
                    self.no_face_start_time = None

        return frame

    def get_current_frame(self):
        """Return the current processed frame."""
        if self.current_frame is not None:
            return self.current_frame
        return np.zeros((480, 640, 3), dtype=np.uint8)  # Return blank frame if none available

    def get_current_emotion(self):
        """Return the current detected emotion."""
        return self.current_emotion

def start_camera():
    """Original standalone function to start the camera tracker."""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot access the camera.")
        return

    print("🎥 Affectra session tracking (DeepFace-based) started. Press 'q' to quit.")
    
    tracker = CameraTracker()

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to grab frame.")
            break

        processed_frame = tracker.process_frame(frame)
        cv2.imshow("Affectra Camera Feed", processed_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("👋 Exiting...")
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    start_camera()
