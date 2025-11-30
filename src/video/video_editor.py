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
            
            # Create concat list with processed visuals
            with open(concat_file, 'w') as f:
                for video_path in processed_visuals:
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

            # Get color grading filter for niche
            color_filter = self._get_color_filter(niche)

            # Concatenate videos, scale, apply color grading, crop, and add subtitles
            filter_chain = f"[0:v]scale={self.resolution[0]}:{self.resolution[1]}:force_original_aspect_ratio=increase[vscaled];[vscaled]{color_filter}[vgraded];[vgraded]crop={self.resolution[0]}:{self.resolution[1]}[vcropped];[vcropped]{subtitles_filter}[vfinal]"
            
            concat_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-i', audio_path,
                '-t', str(duration),
                '-filter_complex', filter_chain,
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
