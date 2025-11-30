import logging
import os
import requests
from config.settings import Config

logger = logging.getLogger(__name__)

class ImageGenerator:
    """
    Generates AI images using Hugging Face Stable Diffusion API.
    """
    def __init__(self):
        self.api_key = os.getenv("HUGGINGFACE_API_KEY", "")
        # Using Stable Diffusion XL for high quality
        self.api_url = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
    
    def generate_image(self, prompt, niche, output_path):
        """
        Generate an image using Hugging Face Stable Diffusion.
        """
        if not self.api_key:
            logger.warning("HUGGINGFACE_API_KEY not set. Using fallback placeholder images.")
            return self._generate_placeholder(niche, output_path)
        
        try:
            # Enhance prompt based on niche
            style_prompts = {
                "horror": "dark horror, eerie atmosphere, cinematic lighting, unsettling, 4k, photorealistic",
                "horror_stories": "creepy abandoned place, dark shadows, suspenseful mood, cinematic, ultra detailed",
                "history": "historical scene, vintage photograph style, sepia tone, ancient, detailed, 8k",
                "scp": "SCP foundation, laboratory, containment chamber, clinical, ominous, high detail",
                "life_advice": "motivational, inspiring scene, warm lighting, professional, clean aesthetic",
                "news": "modern newsroom, professional, high tech, clean, 4k",
                "general": "cinematic, professional, high quality, detailed, 4k"
            }
            
            style = style_prompts.get(niche, style_prompts["general"])
            full_prompt = f"{prompt}, {style}"
            
            headers = {"Authorization": f"Bearer {self.api_key}"}
            payload = {"inputs": full_prompt}
            
            logger.info(f"Generating AI image with prompt: {full_prompt[:100]}...")
            
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                logger.info(f"AI image generated: {output_path}")
                return output_path
            else:
                logger.error(f"Image generation failed: {response.status_code} - {response.text}")
                return self._generate_placeholder(niche, output_path)
                
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return self._generate_placeholder(niche, output_path)
    
    def _generate_placeholder(self, niche, output_path):
        """Fallback: Generate simple gradient placeholder"""
        try:
            from PIL import Image, ImageDraw
            
            colors = {
                "horror": (20, 20, 30),
                "horror_stories": (30, 15, 15),
                "history": (80, 70, 50),
                "scp": (15, 25, 35),
                "life_advice": (240, 235, 220),
                "news": (30, 40, 60),
                "general": (40, 40, 50)
            }
            
            bg_color = colors.get(niche, colors["general"])
            img = Image.new('RGB', (1080, 1920), color=bg_color)
            draw = ImageDraw.Draw(img)
            
            # Add gradient
            for y in range(1920):
                alpha = y / 1920
                gradient_color = tuple(int(c * (1 - alpha * 0.3)) for c in bg_color)
                draw.line([(0, y), (1080, y)], fill=gradient_color)
            
            img.save(output_path, quality=95)
            logger.info(f"Generated placeholder image: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Placeholder generation failed: {e}")
            return None
    
    def create_images_for_script(self, script, niche, count=3):
        """
        Generate multiple images based on script content.
        """
        images = []
        
        # Extract key phrases from script for prompts
        words = script.split()
        mid_point = len(words) // 2
        
        prompts = [
            " ".join(words[:15]),  # Beginning
            " ".join(words[mid_point:mid_point+15]),  # Middle
            " ".join(words[-15:])  # End
        ]
        
        for i in range(min(count, len(prompts))):
            output_path = os.path.join(Config.ASSETS_DIR, f"ai_image_{i}.jpg")
            
            image_path = self.generate_image(prompts[i], niche, output_path)
            if image_path:
                images.append(image_path)
        
        return images

