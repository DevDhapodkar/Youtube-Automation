import logging
import requests
import os
import time
from gradio_client import Client, handle_file

logger = logging.getLogger(__name__)


class MochiGenerator:
    """
    Generate AI videos using Genmo Mochi 1.
    Free tier: Unlimited usage through web playground.
    """
    
    def __init__(self):
        self.enabled = True
        try:
            # Genmo Mochi 1 - Free, unlimited
            hf_token = os.getenv("HUGGINGFACE_API_KEY")
            # List of spaces to try (Best to Backup)
            spaces_to_try = [
                "DeepRat/LTX-Video-ZeroGPU-Optimized",
                "genmo/mochi-1-preview",
                "https://genmo-mochi-1-preview.hf.space",
                "KingNish/mochi-1-preview",
                "https://kingnish-mochi-1-preview.hf.space",
                "multimodalart/mochi-1-preview",
                "cerspense/zeroscope_v2_576w",
                "damo-vilab/text-to-video-ms-1.7b",
                "ali-vilab/modelscope-damo-text-to-video-synthesis"
            ]
            
            self.client = None
            last_error = None
            
            if hf_token:
                logger.info("Found Hugging Face token")
            else:
                logger.warning("No Hugging Face token found")

            for space in spaces_to_try:
                # Try with token first (if available)
                if hf_token:
                    try:
                        logger.info(f"Attempting to connect to {space} (with token)...")
                        self.client = Client(space, token=hf_token)
                        logger.info(f"✓ Connected to {space}")
                        self.model_name = space
                        break
                    except Exception as e:
                        logger.warning(f"Failed to connect to {space} with token: {e}")
                
                # Try without token (public access)
                try:
                    logger.info(f"Attempting to connect to {space} (without token)...")
                    self.client = Client(space)
                    logger.info(f"✓ Connected to {space}")
                    self.model_name = space
                    break
                except Exception as e:
                    logger.warning(f"Failed to connect to {space} without token: {e}")
                    last_error = e
            
            if not self.client:
                raise last_error or Exception("All AI video spaces failed")
                
            logger.info(f"AI Video Generator initialized with {self.model_name}")
        except Exception as e:
            logger.warning(f"Mochi initialization failed: {e}. AI video generation disabled.")
            self.enabled = False
    
    def generate_video(self, prompt: str, output_path: str, duration: int = 5) -> str:
        """
        Generate a video from text prompt.
        
        Args:
            prompt: Text description of the video
            output_path: Path to save generated video
            duration: Target duration in seconds (Mochi generates ~5s clips)
            
        Returns:
            Path to generated video, or None if failed
        Generate video from prompt using the initialized model.
        """
        if not self.enabled or not self.client:
            return None
            
        logger.info(f"Generating AI video with {self.model_name} for: {prompt}")
        
        try:
            # Mochi Logic
            if "mochi" in self.model_name.lower():
                result = self.client.predict(
                    prompt,	# str  in 'Prompt' Textbox component
                    "",	# str  in 'Negative prompt' Textbox component
                    0,	# int | float (numeric value between 0 and 2147483647) in 'Seed' Slider component
                    True,	# bool  in 'Randomize seed' Checkbox component
                    1920,	# int | float (numeric value between 1024 and 1920) in 'Width' Slider component
                    1080,	# int | float (numeric value between 1024 and 1920) in 'Height' Slider component
                    30,	# int | float (numeric value between 10 and 50) in 'Number of frames' Slider component
                    6,	# int | float (numeric value between 1 and 20) in 'Guidance scale' Slider component
                    api_name="/predict"
                )
                # Result is usually a path to mp4
                video_file = result
                
            # LTX Logic
            elif "ltx" in self.model_name.lower():
                result = self.client.predict(
                    prompt,             # prompt
                    "worst quality, inconsistent motion, blurry, jittery, distorted", # negative_prompt
                    None,               # input_image_filepath
                    None,               # input_video_filepath
                    512,                # height_ui
                    704,                # width_ui
                    "text-to-video",    # mode
                    min(float(duration), 2.0), # duration_ui (Cap at 2s for free tier reliability)
                    9,                  # ui_frames_to_use
                    0,                  # seed_ui
                    True,               # randomize_seed
                    3,                  # ui_guidance_scale
                    True,               # improve_texture_flag
                    False,              # slow_motion_flag
                    api_name="/text_to_video"
                )
                # Result is ({'video': path, ...}, seed)
                if isinstance(result, tuple) and isinstance(result[0], dict):
                    video_file = result[0].get('video')
                else:
                    video_file = result
                
            # Zeroscope Logic
            elif "zeroscope" in self.model_name.lower():
                result = self.client.predict(
                    prompt,
                    "cerspense/zeroscope_v2_576w", # Model choice
                    api_name="/predict"
                )
                video_file = result
                
            # Modelscope / Damo Logic
            elif "modelscope" in self.model_name.lower() or "damo" in self.model_name.lower():
                result = self.client.predict(
                    prompt,
                    api_name="/predict"
                )
                video_file = result
            
            else:
                # Generic fallback
                try:
                    # Try with just prompt
                    result = self.client.predict(prompt, api_name="/predict")
                except:
                    # Try with prompt and seed
                    result = self.client.predict(prompt, 0, api_name="/predict")
                video_file = result

            if video_file and os.path.exists(video_file):
                # Move to output path
                import shutil
                shutil.move(video_file, output_path)
                logger.info(f"✓ AI video generated: {output_path}")
                return output_path
            else:
                logger.error("AI video generation returned invalid file")
                return None
                
        except Exception as e:
            logger.error(f"AI video generation failed: {e}")
            return None
    
    def _enhance_prompt(self, prompt: str) -> str:
        """
        Enhance prompt for better video generation.
        Add quality modifiers and style hints.
        """
        # Add quality modifiers
        quality_terms = "high quality, cinematic, professional, detailed"
        
        # Add camera movement for more dynamic videos
        camera_hints = "smooth camera movement"
        
        enhanced = f"{prompt}, {quality_terms}, {camera_hints}"
        
        return enhanced
    
    def _download_file(self, url: str, filepath: str):
        """Download file from URL."""
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)


class LumaGenerator:
    """
    Alternative: Luma Dream Machine (if available).
    Note: Luma may require API key or have limited free tier.
    """
    
    def __init__(self):
        self.enabled = False
        logger.info("Luma generator not implemented (requires API key)")
    
    def generate_video(self, prompt: str, output_path: str) -> str:
        """Placeholder for Luma integration."""
        return None


class AIVideoGenerator:
    """
    Unified interface for AI video generation.
    Tries multiple services in order of preference.
    """
    
    def __init__(self):
        self.generators = []
        
        # Initialize available generators
        mochi = MochiGenerator()
        if mochi.enabled:
            self.generators.append(('Mochi', mochi))
        
        # Could add more generators here
        # luma = LumaGenerator()
        # if luma.enabled:
        #     self.generators.append(('Luma', luma))
        
        if not self.generators:
            logger.warning("No AI video generators available")
    
    def generate_video(self, prompt: str, output_path: str, duration: int = 5) -> str:
        """
        Generate video using best available generator.
        
        Args:
            prompt: Text description
            output_path: Where to save video
            duration: Target duration in seconds
            
        Returns:
            Path to generated video, or None if all failed
        """
        for name, generator in self.generators:
            logger.info(f"Trying {name} for AI video generation...")
            result = generator.generate_video(prompt, output_path, duration)
            
            if result:
                logger.info(f"✓ {name} successfully generated video")
                return result
            else:
                logger.warning(f"{name} failed, trying next generator...")
        
        logger.error("All AI video generators failed")
        return None
    
    def is_available(self) -> bool:
        """Check if any AI video generator is available."""
        return len(self.generators) > 0


if __name__ == "__main__":
    # Test AI video generation
    gen = AIVideoGenerator()
    
    if gen.is_available():
        test_prompt = "A serene forest with sunlight filtering through trees"
        output = "test_ai_video.mp4"
        
        result = gen.generate_video(test_prompt, output)
        
        if result:
            print(f"✓ Video generated: {result}")
        else:
            print("✗ Video generation failed")
    else:
        print("No AI video generators available")
