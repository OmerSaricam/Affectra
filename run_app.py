#!/usr/bin/env python
"""
Affectra Emotion Tracking Web UI
Run this script to start the web interface for emotion tracking.
"""

import os
import sys
import traceback

def setup_directories():
    """Ensure all required directories exist."""
    # Get absolute path to the project root
    project_root = os.path.dirname(os.path.abspath(__file__))
    
    # Create required directories
    dirs_to_create = [
        os.path.join(project_root, "server", "logs"),
        os.path.join(project_root, "server", "storage"),
        os.path.join(project_root, "server", "static", "images")
    ]
    
    for directory in dirs_to_create:
        if not os.path.exists(directory):
            print(f"Creating directory: {directory}")
            os.makedirs(directory, exist_ok=True)

if __name__ == "__main__":
    try:
        # Setup directories first
        setup_directories()
        
        # Import Flask app after directories are set up
        from server.app import app
        
        print("🚀 Starting Affectra Web UI")
        print("📊 Access the interface at http://localhost:5000")
        print("💡 Press Ctrl+C to stop the server")
        
        # Start Flask app
        app.run(host='0.0.0.0', port=5000, debug=True)
        
    except Exception as e:
        print("❌ Error starting the application:")
        print(f"   {str(e)}")
        print("\nDetailed error information:")
        traceback.print_exc()
        print("\n💡 Tip: Make sure all dependencies are installed with: pip install -r requirements.txt")
        sys.exit(1) 