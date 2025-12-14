import logging
import os
import subprocess
import json
from typing import List
from config.settings import Config
from src.content.scene_manager import Scene

logger = logging.getLogger(__name__)


class SceneBasedVideoEditor:
    """
    Scene-based video editor that processes videos scene-by-scene
    with proper transitions and subtitle synchronization.
    """
    
    def __init__(self):
        self.resolution = Config.VIDEO_RESOLUTION  # (1080, 1920)
        self.fps = Config.FPS
        self.transition_duration = Config.TRANSITION_DURATION
    
    def create_scene_based_video(
        self,
        scenes: List[Scene],
        audio_paths: List[str],
        visual_paths_per_scene: List[List[str]],
        output_path: str = "final_video.mp4",
        niche: str = "general"
    ) -> str:
        """
        Create video using scene-based approach.
        
        Args:
            scenes: List of Scene objects
            audio_paths: List of audio file paths (one per scene)
            visual_paths_per_scene: List of lists of visual paths (per scene)
            output_path: Final output video path
            niche: Visual style/niche for color grading
            
        Returns:
            Path to final video, or None if failed
        """
        logger.info(f"Creating scene-based video with {len(scenes)} scenes")
        
        try:
            # Step 1: Render each scene individually
            scene_videos = []
            for idx, scene in enumerate(scenes):
                logger.info(f"Rendering scene {scene.scene_id}/{len(scenes)}")
                
                scene_video = self._render_single_scene(
                    scene=scene,
                    audio_path=audio_paths[idx],
                    visual_paths=visual_paths_per_scene[idx],
                    niche=niche
                )
                
                if scene_video and os.path.exists(scene_video):
                    scene_videos.append(scene_video)
                else:
                    logger.error(f"Failed to render scene {scene.scene_id}")
                    return None
            
            # Step 2: Concatenate scenes with transitions
            logger.info("Concatenating scenes with transitions...")
            final_video = self._concatenate_scenes_with_transitions(
                scene_videos,
                output_path
            )
            
            # Step 3: Cleanup intermediate files
            self._cleanup_scene_files(scene_videos)
            
            if final_video and os.path.exists(final_video):
                logger.info(f"✓ Scene-based video created: {final_video}")
                return final_video
            else:
                logger.error("Final video assembly failed")
                return None
                
        except Exception as e:
            logger.error(f"Scene-based video creation failed: {e}", exc_info=True)
            return None
    
    def _render_single_scene(
        self,
        scene: Scene,
        audio_path: str,
        visual_paths: List[str],
        niche: str
    ) -> str:
        """
        Render a single scene with audio, visuals, and subtitles.
        
        Returns:
            Path to rendered scene video
        """
        scene_output = os.path.join(
            Config.ASSETS_DIR,
            f"scene_{scene.scene_id}.mp4"
        )
        
        try:
            # Get audio duration
            duration = self._get_audio_duration(audio_path)
            
            if not visual_paths:
                logger.error(f"No visuals for scene {scene.scene_id}")
                return None
            
            # Process visuals (apply Ken Burns to images)
            processed_visuals = self._process_visuals(visual_paths, scene.scene_id)
            
            # Create concat file for visuals
            concat_file = self._create_visual_concat_file(
                processed_visuals,
                duration,
                scene.scene_id
            )
            
            # Generate subtitles for this scene
            srt_path = self._generate_scene_subtitles(scene, audio_path)
            
            # Get color filter
            color_filter = self._get_color_filter(niche)
            
            # Build FFmpeg command for scene
            temp_video = os.path.join(Config.ASSETS_DIR, f"scene_{scene.scene_id}_temp.mp4")
            
            # Concatenate visuals and add audio
            filter_chain = f"[0:v]setpts=PTS-STARTPTS,scale={self.resolution[0]}:{self.resolution[1]}:force_original_aspect_ratio=increase[vscaled];[vscaled]{color_filter}[vgraded];[vgraded]crop={self.resolution[0]}:{self.resolution[1]}[vcropped]"
            
            concat_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat',
                '-safe', '0',
                '-i', concat_file,
                '-i', audio_path,
                '-filter_complex', filter_chain,
                '-map', '[vcropped]',
                '-map', '1:a:0',
                '-t', str(duration),
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'aac',
                '-b:a', '192k',
                temp_video
            ]
            
            result = subprocess.run(concat_cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode != 0:
                logger.error(f"Scene {scene.scene_id} video assembly failed: {result.stderr}")
                return None
            
            # Add subtitles (Hormozi Style: Yellow, Bold, Centered-ish)
            # MarginV=250 moves it up from the bottom to avoid Shorts/Reels UI
            subtitle_cmd = [
                'ffmpeg', '-y',
                '-i', temp_video,
                '-vf', f"subtitles={srt_path}:force_style='FontName=Arial,FontSize=14,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=1,Shadow=1,Alignment=2,MarginV=150,Bold=1'",
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-c:a', 'copy',
                scene_output
            ]
            
            result = subprocess.run(subtitle_cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                logger.warning(f"Subtitle burning failed for scene {scene.scene_id}, using video without subtitles")
                os.rename(temp_video, scene_output)
            else:
                # Clean up temp file
                if os.path.exists(temp_video):
                    os.remove(temp_video)
            
            # Clean up concat file and srt
            if os.path.exists(concat_file):
                os.remove(concat_file)
            if os.path.exists(srt_path):
                os.remove(srt_path)
            
            return scene_output
            
        except Exception as e:
            logger.error(f"Scene {scene.scene_id} rendering failed: {e}")
            return None
    
    def _process_visuals(self, visual_paths: List[str], scene_id: int) -> List[str]:
        """
        Process visuals - normalize ALL inputs to target resolution/fps for reliable concatenation.
        This fixes the 'video stuck' issue caused by mixing different resolutions/codecs.
        """
        processed = []
        
        for idx, visual_path in enumerate(visual_paths):
            output_name = f"scene_{scene_id}_norm_{idx}.mp4"
            output_path = os.path.join(Config.ASSETS_DIR, output_name)
            
            # Skip if already processed (optimization)
            if os.path.exists(output_path):
                processed.append(output_path)
                continue
                
            ext = os.path.splitext(visual_path)[1].lower()
            
            if ext in ['.jpg', '.jpeg', '.png']:
                # Apply Ken Burns effect to images
                cmd = [
                    'ffmpeg', '-y',
                    '-loop', '1',
                    '-i', visual_path,
                    '-vf', f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,zoompan=z='min(zoom+0.0015,1.5)':d=150:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920",
                    '-t', '5',
                    '-r', str(self.fps),
                    '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p',
                    output_path
                ]
            else:
                # Normalize video clips (scale, crop, fps)
                cmd = [
                    'ffmpeg', '-y',
                    '-i', visual_path,
                    '-vf', f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                    '-r', str(self.fps),
                    '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p',
                    '-an', # Remove audio from visual clips
                    output_path
                ]
            
            try:
                subprocess.run(cmd, capture_output=True, timeout=60)
                if os.path.exists(output_path):
                    processed.append(output_path)
                else:
                    logger.warning(f"Failed to normalize {visual_path}")
            except Exception as e:
                logger.error(f"Error processing visual {visual_path}: {e}")
                
        return processed

    def _create_visual_concat_file(self, visual_paths: List[str], duration: float, scene_id: int) -> str:
        """Create concat file for visuals, looping to fill duration."""
        concat_file = os.path.join(Config.ASSETS_DIR, f"scene_{scene_id}_concat.txt")
        
        # Get duration of each visual
        visual_durations = []
        for visual in visual_paths:
            try:
                dur = self._get_video_duration(visual)
                visual_durations.append(dur)
            except:
                visual_durations.append(5.0)
        
        total_visual_duration = sum(visual_durations)
        
        # Calculate loops needed
        if total_visual_duration > 0:
            loops_needed = int(duration / total_visual_duration) + 2
        else:
            loops_needed = 3
        
        with open(concat_file, 'w') as f:
            for _ in range(loops_needed):
                for video_path in visual_paths:
                    f.write(f"file '{video_path}'\n")
        
        return concat_file
    
    def _generate_scene_subtitles(self, scene: Scene, audio_path: str) -> str:
        """Generate SRT file for a single scene."""
        srt_path = os.path.join(Config.ASSETS_DIR, f"scene_{scene.scene_id}.srt")
        
        # Check for timestamps
        timestamps_path = audio_path.replace('.mp3', '_timestamps.json')
        
        if os.path.exists(timestamps_path):
            # Use timestamps to create accurate subtitles
            with open(timestamps_path, 'r') as f:
                timestamps = json.load(f)
            
            # Group words into sentences
            srt_content = self._create_srt_from_timestamps(timestamps, scene.text)
        else:
            # Fallback: create simple subtitle for whole scene
            srt_content = self._create_simple_srt(scene)
        
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
        
        return srt_path

    def _create_srt_from_timestamps(self, timestamps: List[dict], scene_text: str) -> str:
        """
        Create SRT content from word timestamps, grouping into full sentences.
        """
        srt_lines = []
        subtitle_index = 1
        
        # Group words into sentences based on punctuation
        current_sentence = []
        sentence_start = None
        sentence_end = None
        
        for item in timestamps:
            word = item['word'].strip()
            start = item['start']
            end = item['end']
            
            if not word:
                continue
            
            if not current_sentence:
                sentence_start = start
            
            current_sentence.append(word)
            sentence_end = end
            
            # Check if sentence ends or if it's getting too long (max 3 lines approx 15-20 words)
            is_end_of_sentence = word.rstrip()[-1] in ['.', '!', '?']
            is_too_long = len(current_sentence) > 15
            is_last_word = (item == timestamps[-1])
            
            if is_end_of_sentence or is_too_long or is_last_word:
                # Create subtitle entry
                sentence_text = ' '.join(current_sentence)
                start_str = self._format_srt_time(sentence_start)
                end_str = self._format_srt_time(sentence_end)
                
                srt_lines.append(f"{subtitle_index}")
                srt_lines.append(f"{start_str} --> {end_str}")
                srt_lines.append(sentence_text)
                srt_lines.append("")
                
                subtitle_index += 1
                current_sentence = []
        
        return '\n'.join(srt_lines)
    
    def _create_simple_srt(self, scene: Scene) -> str:
        """Create simple SRT for entire scene."""
        start_str = self._format_srt_time(0)
        end_str = self._format_srt_time(scene.duration)
        
        return f"1\n{start_str} --> {end_str}\n{scene.text}\n\n"
    
    def _concatenate_scenes_with_transitions(self, scene_videos: List[str], output_path: str) -> str:
        """Concatenate scene videos with crossfade transitions."""
        if len(scene_videos) == 1:
            # Only one scene, just copy it
            import shutil
            shutil.copy(scene_videos[0], output_path)
            return output_path
        
        # For multiple scenes, use concat demuxer (simple concatenation)
        # Note: Advanced crossfade transitions require complex filter_complex
        # For now, using simple concatenation for reliability
        
        concat_file = os.path.join(Config.ASSETS_DIR, "final_concat.txt")
        
        with open(concat_file, 'w') as f:
            for video in scene_videos:
                f.write(f"file '{video}'\n")
        
        concat_cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', concat_file,
            '-c', 'copy',
            output_path
        ]
        
        result = subprocess.run(concat_cmd, capture_output=True, text=True, timeout=180)
        
        if os.path.exists(concat_file):
            os.remove(concat_file)
        
        if result.returncode != 0:
            logger.error(f"Scene concatenation failed: {result.stderr}")
            return None
        
        return output_path
    
    def _get_color_filter(self, niche: str) -> str:
        """Get FFmpeg color grading filter for niche."""
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
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds as SRT timestamp: HH:MM:SS,mmm"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"
    
    def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio duration using FFprobe."""
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
            return float(data['format']['duration'])
        except Exception as e:
            logger.error(f"Failed to get audio duration: {e}")
            return 10.0  # Default
    
    def _get_video_duration(self, video_path: str) -> float:
        """Get video duration using FFprobe."""
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                video_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            return float(result.stdout.strip())
        except Exception as e:
            logger.error(f"Failed to get video duration: {e}")
            return 5.0  # Default
    
    def _cleanup_scene_files(self, scene_videos: List[str]):
        """Clean up intermediate scene video files."""
        for video in scene_videos:
            try:
                if os.path.exists(video):
                    os.remove(video)
                    logger.debug(f"Cleaned up: {video}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {video}: {e}")
        
        # Clean up Ken Burns videos
        kb_pattern = os.path.join(Config.ASSETS_DIR, "scene_*_kb_*.mp4")
        import glob
        for kb_file in glob.glob(kb_pattern):
            try:
                os.remove(kb_file)
            except:
                pass


if __name__ == "__main__":
    # Test scene-based video editor
    pass
