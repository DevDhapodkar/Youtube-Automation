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

    def create_short(self, audio_path, visual_paths, script_text, output_path="final_video.mp4"):
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
            with open(concat_file, 'w') as f:
                for video_path in visual_paths:
                    # Repeat each video to fill duration
                    f.write(f"file '{video_path}'\n")
            
            # 3. Concatenate and process videos with FFmpeg
            temp_video = os.path.join(Config.ASSETS_DIR, "temp_concatenated.mp4")
            
            # Concatenate videos, scale to 1080x1920, and trim to audio duration
            concat_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-i', audio_path,
                '-t', str(duration),
                '-vf', f'scale={self.resolution[0]}:{self.resolution[1]}:force_original_aspect_ratio=increase,crop={self.resolution[0]}:{self.resolution[1]}',
                '-c:v', 'libx264',
                '-preset', 'ultrafast',  # Fast encoding
                '-crf', '28',  # Lower quality = less memory
                '-c:a', 'aac',
                '-b:a', '128k',
                '-shortest',
                '-map', '0:v:0',  # video from concat
                '-map', '1:a:0',  # audio from audio file
                temp_video
            ]
            
            logger.info("Running FFmpeg concatenation...")
            result = subprocess.run(concat_cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg concat failed: {result.stderr}")
                return None
            
            # 4. Add simple text overlay (optional - can skip to save memory)
            # For now, skip text overlay to keep it lightweight
            # You can add it later with: -vf "drawtext=..." if needed
            
            # Move temp video to final output
            if os.path.exists(temp_video):
                os.rename(temp_video, output_path)
                logger.info(f"Video created successfully: {output_path}")
                
                # Cleanup
                if os.path.exists(concat_file):
                    os.remove(concat_file)
                
                return output_path
            else:
                logger.error("Temp video not created")
                return None

        except subprocess.TimeoutExpired:
            logger.error("FFmpeg processing timed out")
            return None
        except Exception as e:
            logger.error(f"Video creation failed: {e}", exc_info=True)
            return None

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
