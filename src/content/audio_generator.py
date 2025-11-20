import logging
import asyncio
import edge_tts
from config.settings import Config
import concurrent.futures

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
        Synchronous wrapper for the async generation using a thread.
        """
        logger.info(f"Generating audio to {output_file}...")
        try:
            # Run the async function in a new thread with its own event loop
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._generate_audio_async(text, output_file))
                future.result()  # Wait for completion
            
            logger.info("Audio generation complete.")
            return output_file
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            return None

if __name__ == "__main__":
    gen = AudioGenerator()
    gen.generate_audio("Hello, this is a test of the automated voice system.", "test_audio.mp3")
