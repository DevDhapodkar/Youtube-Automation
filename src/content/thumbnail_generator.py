import logging
from PIL import Image, ImageDraw, ImageFont
import os
import random
from config.settings import Config

logger = logging.getLogger(__name__)

class ThumbnailGenerator:
    def __init__(self):
        self.font_path = "/System/Library/Fonts/Helvetica.ttc" # Mac default
        # Fallback or download a font if needed

    def create_thumbnail(self, title, background_image_path=None, output_path="thumbnail.jpg"):
        """
        Create a thumbnail with text overlay.
        """
        logger.info(f"Creating thumbnail for: {title}")
        
        width, height = 1280, 720
        
        if background_image_path and os.path.exists(background_image_path):
            img = Image.open(background_image_path)
            img = img.resize((width, height))
        else:
            # Create a random solid color background
            color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            img = Image.new('RGB', (width, height), color=color)

        draw = ImageDraw.Draw(img)
        
        # Load font
        try:
            font = ImageFont.truetype(self.font_path, 80)
        except:
            font = ImageFont.load_default()

        # Text wrapping (simple)
        words = title.split()
        lines = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(" ".join(current_line)) > 15: # Arbitrary char limit
                lines.append(" ".join(current_line))
                current_line = []
        if current_line:
            lines.append(" ".join(current_line))

        # Draw text centered
        y_text = height / 2 - (len(lines) * 40)
        for line in lines:
            # Get text bbox
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x_text = (width - text_width) / 2
            
            # Draw shadow/outline
            shadow_color = "black"
            offset = 3
            draw.text((x_text+offset, y_text+offset), line, font=font, fill=shadow_color)
            
            # Draw text
            draw.text((x_text, y_text), line, font=font, fill="white")
            y_text += text_height + 10

        img.save(output_path)
        logger.info(f"Thumbnail saved to {output_path}")
        return output_path

if __name__ == "__main__":
    gen = ThumbnailGenerator()
    gen.create_thumbnail("AMAZING AI FACTS")
