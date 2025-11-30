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
        self.api_key = os.getenv("GOOGLE_API_KEY", "")
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not set. Image generation will fail.")
        
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        self.client = genai
    
    def generate_image(self, prompt, niche, output_path):
        """
        Generate an image using Google Gemini (Imagen 3).
        """
        if not self.api_key:
            logger.warning("GOOGLE_API_KEY not set. Using fallback placeholder images.")
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
            
            logger.info(f"Generating AI image with Gemini: {full_prompt[:100]}...")
            
            # Use Imagen 3 model
            # Note: The exact model name might vary, 'imagen-3.0-generate-001' is a placeholder for the latest available
            # If the specific model isn't available, we might need to handle that.
            # For now, we'll try to use the 'imagen-3.0-generate-001' model.
            
            # Since the python SDK for Imagen might be different or in preview, 
            # we will use the standard model.generate_images if available, or fallback to REST if needed.
            # Assuming the standard SDK supports it now.
            
            try:
                # Attempt to use the latest Imagen model
                model = self.client.ImageGenerationModel("imagen-3.0-generate-001")
                response = model.generate_images(
                    prompt=full_prompt,
                    number_of_images=1,
                    aspect_ratio="9:16", # Vertical for Shorts
                    safety_filter_level="block_some",
                    person_generation="allow_adult"
                )
                
                if response and response.images:
                    image = response.images[0]
                    image.save(output_path)
                    logger.info(f"AI image generated: {output_path}")
                    return output_path
                else:
                    logger.error("No images returned from Gemini")
                    return self._generate_placeholder(niche, output_path)

            except (AttributeError, Exception) as e:
                logger.warning(f"SDK generation failed ({e}), trying REST API fallback...")
                return self._generate_image_rest(full_prompt, niche, output_path)
                
        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return self._generate_placeholder(niche, output_path)

    def _generate_image_rest(self, prompt, niche, output_path):
        """
        Fallback: Generate image using Gemini API via REST (Imagen 3).
        """
        try:
            # Endpoint for Imagen 3
            url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-001:predict?key={self.api_key}"
            
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "instances": [
                    {
                        "prompt": prompt
                    }
                ],
                "parameters": {
                    "sampleCount": 1,
                    "aspectRatio": "9:16"
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                # Parse response - format might vary, usually predictions[0].bytesBase64Encoded or similar
                # For Imagen on Vertex it's bytesBase64Encoded, for Gemini API it might be similar
                
                if 'predictions' in result and len(result['predictions']) > 0:
                    prediction = result['predictions'][0]
                    
                    import base64
                    
                    # Check for bytesBase64Encoded
                    if 'bytesBase64Encoded' in prediction:
                        image_data = base64.b64decode(prediction['bytesBase64Encoded'])
                    elif 'mimeType' in prediction and 'bytesBase64Encoded' in prediction: # Another possible format
                         image_data = base64.b64decode(prediction['bytesBase64Encoded'])
                    else:
                        logger.error(f"Unknown response format: {result}")
                        return self._generate_placeholder(niche, output_path)
                        
                    with open(output_path, 'wb') as f:
                        f.write(image_data)
                        
                    logger.info(f"AI image generated via REST: {output_path}")
                    return output_path
                else:
                    logger.error(f"No predictions in response: {result}")
                    return self._generate_placeholder(niche, output_path)
            else:
                logger.error(f"REST API failed: {response.status_code} - {response.text}")
                return self._generate_placeholder(niche, output_path)
                
        except Exception as e:
            logger.error(f"REST generation error: {e}")
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

