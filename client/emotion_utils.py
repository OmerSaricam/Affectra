from collections import Counter
import time
from datetime import datetime

class EmotionSession:
    """
    Tracks and analyzes emotion data for a single session.
    A session represents a continuous period where a face is visible.
    Collects emotion observations and provides summary statistics.
    """
    
    def __init__(self):
        """Initialize a new emotion tracking session."""
        self.emotions = []  # List to store all detected emotions
        self.start_time = None  # Session start timestamp
        self.end_time = None  # Session end timestamp

    def start(self):
        """
        Start the emotion tracking session.
        Records the current time as the start time.
        """
        self.start_time = time.time()
        print("📍 Session started.")

    def add_emotion(self, emotion):
        """
        Add a detected emotion to the session.
        
        Args:
            emotion (str): The detected emotion (e.g., "happy", "sad", etc.)
        
        Notes:
            Automatically starts the session if not already started
        """
        if self.start_time is None:
            self.start()
        self.emotions.append(emotion)

    def end(self):
        """
        End the emotion tracking session.
        Records the current time as the end time.
        """
        self.end_time = time.time()
        print("📍 Session ended.")

    def get_summary(self):
        """
        Generate a summary of the emotion session.
        
        Returns:
            dict: A dictionary containing:
                - timestamp: ISO formatted time when the session ended
                - duration_seconds: Length of session in seconds
                - dominant_emotion: Most frequently detected emotion
                - emotion_percentages: Distribution of emotions as percentages
                
            Returns empty dict if no emotions were detected.
        """
        if not self.emotions:
            return {}

        # Calculate total session duration
        total_duration = round(self.end_time - self.start_time, 2)
        
        # Count occurrences of each emotion
        counter = Counter(self.emotions)
        
        # Determine the most common emotion
        dominant_emotion = counter.most_common(1)[0][0]
        
        # Calculate percentage for each detected emotion
        emotion_percentages = {
            emotion: round((count / len(self.emotions)) * 100, 2)
            for emotion, count in counter.items()
        }

        # Return structured summary data
        return {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": total_duration,
            "dominant_emotion": dominant_emotion,
            "emotion_percentages": emotion_percentages
        }