import logging
import asyncio
import edge_tts
import requests
import json
import os
from config.settings import Config
import concurrent.futures

logger = logging.getLogger(__name__)


class ElevenLabsGenerator:
    """
    Generate natural-sounding audio using ElevenLabs API.
    Free tier: 10,000 characters/month (~10 videos)
    """
    
    def __init__(self):
        self.api_key = Config.ELEVENLABS_API_KEY
        self.voice_id = Config.ELEVENLABS_VOICE_ID
        self.model = Config.ELEVENLABS_MODEL
        self.base_url = "https://api.elevenlabs.io/v1"
    
    def generate_audio(self, text: str, output_file: str) -> bool:
        """
        Generate audio using ElevenLabs API.
        
        Args:
            text: Text to convert to speech
            output_file: Path to save MP3 file
            
        Returns:
            True if successful, False otherwise
        """
        if not self.api_key:
            logger.warning("ElevenLabs API key not configured")
            return False
        
        try:
            url = f"{self.base_url}/text-to-speech/{self.voice_id}"
            
            headers = {
                "xi-api-key": self.api_key,
                "Content-Type": "application/json"
            }
            
            data = {
                "text": text,
                "model_id": self.model,
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                    "style": 0.0,
                    "use_speaker_boost": True
                }
            }
            
            logger.info(f"Generating audio with ElevenLabs (voice: {self.voice_id})")
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Save audio
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                
                logger.info(f"ElevenLabs audio saved to {output_file}")
                return True
            else:
                logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"ElevenLabs generation failed: {e}")
            return False
    
    def get_available_voices(self) -> list:
        """Get list of available voices from ElevenLabs."""
        if not self.api_key:
            return []
        
        try:
            url = f"{self.base_url}/voices"
            headers = {"xi-api-key": self.api_key}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                voices = response.json().get("voices", [])
                return [(v["voice_id"], v["name"]) for v in voices]
            else:
                logger.error(f"Failed to fetch voices: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching voices: {e}")
            return []


class AudioGenerator:
    """
    Enhanced audio generator with multiple TTS backends.
    Priority: ElevenLabs > edge-tts > gTTS
    """
    
    def __init__(self):
        # Initialize all generators
        self.elevenlabs = ElevenLabsGenerator()
        
        # edge-tts settings
        self.edge_voice = "en-US-JennyNeural"
        
        # gTTS is imported on-demand
    
    def generate_audio(self, text: str, output_file: str, target_duration: int = 60, niche: str = "general") -> str:
        """
        Generate audio using best available TTS engine.
        
        Args:
            text: Text to convert to speech
            output_file: Path to save audio file
            target_duration: Target duration in seconds (for padding if needed)
            niche: Content niche (e.g., 'horror', 'news', 'tech')
            
        Returns:
            Path to generated audio file, or None if failed
        """
        logger.info(f"Generating audio for text ({len(text)} chars) - Niche: {niche}")
        
        # Select voice based on niche/content
        voice_config = self._select_voice(text, niche)
        logger.info(f"Selected voice config: {voice_config}")
        
        # Try ElevenLabs first (best quality)
        if Config.ELEVENLABS_API_KEY:
            logger.info("Attempting ElevenLabs TTS...")
            if self.elevenlabs.generate_audio(text, output_file):
                logger.info("✓ ElevenLabs audio generated successfully")
                self._generate_timestamps_for_elevenlabs(text, output_file)
                return output_file
            else:
                logger.warning("ElevenLabs failed, falling back to edge-tts")
        
        # Try edge-tts (good quality, free)
        logger.info("Attempting edge-tts...")
        try:
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(
                    asyncio.run,
                    self._generate_with_edge_tts(text, output_file, voice_config)
                )
                future.result(timeout=30)
            
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                logger.info("✓ edge-tts audio generated successfully")
                return output_file
            else:
                raise Exception("edge-tts produced empty file")
                
        except Exception as e:
            logger.warning(f"edge-tts failed: {e}, falling back to gTTS")
        
        # Fallback to gTTS (reliable)
        logger.info("Using gTTS fallback...")
        try:
            self._generate_with_gtts(text, output_file)
            logger.info("✓ gTTS audio generated successfully")
            return output_file
        except Exception as e:
            logger.error(f"All TTS engines failed: {e}")
            return None
    
    def _select_voice(self, text: str, niche: str) -> dict:
        """
        Select appropriate voice based on niche and text content.
        """
        niche = niche.lower()
        text_lower = text.lower()
        
        # Default config
        config = {
            "voice": "en-US-JennyNeural",
            "rate": "+0%",
            "pitch": "+0Hz"
        }
        
        # Analyze content for gender hints
        is_male_narrator = any(word in text_lower for word in [" i'm a guy", " i am a man", " my wife", " my girlfriend"])
        
        if "horror" in niche or "scary" in niche or "creepypasta" in niche:
            # Creepy/Horror style
            config["voice"] = "en-US-ChristopherNeural" # Deep male voice
            config["rate"] = "-10%" # Slower
            config["pitch"] = "-5Hz" # Lower pitch
        
        elif "news" in niche:
            # Professional News style
            config["voice"] = "en-US-AriaNeural" # Professional female
            config["rate"] = "+5%" # Slightly faster
        
        elif "tech" in niche or "coding" in niche:
            # Tech/Educational style
            config["voice"] = "en-US-ChristopherNeural" # Professional male
        
        elif "motivation" in niche:
            # Motivational style
            config["voice"] = "en-US-EricNeural" # Friendly/Energetic male
            config["rate"] = "+0%"
        
        elif is_male_narrator:
            config["voice"] = "en-US-GuyNeural" # Casual male
            
        return config

    async def _generate_with_edge_tts(self, text: str, output_file: str, voice_config: dict = None):
        """
        Generate audio with edge-tts.
        Tries multiple voices if the primary one fails.
        """
        if voice_config is None:
            voice_config = {"voice": "en-US-JennyNeural", "rate": "+0%", "pitch": "+0Hz"}
            
        primary_voice = voice_config["voice"]
        rate = voice_config.get("rate", "+0%")
        pitch = voice_config.get("pitch", "+0Hz")
        
        # List of voices to try (primary first)
        voices = [primary_voice, "en-US-JennyNeural", "en-US-ChristopherNeural"]
        
        # Remove duplicates while preserving order
        voices = list(dict.fromkeys(voices))
        
        last_error = None
        
        for voice in voices:
            try:
                logger.info(f"Trying edge-tts voice: {voice} (Rate: {rate}, Pitch: {pitch})")
                communicate = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
                submaker = edge_tts.SubMaker()
                
                # Create a temporary file for this attempt
                temp_file = output_file + ".tmp"
                
                with open(temp_file, "wb") as f:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            f.write(chunk["data"])
                        elif chunk["type"] in ["WordBoundary", "SentenceBoundary"]:
                            submaker.feed(chunk)
                
                # If we got here, it worked!
                # Move temp file to actual output
                if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                    os.replace(temp_file, output_file)
                    
                    # Save SRT and timestamps
                    try:
                        srt_content = submaker.get_srt()
                        srt_file = output_file.replace('.mp3', '.srt')
                        with open(srt_file, 'w', encoding='utf-8') as f:
                            f.write(srt_content)
                        
                        # Parse SRT to JSON timestamps
                        self._srt_to_timestamps(srt_file, output_file.replace('.mp3', '_timestamps.json'))
                    except Exception as e:
                        logger.warning(f"Failed to generate subtitles for {voice}: {e}, but audio is saved.")
                        # Generate estimated timestamps as fallback
                        self._generate_timestamps_for_elevenlabs(text, output_file)
                    
                    logger.info(f"✓ edge-tts successful with {voice}")
                    return
                else:
                    raise Exception("Generated file was empty")
                    
            except Exception as e:
                logger.warning(f"Voice {voice} failed: {e}")
                last_error = e
                if os.path.exists(output_file + ".tmp"):
                    os.remove(output_file + ".tmp")
                continue
        
        # If all voices failed
        raise Exception(f"All edge-tts voices failed. Last error: {last_error}")
    
    def _generate_with_gtts(self, text: str, output_file: str):
        """Generate audio with gTTS."""
        from gtts import gTTS
        import subprocess
        
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_file)
        
        # Generate approximate timestamps
        words = text.split()
        
        # Get audio duration
        probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', output_file]
        result = subprocess.run(probe_cmd, capture_output=True, text=True)
        duration = float(json.loads(result.stdout)['format']['duration'])
        
        time_per_word = duration / len(words) if words else 0
        
        timestamps = []
        current_time = 0
        for word in words:
            timestamps.append({
                "word": word,
                "start": current_time,
                "end": current_time + time_per_word
            })
            current_time += time_per_word
        
        timestamps_file = output_file.replace('.mp3', '_timestamps.json')
        with open(timestamps_file, 'w') as f:
            json.dump(timestamps, f, indent=2)
    
    def _generate_timestamps_for_elevenlabs(self, text: str, audio_file: str):
        """
        Generate approximate timestamps for ElevenLabs audio.
        ElevenLabs doesn't provide word-level timestamps, so we estimate.
        """
        import subprocess
        
        words = text.split()
        
        # Get audio duration
        try:
            probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', audio_file]
            result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
            duration = float(json.loads(result.stdout)['format']['duration'])
        except:
            # Estimate: ~2.5 words per second
            duration = len(words) / 2.5
        
        time_per_word = duration / len(words) if words else 0
        
        timestamps = []
        current_time = 0
        for word in words:
            timestamps.append({
                "word": word,
                "start": current_time,
                "end": current_time + time_per_word
            })
            current_time += time_per_word
        
        timestamps_file = audio_file.replace('.mp3', '_timestamps.json')
        with open(timestamps_file, 'w') as f:
            json.dump(timestamps, f, indent=2)
    
    def _srt_to_timestamps(self, srt_file: str, json_file: str):
        """Convert SRT file to JSON timestamps."""
        import re
        
        with open(srt_file, 'r', encoding='utf-8') as f:
            srt_content = f.read()
        
        pattern = re.compile(r'(\d{2}:\d{2}:\d{2}[.,]\d{3}) --> (\d{2}:\d{2}:\d{2}[.,]\d{3})\n(.*?)(?=\n\n|\Z)', re.DOTALL)
        
        timestamps = []
        for match in pattern.finditer(srt_content):
            start_str, end_str, text = match.groups()
            
            def parse_time(t_str):
                t_str = t_str.replace(',', '.')
                h, m, s = t_str.split(':')
                return int(h) * 3600 + int(m) * 60 + float(s)
            
            timestamps.append({
                "word": text.strip(),
                "start": parse_time(start_str),
                "end": parse_time(end_str)
            })
        
        with open(json_file, 'w') as f:
            json.dump(timestamps, f, indent=2)


if __name__ == "__main__":
    # Test audio generation
    gen = AudioGenerator()
    test_text = "Welcome to this amazing video about artificial intelligence. AI is transforming our world."
    gen.generate_audio(test_text, "test_elevenlabs.mp3")
