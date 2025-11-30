import logging
import os
import requests
from config.settings import Config

logger = logging.getLogger(__name__)

class SoundEffectGenerator:
    """
    Manages ambient sound effects for videos.
    Uses Pixabay API for royalty-free sounds.
    """
    def __init__(self):
        self.api_key = os.getenv("PIXABAY_API_KEY", "")
        self.base_url = "https://pixabay.com/api/"
        self.sfx_dir = os.path.join(Config.ASSETS_DIR, "sfx")
        
        if not os.path.exists(self.sfx_dir):
            os.makedirs(self.sfx_dir)
    
    def get_ambient_sound(self, niche):
        """
        Get appropriate ambient sound for the niche.
        Returns path to downloaded audio file, or None if unavailable.
        """
        # Niche-specific search queries
        queries = {
            "horror": "horror ambient scary",
            "horror_stories": "suspense thriller dark",
            "history": "medieval ambient ancient",
            "scp": "laboratory alarm industrial",
            "life_advice": "calm meditation peaceful",
            "news": "news broadcast",
            "general": "ambient background"
        }
        
        query = queries.get(niche, queries["general"])
        
        # Check if we already have a cached sound for this niche
        cached_file = os.path.join(self.sfx_dir, f"{niche}_ambient.mp3")
        if os.path.exists(cached_file):
            logger.info(f"Using cached ambient sound for {niche}")
            return cached_file
        
        # If no API key, use silence (no SFX)
        if not self.api_key:
            logger.warning("PIXABAY_API_KEY not set. Skipping sound effects.")
            return None
        
        try:
            # Search for sound effects
            params = {
                "key": self.api_key,
                "q": query,
                "audio_type": "music",
                "per_page": 3
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("hits"):
                # Get first result
                sound = data["hits"][0]
                download_url = sound.get("previewURL")
                
                if download_url:
                    logger.info(f"Downloading ambient sound for {niche}...")
                    audio_response = requests.get(download_url, timeout=30)
                    audio_response.raise_for_status()
                    
                    with open(cached_file, 'wb') as f:
                        f.write(audio_response.content)
                    
                    logger.info(f"Ambient sound saved to {cached_file}")
                    return cached_file
            
            logger.warning(f"No ambient sounds found for {niche}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get ambient sound: {e}")
            return None
    
    def mix_audio(self, voice_path, ambient_path, output_path, ambient_volume=0.15):
        """
        Mix voice audio with ambient sound using FFmpeg.
        ambient_volume: Volume of ambient (0.0-1.0), default 0.15 for subtle background
        """
        if not ambient_path or not os.path.exists(ambient_path):
            logger.info("No ambient sound to mix, using voice only")
            return voice_path
        
        try:
            import subprocess
            
            logger.info(f"Mixing voice with ambient sound (volume: {ambient_volume})")
            
            # Mix command: loop ambient, lower volume, mix with voice
            mix_cmd = [
                'ffmpeg', '-y',
                '-i', voice_path,
                '-stream_loop', '-1',  # Loop ambient indefinitely
                '-i', ambient_path,
                '-filter_complex', f'[1:a]volume={ambient_volume}[ambient];[0:a][ambient]amix=inputs=2:duration=first:dropout_transition=2',
                '-c:a', 'libmp3lame',
                '-q:a', '2',
                output_path
            ]
            
            result = subprocess.run(mix_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info("Audio mixing complete")
                return output_path
            else:
                logger.error(f"Audio mixing failed: {result.stderr}")
                return voice_path
                
        except Exception as e:
            logger.error(f"Audio mixing error: {e}")
            return voice_path
