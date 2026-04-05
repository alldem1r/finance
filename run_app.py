#!/usr/bin/env python3
"""
Financial Tracker - Desktop App Launcher
Run this script to start the Financial Tracker application.
"""

import subprocess
import sys
import os

def main():
    """Launch the Streamlit app with desktop-like settings"""
    try:
        # Get the directory of this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(script_dir, "app.py")

        # Check if app.py exists
        if not os.path.exists(app_path):
            print("Error: app.py not found in the current directory.")
            print("Make sure you're running this from the Financial Tracker directory.")
            sys.exit(1)

        # Launch streamlit with specific settings for desktop app experience
        cmd = [
            sys.executable, "-m", "streamlit", "run", app_path,
            "--server.headless", "true",  # Run in headless mode
            "--server.port", "8501",      # Use port 8501
            "--browser.serverAddress", "localhost",  # Bind to localhost
            "--theme.base", "dark"        # Use dark theme
        ]

        print("🚀 Starting Financial Tracker...")
        print("📱 App will open in your default web browser")
        print("💡 Keep this terminal window open while using the app")
        print("🔄 Press Ctrl+C to stop the app")
        print()

        # Run the command
        subprocess.run(cmd, cwd=script_dir)

    except KeyboardInterrupt:
        print("\n👋 Financial Tracker stopped. Have a great day!")
    except Exception as e:
        print(f"Error starting the app: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()