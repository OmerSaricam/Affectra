import cv2
import time
from deepface import DeepFace
from client.emotion_utils import EmotionSession

def start_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot access the camera.")
        return

    print("🎥 Affectra session tracking (DeepFace-based) started. Press 'q' to quit.")

    session = None
    session_counter = 0
    detection_interval = 2  # seconds
    last_detection_time = 0
    no_face_start_time = None
    no_face_threshold = 1.5
    face_detected = False

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to grab frame.")
            break

        current_time = time.time()

        try:
            result = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=True)
            dominant_emotion = result[0]['dominant_emotion']
            region = result[0].get('region')
            face_detected = True

            # Eğer aktif bir session yoksa yeni başlat
            if session is None:
                session_counter += 1
                session = EmotionSession()
                session.start()
                print(f"📍 Session started.")
                print(f"👤 New person detected → Session #{session_counter} started.")

            # Duygu metni ve çerçeve çizimi
            if region:
                x, y, w, h = region['x'], region['y'], region['w'], region['h']
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, dominant_emotion, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

            # Her 2 saniyede bir duygu ekle
            if current_time - last_detection_time >= detection_interval:
                session.add_emotion(dominant_emotion)
                print(f"🧠 Detected Emotion: {dominant_emotion}")
                last_detection_time = current_time

            no_face_start_time = None  # yüz görünüyor

        except Exception:
            face_detected = False
            #print(f"⚠️ Face not detected: {e}")

            if session:
                if no_face_start_time is None:
                    no_face_start_time = time.time()
                elif time.time() - no_face_start_time > no_face_threshold:
                    session.end()
                    print(f"📍 Session ended.")
                    summary = session.get_summary()
                    if summary:
                        print(f"\n📋 Session #{session_counter} Summary:")
                        print(f"🧾 Timestamp: {summary['timestamp']}")
                        print(f"⏱ Duration: {summary['duration_seconds']} sec")
                        print(f"😶 Dominant Emotion: {summary['dominant_emotion']}")
                        print("📊 Emotion Percentages:")
                        for emotion, pct in summary['emotion_percentages'].items():
                            print(f"   - {emotion}: {pct}%")
                    else:
                        print(f"\n📋 Session #{session_counter} Summary: ⚠️ No emotion data.")
                    print("—" * 40)

                    session = None
                    no_face_start_time = None

        cv2.imshow("Affectra Camera Feed", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("👋 Exiting...")
            break

    cap.release()
    cv2.destroyAllWindows()
