from flask import Flask, request, jsonify
import os
import pandas as pd
from datetime import datetime

app = Flask(__name__)

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

if __name__ == "__main__":
    app.run(port=5000, debug=True)
