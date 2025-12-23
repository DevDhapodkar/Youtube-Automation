import logging
import os
import requests
import json
import random
from PIL import Image, ImageDraw, ImageFont
from config.settings import Config
import google.generativeai as genai
from gradio_client import Client, handle_file

logger = logging.getLogger(__name__)

class ThumbnailGenerator:
    def __init__(self):
        self.api_key = Config.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-flash-latest')
        else:
            logger.error("GEMINI_API_KEY is missing. Thumbnail concept generation will fail.")
            self.model = None

    def generate_thumbnail(self, topic, niche, viral_title):
        """
        Generates a high-quality clickbait thumbnail.
        Returns the path to the generated thumbnail.
        """
        logger.info(f"Generating thumbnail for: {topic}")
        
        # 1. Get Concept & Text from Gemini
        concept = self._get_thumbnail_concept(topic, niche, viral_title)
        if not concept:
            return None
            
        visual_prompt = concept.get("visual_prompt")
        overlay_text = concept.get("overlay_text")
        
        # 2. Generate Base Image
        # 2. Generate Base Image
        image_path = os.path.join(Config.ASSETS_DIR, f"thumb_{int(random.random()*10000)}.jpg")
        
        success = self._generate_base_image(visual_prompt, image_path)
        if not success:
            logger.warning("Base image generation failed. Using fallback.")
            self._generate_fallback_image(image_path)
            
        # 3. Add Text Overlay
        # Always try to add text, even on fallback
        final_path = self._add_text_overlay(image_path, overlay_text)
        
        return final_path

    def _get_thumbnail_concept(self, topic, niche, viral_title):
        """
        Uses Gemini to create a visual prompt and catchy overlay text.
        """
        if not self.model:
            return None
            
        prompt = f"""
        You are a YouTube Thumbnail expert. Create a concept for a CLICKBAIT thumbnail for a video about "{topic}" (Title: "{viral_title}").
        
        Niche: {niche}
        
        Return a JSON object with:
        1. "visual_prompt": A highly descriptive image generation prompt for Pollinations.ai. 
           - Aspect Ratio: 16:9.
           - Style: High contrast, 4k, hyper-realistic, vibrant colors, expressive faces (if any), dramatic lighting.
           - Content: Something shocking, mysterious, or visually striking related to the topic.
        2. "overlay_text": Short, punchy text to put on the thumbnail (Max 3-4 words).
           - Examples: "THE TRUTH", "DON'T WATCH", "SECRET REVEALED", "IMPOSSIBLE?".
           - MUST be different from the video title.
        
        Return ONLY the JSON.
        """
        
        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
                
            return json.loads(text)
        except Exception as e:
            logger.error(f"Thumbnail concept generation failed: {e}")
            return None

    def _generate_base_image(self, prompt, output_path):
        """
        Generates 16:9 image using Pollinations.ai with retries.
        """
        logger.info(f"Generating thumbnail base image: {prompt[:50]}...")
        
        import urllib.parse
        import time
        encoded_prompt = urllib.parse.quote(prompt)
        
        # 1280x720 is standard HD thumbnail size
        width = 1280
        height = 720
        
        max_retries = 3
        for attempt in range(max_retries):
            seed = random.randint(0, 1000000)
            url = f"https://pollinations.ai/p/{encoded_prompt}?width={width}&height={height}&seed={seed}&model=flux"
            
            try:
                logger.info(f"Pollinations attempt {attempt+1}/{max_retries}")
                response = requests.get(url, timeout=30) # Reduced timeout for faster failover
                if response.status_code == 200:
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    return True
                else:
                    logger.warning(f"Pollinations failed with status {response.status_code}")
            except Exception as e:
                logger.warning(f"Image generation attempt {attempt+1} failed: {e}")
            
            # Wait before retry
            if attempt < max_retries - 1:
                time.sleep(2)
                
        logger.warning("Pollinations failed. Trying Hugging Face Fallback (FLUX.1)...")
        
        # Fallback 1: Hugging Face (High Quality)
        if self._generate_with_hf_gradio(prompt, output_path):
            return True
            
        logger.error("All high-quality image generation attempts failed.")
        return False

    def _generate_with_hf_gradio(self, prompt, output_path):
        """
        Generates image using FLUX.1-schnell via Hugging Face Spaces.
        """
        try:
            logger.info(f"Generating fallback image with FLUX.1 for: {prompt[:50]}...")
            client = Client("black-forest-labs/FLUX.1-schnell")
            
            result = client.predict(
                prompt=prompt,
                seed=0,
                randomize_seed=True,
                width=1280,
                height=720,
                num_inference_steps=4,
                api_name="/predict"
            )
            
            # Result is usually a tuple or path, depending on the space
            # For FLUX.1-schnell, it returns a tuple with path at index 0
            image_path = result[0] if isinstance(result, tuple) else result
            
            if image_path and os.path.exists(image_path):
                import shutil
                shutil.move(image_path, output_path)
                logger.info(f"✓ FLUX.1 image generated: {output_path}")
                return True
            else:
                logger.error("FLUX.1 returned invalid result")
                return False
                
        except Exception as e:
            logger.error(f"HF Gradio generation failed: {e}")
            return False

    def _generate_fallback_image(self, output_path):
        """
        Generates a simple dark background for fallback.
        """
        logger.info("Generating fallback thumbnail background...")
        try:
            # Create a dark red/black gradient-ish solid color
            # 1280x720
            width = 1280
            height = 720
            
            # Dark red background
            color = (20, 0, 0) 
            img = Image.new('RGB', (width, height), color)
            
            # Add some noise or simple pattern if possible, but solid is fine for robustness
            draw = ImageDraw.Draw(img)
            
            # Draw a slightly lighter rectangle in the center for interest
            draw.rectangle([100, 100, width-100, height-100], outline=(50, 0, 0), width=5)
            
            img.save(output_path)
            return True
        except Exception as e:
            logger.error(f"Fallback generation failed: {e}")
            # Last resort: Create a tiny black image
            try:
                img = Image.new('RGB', (1280, 720), (0, 0, 0))
                img.save(output_path)
                return True
            except:
                return False

    def _add_text_overlay(self, image_path, text):
        """
        Adds bold, high-contrast text to the thumbnail.
        """
        try:
            img = Image.open(image_path)
            draw = ImageDraw.Draw(img)
            
            # Try to load a bold font
            # Cross-platform common paths
            font_paths = [
                # Windows
                "C:\\Windows\\Fonts\\impact.ttf",
                "C:\\Windows\\Fonts\\arialbd.ttf",
                "C:\\Windows\\Fonts\\seguiemj.ttf",
                # MacOS
                "/System/Library/Fonts/Supplemental/Impact.ttf",
                "/System/Library/Fonts/HelveticaNeue-CondensedBlack.otf",
                "/System/Library/Fonts/Helvetica.ttc",
                "/Library/Fonts/Arial Black.ttf",
                # Linux
                "/usr/share/fonts/truetype/msttcorefonts/Impact.ttf",
                "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
                "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
            ]
            
            font = None
            for path in font_paths:
                if os.path.exists(path):
                    try:
                        font = ImageFont.truetype(path, 100) # Large font size
                        break
                    except:
                        continue
            
            if not font:
                logger.warning("No custom font found, using default.")
                font = ImageFont.load_default()

            # Calculate text size and position (centered, slightly lower)
            # Pillow 10+ uses textbbox
            try:
                left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
                text_width = right - left
                text_height = bottom - top
            except AttributeError:
                # Older Pillow
                text_width, text_height = draw.textsize(text, font=font)

            x = (img.width - text_width) / 2
            y = (img.height - text_height) / 2 + 100 # Slightly lower than center
            
            # Draw outline/stroke for contrast
            stroke_width = 6
            stroke_color = "black"
            
            # Draw text with stroke
            draw.text((x, y), text, font=font, fill="white", stroke_width=stroke_width, stroke_fill=stroke_color)
            
            # Save
            final_path = image_path.replace(".jpg", "_thumb.jpg")
            img.save(final_path, quality=95)
            logger.info(f"Thumbnail created: {final_path}")
            
            return final_path
            
        except Exception as e:
            logger.error(f"Text overlay failed: {e}")
            return image_path # Return base image if overlay fails
