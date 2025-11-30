import logging
import asyncio
import edge_tts
from config.settings import Config
import concurrent.futures
import json

logger = logging.getLogger(__name__)

class AudioGenerator:
    def __init__(self):
        # Voice options: en-US-ChristopherNeural, en-US-EricNeural, en-US-GuyNeural, en-US-JennyNeural, en-US-AriaNeural
        self.voice = "en-US-AriaNeural" 

    async def _generate_audio_async(self, text, output_file):
        communicate = edge_tts.Communicate(text, self.voice)
        
        # Prepare to capture subtitles
        submaker = edge_tts.SubMaker()
        
        with open(output_file, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary":
                    submaker.feed(chunk)

        # Save timestamps to JSON
        import json
        timestamps_file = output_file.replace('.mp3', '_timestamps.json')
        
        # Convert SubMaker events to our format
        # SubMaker stores events as (offset, duration, text)
        # We want a list of dicts with start, end, word
        word_timestamps = []
        
        # Access the internal events list from SubMaker (it's a list of tuples)
        # Each tuple is (time, duration, text)
        # time is in seconds (float)
        
        # Note: edge_tts.SubMaker might not expose events directly in all versions,
        # but we can capture them manually from the chunk loop if needed.
        # Actually, let's just capture them manually in the loop to be safe.
        pass

    async def _generate_audio_with_timestamps_async(self, text, output_file):
        communicate = edge_tts.Communicate(text, self.voice)
        submaker = edge_tts.SubMaker()
        
        with open(output_file, "wb") as file:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    file.write(chunk["data"])
                elif chunk["type"] == "WordBoundary" or chunk["type"] == "SentenceBoundary":
                    # Feed boundary events to submaker
                    submaker.feed(chunk)
                    logger.debug(f"Fed {chunk['type']} to submaker")
                else:
                    logger.debug(f"Ignored chunk type: {chunk['type']}")

        # Generate and save SRT
        srt_content = submaker.get_srt()
        srt_file = output_file.replace('.mp3', '.srt')
        with open(srt_file, 'w', encoding='utf-8') as f:
            f.write(srt_content)
            
        logger.info(f"Saved subtitles to {srt_file}")
        
        # Also save as JSON for video editor to consume easily (parsing SRT here)
        import re
        timestamps = []
        # Regex to parse SRT
        # Look for: timestamp --> timestamp \n text
        pattern = re.compile(r'(\d{2}:\d{2}:\d{2}[.,]\d{3}) --> (\d{2}:\d{2}:\d{2}[.,]\d{3})\n(.*)')
        
        # Split by double newline to get blocks
        lines = srt_content.split('\n\n')
        for block in lines:
            match = pattern.search(block)
            if match:
                start_str, end_str, text = match.groups()
                
                # Convert time string to seconds
                def parse_time(t_str):
                    t_str = t_str.replace(',', '.')
                    h, m, s = t_str.split(':')
                    return int(h) * 3600 + int(m) * 60 + float(s)
                
                start = parse_time(start_str)
                end = parse_time(end_str)
                
                timestamps.append({
                    "word": text.strip(), # It's actually a sentence/segment
                    "start": start,
                    "end": end
                })
        
        timestamps_file = output_file.replace('.mp3', '_timestamps.json')
        with open(timestamps_file, 'w') as f:
            json.dump(timestamps, f, indent=2)
            
        logger.info(f"Saved {len(timestamps)} segments to {timestamps_file}")

    def generate_audio(self, text, output_file, target_duration=60):
        """
        Synchronous wrapper for the async generation using a thread.
        target_duration: Target duration in seconds (default 60 for Shorts)
        """
        logger.info(f"Generating audio to {output_file}...")
        try:
            # Run the async function in a new thread with its own event loop
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self._generate_audio_with_timestamps_async(text, output_file))
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
            
            # Always ensure audio is exactly target duration
            if abs(duration - target_duration) > 0.5:  # If difference > 0.5s
                logger.info(f"Adjusting audio from {duration}s to {target_duration}s")
                temp_output = output_file.replace('.mp3', '_adjusted.mp3')
                
                if duration < target_duration:
                    # Audio too short - loop it
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
                    os.remove(concat_file)
                else:
                    # Audio too long - trim it
                    trim_cmd = [
                        'ffmpeg', '-y', '-i', output_file,
                        '-t', str(target_duration), '-c', 'copy', temp_output
                    ]
                    subprocess.run(trim_cmd, capture_output=True)
                
                # Replace original with adjusted
                if os.path.exists(temp_output):
                    os.replace(temp_output, output_file)
                    logger.info(f"Audio adjusted to {target_duration}s")
                    
                    # NOTE: If we adjust audio, timestamps might become invalid for the looped parts.
                    # For now, we assume the initial timestamps are valid for the first loop.
                    # Ideally, we should replicate timestamps if we loop.
            
            
            logger.info("Audio generation complete.")
            return output_file
        except Exception as e:
            logger.error(f"Audio generation failed: {e}")
            return None

if __name__ == "__main__":
    gen = AudioGenerator()
    gen.generate_audio("Hello, this is a test of the automated voice system.", "test_audio.mp3")
