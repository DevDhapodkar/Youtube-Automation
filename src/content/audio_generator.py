import logging
import asyncio
import edge_tts
from config.settings import Config

logger = logging.getLogger(__name__)

class AudioGenerator:
    def __init__(self):
        # Voice options: en-US-ChristopherNeural, en-US-EricNeural, en-US-GuyNeural, en-US-JennyNeural, en-US-AriaNeural
        self.voice = "en-US-ChristopherNeural" 

    async def _generate_audio_async(self, text, output_file):
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_file)

    def generate_audio(self, text, output_file):
        """
        Synchronous wrapper for the async generation.
        """
        logger.info(f"Generating audio to {output_file}...")
        try:
            # Check if there's already a running event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in an async context, create a task
                import nest_asyncio
                nest_asyncio.apply()
                asyncio.run(self._generate_audio_async(text, output_file))
            except RuntimeError:
                # No event loop running, safe to use asyncio.run
                asyncio.run(self._generate_audio_async(text, output_file))
            
            logger.info("Audio generation complete.")
            return output_file
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            return None

if __name__ == "__main__":
    gen = AudioGenerator()
    gen.generate_audio("Hello, this is a test of the automated voice system.", "test_audio.mp3")
