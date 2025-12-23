import os
import sys
import webbrowser
import uvicorn
import multiprocessing
import time
from api.main import app

def open_browser():
    """Wait for server to start and open browser."""
    time.sleep(2)
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    # On Windows, PyInstaller needs this for multiprocessing
    multiprocessing.freeze_support()
    
    print("🚀 Starting YouTube Automation Agent...")
    print("Backend: http://localhost:8000")
    
    # Optional: Auto-open browser
    p = multiprocessing.Process(target=open_browser)
    p.start()
    
    try:
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
    except KeyboardInterrupt:
        print("\n👋 Stopping agent...")
    finally:
        p.terminate()
