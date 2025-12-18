import logging
import json
import google.generativeai as genai
from config.settings import Config
import time
import random

logger = logging.getLogger(__name__)

def retry_with_backoff(func, max_retries=5, initial_delay=5):
    for i in range(max_retries):
        try:
            return func()
        except Exception as e:
            if "429" in str(e) or "Quota exceeded" in str(e) or "Resource exhausted" in str(e):
                if i == max_retries - 1:
                    raise e
                delay = initial_delay * (2 ** i) + random.uniform(0, 1)
                logger.warning(f"Gemini quota exceeded. Retrying in {delay:.2f}s...")
                time.sleep(delay)
            else:
                raise e

class UnifiedContentGenerator:
    def __init__(self):
        if Config.GEMINI_API_KEY:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-flash-latest')
        else:
            logger.error("GEMINI_API_KEY is missing. Content generation will fail.")
            self.model = None

    def generate_full_content(self, niche, duration_type="short"):
        """
        Generates topic, title, script, and scene keywords in a SINGLE API call.
        """
        if not self.model:
            return None

        prompt = f"""
        You are a viral YouTube Shorts creator. Generate content for a video in the "{niche}" niche.
        
        Return a JSON object with the following fields:
        1. "topic": A viral topic name.
        2. "title": A short, clickbaity, ALL CAPS title (max 6 words).
        3. "script": A highly engaging spoken script (180-200 words). No scene directions.
        4. "scenes": A list of objects, each with:
           - "text": The specific part of the script for this scene.
           - "keywords": 3 highly specific visual search terms for stock footage.
        
        Rules for "{niche}":
        - If horror: Eerie, suspenseful, fast-paced.
        - If history: Educational but dramatic.
        - If scp: Clinical but unsettling.
        - If life_advice: Direct, empowering.
        - If news: Urgent, breaking news style.
        
        The script should be divided into 6-8 logical scenes.
        
        Return ONLY the JSON object.
        """

        try:
            response = retry_with_backoff(lambda: self.model.generate_content(prompt))
            text = response.text.strip()
            
            # Extract JSON
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            data = json.loads(text)
            logger.info(f"Successfully generated unified content for {niche}")
            return data
        except Exception as e:
            logger.error(f"Unified content generation failed: {e}")
            return None

    def generate_content_from_topic(self, topic, niche, duration_type="short"):
        """
        Generates title, script, and scene keywords for a GIVEN topic in a SINGLE API call.
        """
        if not self.model:
            return None

        prompt = f"""
        You are a viral YouTube Shorts creator. Generate content for a video about "{topic}" in the "{niche}" niche.
        
        Return a JSON object with the following fields:
        1. "title": A short, clickbaity, ALL CAPS title (max 6 words).
        2. "script": A highly engaging spoken script (180-200 words). No scene directions.
        3. "scenes": A list of objects, each with:
           - "text": The specific part of the script for this scene.
           - "keywords": 3 highly specific visual search terms for stock footage.
        
        Rules:
        - The script should be divided into 6-8 logical scenes.
        - Return ONLY the JSON object.
        """

        try:
            response = retry_with_backoff(lambda: self.model.generate_content(prompt))
            text = response.text.strip()
            
            # Extract JSON
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
            
            data = json.loads(text)
            data["topic"] = topic
            logger.info(f"Successfully generated content for topic: {topic}")
            return data
        except Exception as e:
            logger.error(f"Content generation from topic failed: {e}")
            return None
