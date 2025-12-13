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
        # JennyNeural is friendly and conversational, AndrewNeural is natural male voice
        self.voice = "en-US-JennyNeural"  # More natural and friendly
        
        # SSML prosody settings for more natural speech
        self.rate = "0.95"  # Slightly slower for clarity (1.0 is normal)
        self.pitch = "+2%"  # Slight pitch variation for naturalness
        self.volume = "+10%"  # Slightly louder for better clarity
    
    def _wrap_with_ssml(self, text):
        """
        Wrap text with SSML tags for more natural speech.
        Adds prosody controls for better voice quality.
        Note: Keep SSML simple for edge-tts compatibility.
        """
        # Simple SSML with just prosody - edge-tts doesn't support all SSML features
        ssml = f'''<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">
    <prosody rate="{self.rate}" pitch="{self.pitch}" volume="{self.volume}">
        {text}
    </prosody>
</speak>'''
        return ssml 

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

    async def _generate_audio_with_timestamps_async(self, text, output_file, voice=None):
        """
        Generate audio with timestamps using edge-tts.
        Tries multiple voices if the primary one fails.
        Uses SSML for more natural speech.
        """
        if voice is None:
            voice = self.voice
        
        # Note: SSML with prosody is causing edge-tts to fail
        # Using plain text for now - edge-tts voices are already high quality
        # TODO: Investigate SSML compatibility with edge-tts
        text_to_use = text  # Use plain text instead of SSML
            
        # List of fallback voices to try
        voices_to_try = [
            voice,
            "en-US-JennyNeural",
            "en-US-AndrewNeural",
            "en-US-GuyNeural",
            "en-US-AriaNeural",
            "en-GB-SoniaNeural",
            "en-AU-NatashaNeural"
        ]
        
        # Remove duplicates while preserving order
        seen = set()
        voices_to_try = [v for v in voices_to_try if not (v in seen or seen.add(v))]
        
        last_error = None
        
        for attempt_voice in voices_to_try:
            try:
                logger.info(f"Attempting audio generation with voice: {attempt_voice}")
                communicate = edge_tts.Communicate(text_to_use, attempt_voice)
                submaker = edge_tts.SubMaker()
                
                audio_chunks_count = 0
                
                with open(output_file, "wb") as file:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            file.write(chunk["data"])
                            audio_chunks_count += 1
                        elif chunk["type"] == "WordBoundary" or chunk["type"] == "SentenceBoundary":
                            # Feed boundary events to submaker
                            submaker.feed(chunk)
                            logger.debug(f"Fed {chunk['type']} to submaker")
                        else:
                            logger.debug(f"Ignored chunk type: {chunk['type']}")
                
                logger.info(f"Successfully generated audio with {audio_chunks_count} chunks using {attempt_voice}")
                
                # Verify file was created and has content
                import os
                if not os.path.exists(output_file) or os.path.getsize(output_file) == 0:
                    raise Exception(f"Audio file is empty or not created")
                
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
                
                # Success! Return
                return
                
            except Exception as e:
                last_error = e
                logger.warning(f"Voice {attempt_voice} failed: {e}")
                # Try next voice
                continue
        
        # If we get here, all voices failed
        raise Exception(f"All voices failed. Last error: {last_error}")

    def _generate_audio_with_gtts(self, text, output_file):
        """
        Fallback: Generate audio using gTTS (Google Text-to-Speech).
        More reliable than edge-tts but doesn't provide word-level timestamps.
        """
        try:
            from gtts import gTTS
            import os
            
            logger.info("Using gTTS fallback for audio generation...")
            
            # Generate audio
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(output_file)
            
            logger.info(f"gTTS audio saved to {output_file}")
            
            # Generate approximate timestamps based on word count
            # Average speaking rate: ~150 words per minute = 2.5 words per second
            words = text.split()
            total_words = len(words)
            
            # Get actual audio duration
            import subprocess
            probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', output_file]
            result = subprocess.run(probe_cmd, capture_output=True, text=True)
            duration = float(json.loads(result.stdout)['format']['duration'])
            
            # Calculate time per word
            time_per_word = duration / total_words if total_words > 0 else 0
            
            # Generate approximate timestamps
            timestamps = []
            current_time = 0
            
            for word in words:
                word_duration = time_per_word
                timestamps.append({
                    "word": word,
                    "start": current_time,
                    "end": current_time + word_duration
                })
                current_time += word_duration
            
            # Save timestamps
            timestamps_file = output_file.replace('.mp3', '_timestamps.json')
            with open(timestamps_file, 'w') as f:
                json.dump(timestamps, f, indent=2)
                
            logger.info(f"Generated {len(timestamps)} approximate timestamps")
            
            # Generate basic SRT
            srt_content = ""
            for i, ts in enumerate(timestamps, 1):
                start_time = self._seconds_to_srt_time(ts['start'])
                end_time = self._seconds_to_srt_time(ts['end'])
                srt_content += f"{i}\n{start_time} --> {end_time}\n{ts['word']}\n\n"
            
            srt_file = output_file.replace('.mp3', '.srt')
            with open(srt_file, 'w', encoding='utf-8') as f:
                f.write(srt_content)
                
            logger.info(f"Generated SRT file: {srt_file}")
            
        except Exception as e:
            logger.error(f"gTTS fallback failed: {e}")
            raise
    
    def _seconds_to_srt_time(self, seconds):
        """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def generate_audio(self, text, output_file, target_duration=60):
        """
        Synchronous wrapper for the async generation using a thread.
        target_duration: Target duration in seconds (default 60 for Shorts)
        """
        logger.info(f"Generating audio to {output_file}...")
        try:
            # Try edge-tts first
            try:
                # Run the async function in a new thread with its own event loop
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self._generate_audio_with_timestamps_async(text, output_file))
                    future.result(timeout=30)  # 30 second timeout
                
                logger.info("Successfully generated audio with edge-tts")
                
            except Exception as edge_error:
                logger.warning(f"edge-tts failed: {edge_error}")
                logger.info("Falling back to gTTS...")
                
                # Fallback to gTTS
                self._generate_audio_with_gtts(text, output_file)
            
            # Check audio duration and extend if needed
            import subprocess
            import json
            import os
            
            # Get actual duration
            probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'json', output_file]
            result = subprocess.run(probe_cmd, capture_output=True, text=True)
            
            try:
                duration = float(json.loads(result.stdout)['format']['duration'])
            except:
                logger.warning("Could not determine audio duration, skipping adjustment")
                return output_file
            
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
