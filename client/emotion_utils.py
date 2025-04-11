from collections import Counter
import time
from datetime import datetime

class EmotionSession:
    def __init__(self):
        self.emotions = []
        self.start_time = None
        self.end_time = None

    def start(self):
        self.start_time = time.time()
        print("📍 Session started.")

    def add_emotion(self, emotion):
        if self.start_time is None:
            self.start()
        self.emotions.append(emotion)

    def end(self):
        self.end_time = time.time()
        print("📍 Session ended.")


    def get_summary(self):
        if not self.emotions:
            return {}

        total_duration = round(self.end_time - self.start_time, 2)
        counter = Counter(self.emotions)
        dominant_emotion = counter.most_common(1)[0][0]
        emotion_percentages = {
            emotion: round((count / len(self.emotions)) * 100, 2)
            for emotion, count in counter.items()
        }

        return {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": total_duration,
            "dominant_emotion": dominant_emotion,
            "emotion_percentages": emotion_percentages
        }