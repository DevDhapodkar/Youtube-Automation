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

    def generate_audio(self, text, output_file, target_duration=60):
        """
        Synchronous wrapper for the async generation using a thread.
        target_duration: Target duration in seconds (default 60 for Shorts)
        """
        logger.info(f"Generating audio to {output_file}...")
        try:
            # Run the async function in a new thread with its own event loop
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._generate_audio_async(text, output_file))
                future.result()  # Wait for completion
            
            # Check audio duration and extend if needed
            import subprocess
            import json
            import os
            
            # Get actual duration
            probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', output_file]
            result = subprocess.run(probe_cmd, capture_output=True, text=True)
            duration = float(json.loads(result.stdout)['format']['duration'])
            
            logger.info(f"Generated audio duration: {duration}s (target: {target_duration}s)")
            
            # If audio is shorter than target, loop it
            if duration < target_duration:
                logger.info(f"Extending audio from {duration}s to {target_duration}s")
                temp_output = output_file.replace('.mp3', '_extended.mp3')
                
                # Calculate how many loops needed
                loops = int(target_duration / duration) + 1
                
                # Create concat file
                concat_file = output_file.replace('.mp3', '_concat.txt')
                with open(concat_file, 'w') as f:
                    for _ in range(loops):
                        f.write(f"file '{os.path.basename(output_file)}'\n")
                
                # Concatenate and trim to exact duration
                concat_cmd = [
                    'ffmpeg', '-y', '-f', 'concat', '-safe', '0', '-i', concat_file,
                    '-t', str(target_duration), '-c', 'copy', temp_output
                ]
                subprocess.run(concat_cmd, capture_output=True)
                
                # Replace original with extended
                os.replace(temp_output, output_file)
                os.remove(concat_file)
                
                logger.info(f"Audio extended to {target_duration}s")
            
            logger.info("Audio generation complete.")
            return output_file
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            return None

if __name__ == "__main__":
    gen = AudioGenerator()
    gen.generate_audio("Hello, this is a test of the automated voice system.", "test_audio.mp3")
