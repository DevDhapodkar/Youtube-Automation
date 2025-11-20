import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    ASSETS_DIR = os.path.join(BASE_DIR, '..', 'assets')
    
    # Settings
    VIDEO_RESOLUTION = (1080, 1920) # 9:16 for Shorts, change to (1920, 1080) for long form
    FPS = 30
    
    # Scheduler
    UPLOAD_FREQUENCY_HOURS = int(os.getenv("UPLOAD_FREQUENCY_HOURS", 24))

    @staticmethod
    def validate():
        missing = []
        if not Config.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        # YouTube API key might be optional if using OAuth for upload, but needed for trends
        if missing:
            print(f"Warning: Missing environment variables: {', '.join(missing)}")

