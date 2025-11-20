import logging
import os
from moviepy import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
from config.settings import Config
import math

logger = logging.getLogger(__name__)

class VideoEditor:
    def __init__(self):
        self.resolution = Config.VIDEO_RESOLUTION # (1080, 1920)
        self.fps = Config.FPS

    def create_short(self, audio_path, visual_paths, script_text, output_path="final_video.mp4"):
        """
        Assembles the video.
        """
        logger.info("Starting video assembly...")
        
        try:
            # 1. Load Audio
            audio = AudioFileClip(audio_path)
            duration = audio.duration
            logger.info(f"Audio duration: {duration}s")

            # 2. Prepare Visuals
            clips = []
            current_duration = 0
            
            # Loop through visuals until we cover the audio duration
            while current_duration < duration:
                for v_path in visual_paths:
                    if current_duration >= duration:
                        break
                    
                    try:
                        clip = VideoFileClip(v_path)
                        # Resize to vertical 9:16 (fill)
                        # Assuming 1080x1920
                        
                        # Calculate resize factor to fill height
                        # clip_h = clip.h
                        # target_h = 1920
                        # ratio = target_h / clip_h
                        # clip = clip.resize(ratio)
                        
                        # Simple resize (might distort if aspect ratio is wild, but usually okay for stock)
                        # Better: crop to center
                        if clip.w / clip.h > 1080 / 1920:
                            # Too wide, crop width
                            clip = clip.resize(height=1920)
                            clip = clip.crop(x1=clip.w/2 - 540, width=1080)
                        else:
                            # Too tall/narrow, crop height
                            clip = clip.resize(width=1080)
                            # clip = clip.crop(y1=clip.h/2 - 960, height=1920)
                        
                        # Set duration for this clip (e.g., 3-5 seconds or remaining time)
                        clip_duration = min(clip.duration, 5, duration - current_duration)
                        clip = clip.subclip(0, clip_duration)
                        
                        clips.append(clip)
                        current_duration += clip_duration
                    except Exception as e:
                        logger.error(f"Error processing clip {v_path}: {e}")

            if not clips:
                logger.error("No valid clips created.")
                return None

            final_visual = concatenate_videoclips(clips, method="compose")
            final_visual = final_visual.set_audio(audio)

            # 3. Add Subtitles (Simple centered text)
            # Splitting text into chunks
            words = script_text.split()
            chunk_size = 5 # words per chunk
            chunks = [" ".join(words[i:i+chunk_size]) for i in range(0, len(words), chunk_size)]
            
            chunk_duration = duration / len(chunks)
            
            text_clips = []
            for i, chunk in enumerate(chunks):
                txt_clip = TextClip(chunk, fontsize=70, color='white', font='Arial-Bold', 
                                    stroke_color='black', stroke_width=2, size=(1000, None), method='caption')
                txt_clip = txt_clip.set_position('center').set_duration(chunk_duration).set_start(i * chunk_duration)
                text_clips.append(txt_clip)

            final_video = CompositeVideoClip([final_visual] + text_clips)
            
            # 4. Write File
            logger.info(f"Writing video to {output_path}")
            final_video.write_videofile(output_path, fps=self.fps, codec='libx264', audio_codec='aac')
            
            return output_path

        except Exception as e:
            logger.error(f"Video creation failed: {e}", exc_info=True)
            return None

if __name__ == "__main__":
    # Mock test
    pass
