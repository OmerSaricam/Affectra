import cv2
from deepface import DeepFace

def start_camera():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("❌ Cannot access the camera.")
        return

    print("🎥 Real-time mode active. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Failed to grab frame.")
            break

        try:
            result = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=False)

            dominant_emotion = result[0]['dominant_emotion']
            region = result[0].get('region', None)
            print(f"🧠 Detected Emotion: {dominant_emotion}")

            if region:
                x, y, w, h = region['x'], region['y'], region['w'], region['h']
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, dominant_emotion, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)

        except Exception as e:
            print(f"⚠️ Emotion detection failed: {e}")

        cv2.imshow("Affectra Camera Feed", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            print("👋 Exiting...")
            break

    cap.release()
    cv2.destroyAllWindows()
