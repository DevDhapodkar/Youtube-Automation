import logging
import os
import requests
from config.settings import Config

logger = logging.getLogger(__name__)

class SoundEffectGenerator:
    """
    Manages ambient sound effects for videos using Freesound API.
    """
    def __init__(self):
        self.api_key = Config.FREESOUND_API_KEY
        self.base_url = "https://freesound.org/apiv2/search/text/"
        self.sfx_dir = os.path.join(Config.ASSETS_DIR, "sfx")
        
        if not os.path.exists(self.sfx_dir):
            os.makedirs(self.sfx_dir)
    
    def get_contextual_sfx(self, sfx_description):
        """
        Search and download a specific contextual sound effect.
        """
        if not sfx_description or not self.api_key:
            return None
            
        try:
            # Clean description for filename
            safe_desc = "".join([c for c in sfx_description if c.isalnum()]).lower()
            file_path = os.path.join(self.sfx_dir, f"context_{safe_desc}.mp3")
            
            if os.path.exists(file_path):
                return file_path
                
            logger.info(f"Searching Freesound for contextual SFX: {sfx_description}")
            
            params = {
                "query": sfx_description,
                "filter": "duration:[0.1 TO 15]", # Broaden duration, remove type:mp3
                "sort": "relevance",
                "page_size": 5,
                "fields": "id,name,previews",
                "token": self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Fallback if no results: try simplifying the query
            if not data.get("results") and " " in sfx_description:
                simplified_query = sfx_description.split()[-1] # Try last word
                logger.info(f"No SFX results for '{sfx_description}', trying fallback: '{simplified_query}'")
                params["query"] = simplified_query
                response = requests.get(self.base_url, params=params, timeout=10)
                data = response.json()

            if data.get("results"):
                sound = data["results"][0] # Take the best match
                previews = sound.get("previews", {})
                preview_url = previews.get("preview-hq-mp3") or previews.get("preview-lq-mp3")
                
                if preview_url:
                    logger.info(f"Downloading SFX: {sfx_description} from {preview_url}")
                    audio_response = requests.get(preview_url, timeout=30)
                    audio_response.raise_for_status()
                    
                    with open(file_path, 'wb') as f:
                        f.write(audio_response.content)
                        
                    return file_path
                    
            return None
        except Exception as e:
            logger.error(f"Failed to get contextual SFX '{sfx_description}': {e}")
            return None

    def get_ambient_sound(self, niche):
        """
        Get appropriate ambient sound for the niche from Freesound.
        Returns path to downloaded audio file, or None if unavailable.
        """
        # Niche-specific search queries
        queries = {
            "horror": "horror ambient dark drone",
            "horror_stories": "suspense thriller creepy atmosphere",
            "history": "medieval ambient ancient music",
            "scp": "laboratory alarm industrial ambience",
            "life_advice": "calm meditation peaceful ambient",
            "news": "news broadcast background",
            "general": "cinematic ambient background"
        }
        
        query = queries.get(niche, queries["general"])
        
        # Check if we have cached sounds for this niche
        import glob
        import random
        
        # Create niche directory
        niche_dir = os.path.join(self.sfx_dir, niche)
        if not os.path.exists(niche_dir):
            os.makedirs(niche_dir)
            
        # Get existing files
        existing_files = glob.glob(os.path.join(niche_dir, "*.mp3"))
        
        # 30% chance to reuse an existing file if we have enough variety (at least 3)
        if len(existing_files) >= 3 and random.random() < 0.3:
            selected = random.choice(existing_files)
            logger.info(f"Reusing cached ambient sound: {os.path.basename(selected)}")
            return selected
        
        # If no API key, try to return an existing file or fail
        if not self.api_key:
            if existing_files:
                return random.choice(existing_files)
            logger.warning("FREESOUND_API_KEY not set. Skipping sound effects.")
            return None
        
        try:
            # Search for sound effects
            params = {
                "query": query,
                "filter": "duration:[20 TO 300]",  # 20-300 second files
                "sort": "rating_desc",  # Highest rated first
                "page_size": 20, 
                "fields": "id,name,previews,username",
                "token": self.api_key
            }
            
            logger.info(f"Searching Freesound for: {query}")
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get("results"):
                # Pick a random sound from top results
                results = data["results"]
                sound = random.choice(results)
                
                # Check if already downloaded
                sound_id = sound.get("id")
                safe_name = "".join([c for c in sound.get("name", "sound") if c.isalpha() or c.isdigit()]).rstrip()
                filename = f"{sound_id}_{safe_name}.mp3"
                file_path = os.path.join(niche_dir, filename)
                
                if os.path.exists(file_path):
                    logger.info(f"Sound already exists: {filename}")
                    return file_path
                
                preview_url = sound.get("previews", {}).get("preview-hq-mp3")
                if not preview_url:
                    preview_url = sound.get("previews", {}).get("preview-lq-mp3")
                
                if preview_url:
                    logger.info(f"Downloading ambient sound: {sound.get('name')} by {sound.get('username')}")
                    audio_response = requests.get(preview_url, timeout=30)
                    audio_response.raise_for_status()
                    
                    with open(file_path, 'wb') as f:
                        f.write(audio_response.content)
                    
                    logger.info(f"Ambient sound saved to {file_path}")
                    return file_path
            
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
                '-filter_complex', f'[1:a]volume={ambient_volume}[ambient];[0:a][ambient]amix=inputs=2:duration=first:dropout_transition=2[aout]',
                '-map', '[aout]',
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
