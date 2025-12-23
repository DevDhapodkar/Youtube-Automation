"""
Scene-Based Video Generation Orchestrator

This module orchestrates the entire scene-based video generation pipeline:
1. Parse script into scenes
2. Generate audio per scene
3. Get visuals per scene
4. Render each scene
5. Concatenate into final video
"""

import logging
import os
from typing import List
from config.settings import Config
from src.content.scene_manager import SceneManager, Scene
from src.content.audio_generator import AudioGenerator
from src.content.scene_visual_coordinator import SceneVisualCoordinator
from src.video.scene_based_editor import SceneBasedVideoEditor
from src.audio.sound_effects import SoundEffectGenerator

logger = logging.getLogger(__name__)

class SceneBasedVideoOrchestrator:
    """
    Orchestrates the complete scene-based video generation pipeline.
    """
    
    def __init__(self):
        self.scene_manager = SceneManager(
            min_scene_duration=Config.SCENE_DURATION_MIN,
            max_scene_duration=Config.SCENE_DURATION_MAX
        )
        self.audio_gen = AudioGenerator()
        self.visual_coordinator = SceneVisualCoordinator()
        self.video_editor = SceneBasedVideoEditor()
        self.sfx_gen = SoundEffectGenerator()
    
    def create_video(
        self,
        script: str,
        output_path: str,
        target_duration: int = 60,
        niche: str = "general",
        stop_check: callable = None,
        pre_generated_scenes: List[dict] = None,
        orientation: str = None  # Auto-detect if None
    ) -> str:
        """
        Create a complete video from script using scene-based approach.
        """
        # Determine orientation if not provided
        if not orientation:
            orientation = "landscape" if target_duration > 90 else "portrait"
            
        logger.info("=" * 70)
        logger.info(f"SCENE-BASED VIDEO GENERATION STARTED ({orientation})")
        logger.info("=" * 70)
        
        try:
            if stop_check and stop_check():
                logger.info("Generation stopped by user")
                return None

            # Ensure assets directory exists
            if not os.path.exists(Config.ASSETS_DIR):
                os.makedirs(Config.ASSETS_DIR)
            
            # Step 1: Parse script into scenes
            logger.info("\n[1/6] Parsing script into scenes...")
            scenes = self.scene_manager.parse_script_to_scenes(script, target_duration, pre_generated_scenes=pre_generated_scenes)
            
            if not scenes:
                logger.error("Failed to parse script into scenes")
                return None
            
            if stop_check and stop_check():
                logger.info("Generation stopped by user")
                return None

            logger.info(f"✓ Created {len(scenes)} scenes")
            logger.info("\n" + self.scene_manager.get_scene_summary(scenes))
            
            # Step 2: Generate audio and SFX for each scene
            logger.info("\n[2/6] Generating audio and SFX for each scene...")
            audio_paths = self._generate_scene_audio(scenes)
            sfx_paths = self._get_scene_sfx(scenes)
            
            if len(audio_paths) != len(scenes):
                logger.error("Audio generation failed for some scenes")
                return None
            
            if stop_check and stop_check():
                logger.info("Generation stopped by user")
                return None
            
            logger.info(f"✓ Generated audio/SFX for {len(audio_paths)} scenes")
            
            # Step 3: Get visuals for each scene
            logger.info("\n[3/6] Getting visuals for each scene...")
            visual_paths_per_scene = self._get_scene_visuals(scenes, orientation)
            
            if len(visual_paths_per_scene) != len(scenes):
                logger.error("Visual generation failed for some scenes")
                return None
            
            if stop_check and stop_check():
                logger.info("Generation stopped by user")
                return None

            total_visuals = sum(len(v) for v in visual_paths_per_scene)
            logger.info(f"✓ Got {total_visuals} visuals across {len(scenes)} scenes")
            
            # Step 4: Render video scene-by-scene
            logger.info("\n[4/6] Rendering scene-based video...")
            temp_video = os.path.join(Config.ASSETS_DIR, "temp_no_music.mp4")
            rendered_video = self.video_editor.create_scene_based_video(
                scenes=scenes,
                audio_paths=audio_paths,
                sfx_paths=sfx_paths,
                visual_paths_per_scene=visual_paths_per_scene,
                output_path=temp_video,
                niche=niche,
                orientation=orientation
            )
            
            if not rendered_video:
                logger.error("Video rendering failed")
                return None
            
            if stop_check and stop_check():
                logger.info("Generation stopped by user")
                return None
            
            logger.info(f"✓ Video rendered successfully")
            
            # Step 5: Add Background Music
            logger.info("\n[5/6] Adding background music...")
            final_video = self._add_background_music(rendered_video, output_path, niche)
            
            if not final_video:
                logger.warning("Failed to add music, using silent video")
                final_video = rendered_video
            
            # Step 6: Cleanup
            logger.info("\n[6/6] Cleaning up temporary files...")
            self._cleanup_temp_files(audio_paths)
            if os.path.exists(temp_video) and temp_video != final_video:
                os.remove(temp_video)
            logger.info("✓ Cleanup complete")
            
            logger.info("\n" + "=" * 70)
            logger.info(f"✓ SCENE-BASED VIDEO GENERATION COMPLETE: {final_video}")
            logger.info("=" * 70)
            
            return final_video
            
        except Exception as e:
            logger.error(f"Video generation failed: {e}", exc_info=True)
            return None

    def _add_background_music(self, video_path: str, output_path: str, niche: str) -> str:
        """Add ambient background music to the video."""
        try:
            ambient_sound = self.sfx_gen.get_ambient_sound(niche)
            
            if not ambient_sound:
                logger.info("No ambient sound found, skipping music")
                # Just rename/copy the video
                if video_path != output_path:
                    import shutil
                    shutil.move(video_path, output_path)
                return output_path
            
            logger.info(f"Mixing background music: {os.path.basename(ambient_sound)}")
            
            import subprocess
            
            # Mix command: loop ambient, volume 0.15, mix with video audio
            mix_cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-stream_loop', '-1',
                '-i', ambient_sound,
                '-filter_complex', '[1:a]volume=0.15[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2[aout]',
                '-map', '0:v',
                '-map', '[aout]',
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-b:a', '192k',
                output_path
            ]
            
            result = subprocess.run(mix_cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and os.path.exists(output_path):
                logger.info("✓ Background music added")
                return output_path
            else:
                logger.error(f"Failed to add music: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Error adding background music: {e}")
            return None
    
    def _generate_scene_audio(self, scenes: List[Scene]) -> List[str]:
        """Generate audio for each scene."""
        audio_paths = []
        
        for scene in scenes:
            logger.info(f"  Generating audio for scene {scene.scene_id}...")
            
            audio_path = os.path.join(
                Config.ASSETS_DIR,
                f"scene_{scene.scene_id}_audio.mp3"
            )
            
            result = self.audio_gen.generate_audio(
                text=scene.text,
                output_file=audio_path,
                target_duration=int(scene.duration)
            )
            
            if result:
                audio_paths.append(result)
                logger.info(f"    ✓ Scene {scene.scene_id} audio generated")
            else:
                logger.error(f"    ✗ Scene {scene.scene_id} audio failed")
                return []
        
        return audio_paths
    
    def _get_scene_sfx(self, scenes: List[Scene]) -> List[str]:
        """Fetch sound effects for each scene if specified."""
        sfx_paths = []
        for scene in scenes:
            if scene.sfx_description:
                logger.info(f"  Fetching SFX for scene {scene.scene_id}: {scene.sfx_description}")
                path = self.sfx_gen.get_contextual_sfx(scene.sfx_description)
                sfx_paths.append(path)
            else:
                sfx_paths.append(None)
        return sfx_paths

    def _get_scene_visuals(self, scenes: List[Scene], orientation: str) -> List[List[str]]:
        """Get visuals for each scene."""
        visual_paths_per_scene = []
        
        for scene in scenes:
            logger.info(f"  Getting visuals for scene {scene.scene_id}...")
            
            visuals = self.visual_coordinator.get_visuals_for_scene(scene, min_visuals=2, orientation=orientation)
            
            if visuals:
                visual_paths_per_scene.append(visuals)
                logger.info(f"    ✓ Scene {scene.scene_id}: {len(visuals)} visuals")
            else:
                logger.error(f"    ✗ Scene {scene.scene_id}: No visuals")
                return []
        
        return visual_paths_per_scene
    
    def _cleanup_temp_files(self, audio_paths: List[str]):
        """Clean up temporary audio files."""
        for audio_path in audio_paths:
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
                
                # Also remove timestamps and SRT files
                timestamps_path = audio_path.replace('.mp3', '_timestamps.json')
                if os.path.exists(timestamps_path):
                    os.remove(timestamps_path)
                
                srt_path = audio_path.replace('.mp3', '.srt')
                if os.path.exists(srt_path):
                    os.remove(srt_path)
                    
            except Exception as e:
                logger.warning(f"Failed to cleanup {audio_path}: {e}")


if __name__ == "__main__":
    # Test the orchestrator
    test_script = """
    Welcome to this amazing video about artificial intelligence. 
    AI is transforming the world in incredible ways. 
    From healthcare to entertainment, the possibilities are endless. 
    Machine learning algorithms can now recognize patterns that humans might miss.
    Deep learning has revolutionized computer vision and natural language processing.
    The future of AI holds even more exciting developments.
    Let's explore how this technology is shaping our future.
    """
    
    orchestrator = SceneBasedVideoOrchestrator()
    
    output_path = os.path.join(Config.ASSETS_DIR, "test_scene_based_video.mp4")
    
    result = orchestrator.create_video(
        script=test_script,
        output_path=output_path,
        target_duration=30,
        niche="general"
    )
    
    if result:
        print(f"\n✓ Test video created: {result}")
    else:
        print("\n✗ Test video creation failed")
