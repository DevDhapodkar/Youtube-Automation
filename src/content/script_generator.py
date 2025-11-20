import logging
import google.generativeai as genai
from config.settings import Config

logger = logging.getLogger(__name__)

class ScriptGenerator:
    def __init__(self):
        if Config.GEMINI_API_KEY:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            logger.error("GEMINI_API_KEY is missing. Script generation will fail.")
            self.model = None

    def generate_script(self, topic, duration_type="short"):
        """
        Generates a script for a YouTube video.
        duration_type: 'short' (60s) or 'long' (5-10 mins)
        """
        if not self.model:
            return "Error: No API Key"

        logger.info(f"Generating script for topic: {topic} ({duration_type})")
        
        if duration_type == "short":
            prompt = f"""
            Write a highly engaging, viral YouTube Short script about "{topic}".
            The script must be exactly 130-150 words long (perfect for 60 seconds).
            
            Structure:
            1. Hook (0-3s): Grab attention immediately.
            2. Body: Deliver value/facts quickly.
            3. CTA: Ask to subscribe.
            
            Output ONLY the spoken text. Do not include scene directions or timestamps.
            """
        else:
            prompt = f"""
            Write a detailed, engaging YouTube video script about "{topic}".
            Target length: 5 minutes.
            Include an intro, 3 main points, and a conclusion.
            Output ONLY the spoken text.
            """

        try:
            response = self.model.generate_content(prompt)
            script = response.text
            logger.info("Script generated successfully.")
            return script
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            return f"Welcome to our channel. Today we talk about {topic}. Please subscribe."

if __name__ == "__main__":
    gen = ScriptGenerator()
    print(gen.generate_script("The History of Coffee"))
