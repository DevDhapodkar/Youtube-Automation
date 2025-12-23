import logging
import os
import requests
import time
import random
from config.settings import Config

logger = logging.getLogger(__name__)

class ImageGenerator:
    """
    Generates AI images using Pollinations.ai (Free, no key) or Google Gemini (Fallback).
    """
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY", "")
        self.use_pollinations = True
        
        if self.api_key:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai
        else:
            self.client = None
    
    def generate_image(self, prompt, niche, output_path, width=1080, height=1920):
        """
        Generate an image using Pollinations.ai (primary) or Gemini (fallback).
        """
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
        
        # Try Pollinations first (Free, no credit card)
        if self.use_pollinations:
            try:
                return self._generate_pollinations(full_prompt, output_path, width, height)
            except Exception as e:
                logger.warning(f"Pollinations generation failed: {e}. Trying fallback...")
        
        # Fallback to Gemini if available
        if self.client:
            try:
                return self._generate_gemini(full_prompt, output_path)
            except Exception as e:
                logger.error(f"Gemini generation failed: {e}")
        
        # Final fallback
        return self._generate_placeholder(niche, output_path)

    def _generate_pollinations(self, prompt, output_path, width=1080, height=1920):
        """
        Generate image using Pollinations.ai API.
        URL format: https://pollinations.ai/p/{prompt}?width={width}&height={height}&seed={seed}
        """
        logger.info(f"Generating AI image with Pollinations.ai: {prompt[:100]}... ({width}x{height})")
        
        # URL encode the prompt
        import urllib.parse
        encoded_prompt = urllib.parse.quote(prompt)
        
        seed = random.randint(0, 1000000)
        
        url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&seed={seed}&model=flux"
        
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                f.write(response.content)
            logger.info(f"Pollinations image saved to: {output_path}")
            return output_path
        else:
            raise Exception(f"Pollinations API returned status {response.status_code}")

    def _generate_gemini(self, prompt, output_path):
        """
        Generate image using Google Gemini (Imagen 3).
        """
        logger.info(f"Generating AI image with Gemini: {prompt[:100]}...")
        
        try:
            model = self.client.ImageGenerationModel("imagen-3.0-generate-001")
            response = model.generate_images(
                prompt=prompt,
                number_of_images=1,
                aspect_ratio="9:16",
                safety_filter_level="block_some",
                person_generation="allow_adult"
            )
            
            if response and response.images:
                image = response.images[0]
                image.save(output_path)
                logger.info(f"Gemini image generated: {output_path}")
                return output_path
            else:
                raise Exception("No images returned from Gemini")
                
        except (AttributeError, Exception) as e:
            logger.warning(f"Gemini SDK failed ({e}), trying REST fallback...")
            return self._generate_gemini_rest(prompt, output_path)

    def _generate_gemini_rest(self, prompt, output_path):
        """
        Fallback: Generate image using Gemini API via REST.
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "instances": [{"prompt": prompt}],
            "parameters": {"sampleCount": 1, "aspectRatio": "9:16"}
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            result = response.json()
            if 'predictions' in result and result['predictions']:
                prediction = result['predictions'][0]
                import base64
                image_data = base64.b64decode(prediction['bytesBase64Encoded'])
                with open(output_path, 'wb') as f:
                    f.write(image_data)
                return output_path
        raise Exception(f"Gemini REST API failed: {response.text}")

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
        words = script.split()
        
        # Create prompts based on segments of the script
        segment_len = len(words) // count
        prompts = []
        
        for i in range(count):
            start = i * segment_len
            end = start + 20 # Take 20 words
            segment = " ".join(words[start:end])
            prompts.append(segment)
            
        for i, prompt in enumerate(prompts):
            output_path = os.path.join(Config.ASSETS_DIR, f"ai_image_{int(time.time())}_{i}.jpg")
            if not os.path.exists(Config.ASSETS_DIR):
                os.makedirs(Config.ASSETS_DIR)
                
            image_path = self.generate_image(prompt, niche, output_path)
            if image_path:
                images.append(image_path)
        
        return images

if __name__ == "__main__":
    # Test
    gen = ImageGenerator()
    gen.generate_image("A futuristic city with flying cars", "general", "test_image.jpg")


