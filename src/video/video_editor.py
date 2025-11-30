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
            
            # 3. Generate Subtitles (SRT)
            srt_path = os.path.join(Config.ASSETS_DIR, "subtitles.srt")
            self._generate_srt(script_text, duration, srt_path)
            
            # 4. Concatenate and process videos with FFmpeg
            temp_video = os.path.join(Config.ASSETS_DIR, "temp_concatenated.mp4")
            
            # Style for subtitles: Huge, Yellow with Black Outline, Bottom Center
            # FontSize is somewhat arbitrary in ffmpeg, 24 is usually decent size, 30+ is huge.
            # PrimaryColour=&H0000FFFF (Yellow in BGR hex: 00 + Blue=00, Green=FF, Red=FF) -> &H0000FFFF
            # Actually ASS color format is &HAABBGGRR. Yellow is R=FF, G=FF, B=00. So &H0000FFFF.
            # Wait, &H0000FFFF is Cyan? No, &H00(Alpha)00(B)FF(G)FF(R).
            # Yellow: R=255, G=255, B=0. -> &H0000FFFF.
            
            subtitles_filter = f"subtitles={srt_path}:force_style='FontName=Arial,FontSize=24,PrimaryColour=&H0000FFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=0,Alignment=2,MarginV=50'"

            # Concatenate videos, scale to 1080x1920, trim, and add subtitles
            concat_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-i', audio_path,
                '-t', str(duration),
                '-filter_complex', f"[0:v]scale={self.resolution[0]}:{self.resolution[1]}:force_original_aspect_ratio=increase,crop={self.resolution[0]}:{self.resolution[1]}[vscaled];[vscaled]{subtitles_filter}[vfinal]",
                '-map', '[vfinal]',
                '-map', '1:a:0',
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-crf', '28',
                '-c:a', 'aac',
                '-b:a', '128k',
                '-shortest',
                temp_video
            ]
            
            logger.info("Running FFmpeg concatenation...")
            result = subprocess.run(concat_cmd, capture_output=True, text=True, timeout=180)
            
            if result.returncode != 0:
                logger.error(f"FFmpeg concat failed: {result.stderr}")
                return None
            
            # Move temp video to final output
            if os.path.exists(temp_video):
                os.rename(temp_video, output_path)
                logger.info(f"Video created successfully: {output_path}")
                
                # Cleanup
                if os.path.exists(concat_file):
                    os.remove(concat_file)
                if os.path.exists(srt_path):
                    os.remove(srt_path)
                
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

    def _generate_srt(self, text, duration, output_path):
        """
        Generates a simple SRT file by distributing text evenly across duration.
        """
        words = text.split()
        word_count = len(words)
        if word_count == 0:
            return

        # Group words into chunks (e.g., 3-4 words per chunk for readability)
        chunk_size = 4
        chunks = [' '.join(words[i:i+chunk_size]) for i in range(0, word_count, chunk_size)]
        
        chunk_duration = duration / len(chunks)
        
        with open(output_path, 'w') as f:
            for i, chunk in enumerate(chunks):
                start_time = i * chunk_duration
                end_time = (i + 1) * chunk_duration
                
                # Format time as HH:MM:SS,mmm
                start_fmt = self._format_time(start_time)
                end_fmt = self._format_time(end_time)
                
                f.write(f"{i+1}\n")
                f.write(f"{start_fmt} --> {end_fmt}\n")
                f.write(f"{chunk}\n\n")

    def _format_time(self, seconds):
        """Convert seconds to HH:MM:SS,mmm format"""
        millis = int((seconds - int(seconds)) * 1000)
        seconds = int(seconds)
        minutes = seconds // 60
        hours = minutes // 60
        minutes %= 60
        seconds %= 60
        return f"{hours:02}:{minutes:02}:{seconds:02},{millis:03}"

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
