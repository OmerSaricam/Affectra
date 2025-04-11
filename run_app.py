#!/usr/bin/env python
"""
Affectra Emotion Tracking Web UI
Run this script to start the web interface for emotion tracking.
"""

import os
import sys
from server.app import app

if __name__ == "__main__":
    print("🚀 Starting Affectra Web UI")
    print("📊 Access the interface at http://localhost:5000")
    print("💡 Press Ctrl+C to stop the server")
    
    # Ensure storage directory exists
    os.makedirs("server/storage", exist_ok=True)
    
    # Start Flask app
    app.run(host='0.0.0.0', port=5000, debug=True) 