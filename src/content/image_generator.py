import logging
import os
import requests
import google.generativeai as genai
from config.settings import Config

logger = logging.getLogger(__name__)

class ImageGenerator:
    """
    Generates AI images using Gemini Imagen when stock footage is unavailable.
    """
    def __init__(self):
        if Config.GEMINI_API_KEY:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            logger.error("GEMINI_API_KEY is missing. Image generation will fail.")
            self.model = None
    
    def generate_image(self, prompt, niche, output_path):
        """
        Generate an image based on prompt and niche.
        For now, we'll use a placeholder approach since Gemini Imagen API
        access is limited. In production, you'd use:
        - Gemini Imagen API
        - Stable Diffusion API
        - DALL-E API
        
        For this implementation, we'll generate a solid color background
        with text overlay as a fallback.
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Niche-specific color schemes
            colors = {
                "horror": (20, 20, 30),  # Very dark blue-black
                "horror_stories": (30, 15, 15),  # Dark red-black
                "history": (80, 70, 50),  # Sepia brown
                "scp": (15, 25, 35),  # Dark blue
                "life_advice": (240, 235, 220),  # Warm beige
                "news": (30, 40, 60),  # News blue
                "general": (40, 40, 50)  # Neutral gray
            }
            
            bg_color = colors.get(niche, colors["general"])
            
            # Create 1080x1920 image (vertical)
            img = Image.new('RGB', (1080, 1920), color=bg_color)
            draw = ImageDraw.Draw(img)
            
            # Add subtle gradient
            for y in range(1920):
                alpha = y / 1920
                gradient_color = tuple(int(c * (1 - alpha * 0.3)) for c in bg_color)
                draw.line([(0, y), (1080, y)], fill=gradient_color)
            
            # Add text overlay (optional, for debugging)
            # In production, this would be the AI-generated image
            
            img.save(output_path, quality=95)
            logger.info(f"Generated placeholder image: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            return None
    
    def create_images_for_script(self, script, niche, count=3):
        """
        Generate multiple images based on script content.
        Returns list of image paths.
        """
        images = []
        
        for i in range(count):
            output_path = os.path.join(Config.ASSETS_DIR, f"ai_image_{i}.jpg")
            
            # Generate simple prompt from script
            prompt = f"{niche} themed image, cinematic, dark, atmospheric"
            
            image_path = self.generate_image(prompt, niche, output_path)
            if image_path:
                images.append(image_path)
        
        return images
