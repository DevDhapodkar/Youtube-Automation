import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
    FREESOUND_API_KEY = os.getenv("FREESOUND_API_KEY", "")
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
    
    # Settings
    VIDEO_RESOLUTION = (1080, 1920) # 9:16 for Shorts, change to (1920, 1080) for long form
    FPS = 30
    
    # Scene-based video settings
    SCENE_DURATION_MIN = 5  # seconds
    SCENE_DURATION_MAX = 10  # seconds
    TRANSITION_DURATION = 0.3  # seconds
    
    # ElevenLabs voice settings
    ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel voice
    ELEVENLABS_MODEL = "eleven_monolingual_v1"
    
    # Scheduler
    UPLOAD_FREQUENCY_HOURS = int(os.getenv("UPLOAD_FREQUENCY_HOURS", 24))
    UPLOAD_SCHEDULE = [] # List of "HH:MM" strings, e.g. ["10:00", "18:00"]

    @staticmethod
    def validate():
        missing = []
        if not Config.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        # YouTube API key might be optional if using OAuth for upload, but needed for trends
        if missing:
            print(f"Warning: Missing environment variables: {', '.join(missing)}")

