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
            self.client = Client("genmo/mochi-1-preview")
            logger.info("Mochi generator initialized")
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
        """
        if not self.enabled:
            logger.warning("Mochi generator is disabled")
            return None
        
        try:
            logger.info(f"Generating AI video with Mochi: '{prompt[:50]}...'")
            
            # Enhance prompt for better results
            enhanced_prompt = self._enhance_prompt(prompt)
            
            # Generate video
            result = self.client.predict(
                prompt=enhanced_prompt,
                negative_prompt="blurry, low quality, distorted, watermark, text",
                num_inference_steps=50,
                guidance_scale=7.5,
                api_name="/generate"
            )
            
            # result is typically a file path or URL
            if isinstance(result, str):
                # Download if it's a URL
                if result.startswith('http'):
                    self._download_file(result, output_path)
                else:
                    # It's a local file path
                    import shutil
                    shutil.copy(result, output_path)
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.info(f"✓ Mochi video generated: {output_path}")
                    return output_path
                else:
                    logger.error("Mochi generated empty file")
                    return None
            else:
                logger.error(f"Unexpected Mochi result type: {type(result)}")
                return None
                
        except Exception as e:
            logger.error(f"Mochi video generation failed: {e}")
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
