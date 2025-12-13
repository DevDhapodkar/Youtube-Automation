import logging
import os
import subprocess
import json
from config.settings import Config

logger = logging.getLogger(__name__)

class VideoEditor:
    def __init__(self):
        self.resolution = Config.VIDEO_RESOLUTION # (1080, 1920)
        self.fps = Config.FPS

    def _get_color_filter(self, niche):
        """Get FFmpeg color grading filter for niche"""
        filters = {
            "horror": "eq=contrast=1.3:saturation=0.6,vignette=angle=PI/4",
            "horror_stories": "eq=contrast=1.4:saturation=0.5:brightness=-0.1,vignette=angle=PI/3",
            "history": "colorchannelmixer=.393:.769:.189:0:.349:.686:.168:0:.272:.534:.131,noise=alls=10:allf=t",
            "scp": "eq=contrast=1.5:saturation=0.7,colorbalance=rs=-0.2:gs=0:bs=0.3",
            "life_advice": "eq=contrast=1.1:saturation=1.2:brightness=0.05",
            "news": "eq=contrast=1.2:saturation=1.1",
            "general": "eq=contrast=1.1:saturation=1.0"
        }
        return filters.get(niche, filters["general"])

    def create_short(self, audio_path, visual_paths, script_text, output_path="final_video.mp4", niche="general"):
        """
        Assembles the video using FFmpeg (memory efficient).
        """
        logger.info("Starting video assembly with FFmpeg...")
        
        try:
            # 1. Get audio duration using FFprobe
            duration = self._get_audio_duration(audio_path)
            logger.info(f"Audio duration: {duration}s")
            
            if not visual_paths or len(visual_paths) == 0:
                logger.error("No visual files provided")
                return None

            # 2. Create a concat file for videos
            concat_file = os.path.join(Config.ASSETS_DIR, "concat_list.txt")
            
            # Process visual files - apply Ken Burns to images, keep videos as-is
            processed_visuals = []
            for idx, visual_path in enumerate(visual_paths):
                # Check if it's an image or video
                ext = os.path.splitext(visual_path)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png']:
                    # Apply Ken Burns effect to image
                    logger.info(f"Applying Ken Burns effect to image {idx}")
                    ken_burns_video = os.path.join(Config.ASSETS_DIR, f"kb_{idx}.mp4")
                    
                    # Create 5-second video from image with zoom/pan
                    kb_cmd = [
                        'ffmpeg', '-y',
                        '-loop', '1',
                        '-i', visual_path,
                        '-vf', f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0015,1.5)':d=125:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920",
                        '-t', '5',
                        '-c:v', 'libx264',
                        '-pix_fmt', 'yuv420p',
                        ken_burns_video
                    ]
                    subprocess.run(kb_cmd, capture_output=True, timeout=30)
                    
                    if os.path.exists(ken_burns_video):
                        processed_visuals.append(ken_burns_video)
                else:
                    # It's already a video
                    processed_visuals.append(visual_path)
            
            # Calculate how many times to loop each video to fill duration
            if not processed_visuals:
                logger.error("No processed visuals available")
                return None
            
            # Create concat list - repeat videos to fill 60 seconds
            # We need to ensure total video length >= audio duration
            concat_file = os.path.join(Config.ASSETS_DIR, "concat_list.txt")
            
            # Get duration of each processed visual
            visual_durations = []
            for visual in processed_visuals:
                try:
                    probe_cmd = ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', visual]
                    result = subprocess.run(probe_cmd, capture_output=True, text=True, timeout=10)
                    dur = float(result.stdout.strip())
                    visual_durations.append(dur)
                except:
                    visual_durations.append(5.0)  # Default 5 seconds if probe fails
            
            total_visual_duration = sum(visual_durations)
            
            # Calculate how many full loops we need
            if total_visual_duration > 0:
                loops_needed = int(duration / total_visual_duration) + 2  # +2 for safety margin
            else:
                loops_needed = 5
            
            logger.info(f"Total visual duration: {total_visual_duration}s, loops needed: {loops_needed}")
            
            with open(concat_file, 'w') as f:
                for _ in range(loops_needed):
                    for video_path in processed_visuals:
                        f.write(f"file '{video_path}'\n")
            
            # 3. Generate Subtitles (SRT) with proper timing based on audio duration
            srt_path = os.path.join(Config.ASSETS_DIR, "subtitles.srt")
            self._generate_srt(script_text, duration, srt_path, audio_path)
            
            # 4. Concatenate and process videos with FFmpeg
            temp_video = os.path.join(Config.ASSETS_DIR, "temp_concatenated.mp4")
            
            # Get color grading filter for niche
            color_filter = self._get_color_filter(niche)

            # Build filter chain: scale → color grade → crop
            # Use setpts to ensure smooth playback without black frames
            filter_chain = f"[0:v]setpts=PTS-STARTPTS,scale={self.resolution[0]}:{self.resolution[1]}:force_original_aspect_ratio=increase[vscaled];[vscaled]{color_filter}[vgraded];[vgraded]crop={self.resolution[0]}:{self.resolution[1]}[vcropped]"
            
            # First pass: concatenate and apply filters WITHOUT subtitles
            # CRITICAL: Remove -shortest flag and use -t to force exact duration
            concat_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-i', audio_path,
                '-filter_complex', filter_chain,
                '-map', '[vcropped]',
                '-map', '1:a:0',
                '-t', str(duration),  # Force exact duration
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '192k',
                temp_video
            ]
            
            logger.info("Running FFmpeg concatenation...")
            result = subprocess.run(concat_cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg concat failed: {result.stderr}")
                return None
            
            # Second pass: Add subtitles
            logger.info("Adding subtitles...")
            final_output = output_path
            
            subtitle_cmd = [
                'ffmpeg', '-y',
                '-i', temp_video,
                '-vf', f"subtitles={srt_path}:force_style='FontName=Arial Bold,FontSize=28,PrimaryColour=&H00FFFF00,OutlineColour=&H00000000,BorderStyle=1,Outline=4,Shadow=0,Alignment=2,MarginV=60'",
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'copy',
                final_output
            ]
            
            result = subprocess.run(subtitle_cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                logger.error(f"Subtitle burning failed: {result.stderr}")
                # Use video without subtitles as fallback
                os.rename(temp_video, final_output)
            
            # Move temp video to final output
            if os.path.exists(final_output):
                logger.info(f"Video created successfully: {final_output}")
                
                # Cleanup
                if os.path.exists(concat_file):
                    os.remove(concat_file)
                if os.path.exists(srt_path):
                    os.remove(srt_path)
                if os.path.exists(temp_video):
                    os.remove(temp_video)
                
                return final_output
            else:
                logger.error("Final video not created")
                return None

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg processing timed out")
            return None
        except Exception as e:
            logger.error(f"Video creation failed: {e}", exc_info=True)
            return None

    def _generate_srt(self, text, duration, output_path, audio_path=None):
        """
        Generate SRT subtitle file with sentence-based chunking for better sync.
        Uses actual timestamps from edge-tts for accurate synchronization.
        """
        timestamps_path = None
        if audio_path:
            timestamps_path = audio_path.replace('.mp3', '_timestamps.json')
        
        if timestamps_path and os.path.exists(timestamps_path):
            logger.info(f"Using exact timestamps from {timestamps_path}")
            try:
                with open(timestamps_path, 'r') as f:
                    raw_timestamps = json.load(f)
                
                # Check if timestamps are word-level or sentence-level
                # If average entry has only 1-2 words, it's word-level
                avg_words = sum(len(item['word'].split()) for item in raw_timestamps) / len(raw_timestamps) if raw_timestamps else 0
                
                srt_content = []
                chunk_index = 1
                
                if avg_words < 3:
                    # Word-level timestamps - group into sentences
                    logger.info("Detected word-level timestamps, grouping into sentences...")
                    
                    current_sentence = []
                    sentence_start = None
                    sentence_end = None
                    
                    for i, item in enumerate(raw_timestamps):
                        word = item['word'].strip()
                        start = item['start']
                        end = item['end']
                        
                        if not word:
                            continue
                        
                        # Start new sentence if needed
                        if not current_sentence:
                            sentence_start = start
                        
                        current_sentence.append(word)
                        sentence_end = end
                        
                        # Check if this word ends a sentence
                        ends_sentence = False
                        if word.rstrip()[-1] in ['.', '!', '?']:
                            ends_sentence = True
                        elif i == len(raw_timestamps) - 1:
                            # Last word
                            ends_sentence = True
                        
                        if ends_sentence:
                            # Create subtitle for this sentence
                            sentence_text = ' '.join(current_sentence)
                            
                            # For very long sentences (>15 words), split into two
                            words = current_sentence
                            if len(words) > 15:
                                mid = len(words) // 2
                                
                                # Look for good split points
                                split_points = []
                                for j, w in enumerate(words):
                                    if w.rstrip(',') in ['and', 'but', 'or', 'so', 'yet', 'for', 'nor'] or ',' in w:
                                        split_points.append(j)
                                
                                if split_points:
                                    split_idx = min(split_points, key=lambda x: abs(x - mid))
                                else:
                                    split_idx = mid
                                
                                # Calculate mid time
                                mid_time = sentence_start + (sentence_end - sentence_start) * (split_idx + 1) / len(words)
                                
                                # First half
                                first_half = ' '.join(words[:split_idx + 1])
                                start_str = self._format_srt_time(sentence_start)
                                mid_str = self._format_srt_time(mid_time)
                                srt_content.append(f"{chunk_index}")
                                srt_content.append(f"{start_str} --> {mid_str}")
                                srt_content.append(first_half)
                                srt_content.append("")
                                chunk_index += 1
                                
                                # Second half
                                second_half = ' '.join(words[split_idx + 1:])
                                end_str = self._format_srt_time(sentence_end)
                                srt_content.append(f"{chunk_index}")
                                srt_content.append(f"{mid_str} --> {end_str}")
                                srt_content.append(second_half)
                                srt_content.append("")
                                chunk_index += 1
                            else:
                                # Use sentence as-is
                                start_str = self._format_srt_time(sentence_start)
                                end_str = self._format_srt_time(sentence_end)
                                srt_content.append(f"{chunk_index}")
                                srt_content.append(f"{start_str} --> {end_str}")
                                srt_content.append(sentence_text)
                                srt_content.append("")
                                chunk_index += 1
                            
                            # Reset for next sentence
                            current_sentence = []
                            sentence_start = None
                            sentence_end = None
                else:
                    # Sentence-level timestamps - use directly
                    logger.info("Detected sentence-level timestamps, using directly...")
                    
                    for item in raw_timestamps:
                        subtitle_text = item['word'].strip()
                        start = item['start']
                        end = item['end']
                        
                        if not subtitle_text:
                            continue
                        
                        # For very long sentences (>15 words), split into multiple lines
                        words = subtitle_text.split()
                        if len(words) > 15:
                            mid = len(words) // 2
                            
                            split_points = []
                            for i, word in enumerate(words):
                                if word.rstrip(',') in ['and', 'but', 'or', 'so', 'yet', 'for', 'nor'] or ',' in word:
                                    split_points.append(i)
                            
                            if split_points:
                                split_idx = min(split_points, key=lambda x: abs(x - mid))
                            else:
                                split_idx = mid
                            
                            first_half = ' '.join(words[:split_idx + 1])
                            second_half = ' '.join(words[split_idx + 1:])
                            
                            mid_time = start + (end - start) * (split_idx + 1) / len(words)
                            
                            # First half
                            start_str = self._format_srt_time(start)
                            mid_str = self._format_srt_time(mid_time)
                            srt_content.append(f"{chunk_index}")
                            srt_content.append(f"{start_str} --> {mid_str}")
                            srt_content.append(first_half)
                            srt_content.append("")
                            chunk_index += 1
                            
                            # Second half
                            end_str = self._format_srt_time(end)
                            srt_content.append(f"{chunk_index}")
                            srt_content.append(f"{mid_str} --> {end_str}")
                            srt_content.append(second_half)
                            srt_content.append("")
                            chunk_index += 1
                        else:
                            # Use the sentence as-is
                            start_str = self._format_srt_time(start)
                            end_str = self._format_srt_time(end)
                            
                            srt_content.append(f"{chunk_index}")
                            srt_content.append(f"{start_str} --> {end_str}")
                            srt_content.append(subtitle_text)
                            srt_content.append("")
                            chunk_index += 1
                
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(srt_content))
                
                logger.info(f"Generated sentence-based SRT with {chunk_index-1} subtitles")
                return
                
            except Exception as e:
                logger.error(f"Failed to use timestamps: {e}. Falling back to sentence parsing.")
        
        # Fallback: Parse text into sentences manually
        logger.warning("No timestamps found, using sentence-based parsing fallback")
        
        import re
        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            logger.error("No sentences found in text")
            return
        
        # Calculate timing for each sentence based on word count
        total_words = sum(len(s.split()) for s in sentences)
        time_per_word = duration / total_words if total_words > 0 else 0
        
        srt_content = []
        current_time = 0.0
        
        for i, sentence in enumerate(sentences, 1):
            words_in_sentence = len(sentence.split())
            sentence_duration = words_in_sentence * time_per_word
            
            # Ensure minimum display time of 1.5 seconds
            sentence_duration = max(sentence_duration, 1.5)
            
            # Ensure maximum display time of 6 seconds
            sentence_duration = min(sentence_duration, 6.0)
            
            start_time = current_time
            end_time = current_time + sentence_duration
            
            # Don't exceed total duration
            if end_time > duration:
                end_time = duration
            
            start_str = self._format_srt_time(start_time)
            end_str = self._format_srt_time(end_time)
            
            srt_content.append(f"{i}")
            srt_content.append(f"{start_str} --> {end_str}")
            srt_content.append(sentence)
            srt_content.append("")
            
            current_time = end_time
            
            # Stop if we've reached the end
            if current_time >= duration:
                break
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srt_content))
        
        logger.info(f"Generated fallback sentence-based SRT with {len(sentences)} subtitles")
    
    def _format_srt_time(self, seconds):
        """Format seconds as SRT timestamp: HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def _get_audio_duration(self, audio_path):
        """Get audio duration using FFprobe"""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                audio_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            data = json.loads(result.stdout)
            duration = float(data['format']['duration'])
            return duration
        except Exception as e:
            logger.error(f"Failed to get audio duration: {e}")
            return 60  # Default to 60 seconds

if __name__ == "__main__":
    # Mock test
    pass
