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

    def generate_full_content(self, niche, duration_type="short", duration_minutes=None):
        """
        Generates topic, title, script, and scene keywords in a SINGLE API call.
        """
        if not self.model:
            return None

        is_long = duration_type == "long"
        
        if duration_minutes:
            # Dynamic calculation based on requested duration
            words_per_minute = 150
            scenes_per_minute = 10 # Fast pacing
            
            target_words = int(duration_minutes * words_per_minute)
            target_scenes = int(duration_minutes * scenes_per_minute)
            
            script_length = f"{target_words}-{target_words + 50}"
            scene_count = f"{target_scenes}-{target_scenes + 5}"
            video_type = f"Video ({duration_minutes} mins)"
        else:
            # Fallback defaults
            script_length = "1500-2000" if is_long else "180-200"
            scene_count = "15-20" if is_long else "6-8"
            video_type = "Full Length Video (5-10 mins)" if is_long else "YouTube Short (60s)"

        prompt = f"""
        You are a viral YouTube creator. Generate content for a {video_type} in the "{niche}" niche.
        
        GOAL: Maximize Audience Retention, Revenue (High CPM), and Subscriber Growth for the US Market.
        
        CONSTRAINTS:
        - Total Script Length: ~{script_length} words.
        - Total Scene Count: Exactly {scene_count} scenes.
        
        TONE & STYLE: 
        - Use American English and US-centric cultural references.
        - Be aggressive, high-energy, and professional.
        - Use "Curiosity Gaps" to keep viewers engaged.
        - The goal is to make the video go viral in the United States and earn maximum ad revenue.
        
        Return a JSON object with the following fields:
        1. "topic": A viral topic name.
        2. "title": A short, clickbaity, ALL CAPS title (max 6 words).
        3. "script": The full spoken script for the video.
        4. "scenes": A list of {scene_count} objects, each with:
           - "text": The spoken text for this scene (part of the script).
           - "sfx": A short description of a contextual sound effect for this scene if needed (e.g., "dramatic jumpscare", "violent knocking", "heavy thunder", "footsteps on gravel"). Leave as null if no specific SFX is needed.
           - "keywords": A JSON LIST of 3 highly specific, descriptive visual search terms for Pexels stock footage.
             (e.g., ["ancient rusted hunting cabin in deep woods", "cinematic close up of old keys", ...])
             CRITICAL: Keywords must be long and descriptive (>4 words) to ensure high quality visuals.
             DO NOT use generic words. Each keyword must be a full descriptive phrase.
        5. "description": A high-retention, SEO-optimized YouTube description (US Market focus). Include a powerful hook, a brief summary of the video, and a strong Call to Action (CTA) to subscribe. Use relevant keywords naturally.
        6. "tags": A list of 15-20 high-CPM, high-volume hashtags and keywords for YouTube SEO (US Market). Include broad, niche-specific, and trending tags to maximize reach.
        
        Rules for "{niche}":
        - CRITICAL: The first 5-10 seconds (Scene 1) MUST be an attention-grabbing "HOOK". It should create curiosity, ask a shocking question, or show a mind-blowing fact so the user doesn't scroll away.
        - RETENTION: Use "Open Loops" - raise questions early and answer them late. Keep the pacing fast.
        - MONETIZATION: Include a subtle but clear "Subscribe for more wealth/knowledge" Call to Action in the middle or end.
        - LOCALE: Use American spelling (e.g., "color" not "colour") and US-centric examples/slang where appropriate.
        - If horror: Eerie, suspenseful, fast-paced, high stakes.
        - If history: Educational, dramatic, focusing on "untold stories" or "secret facts".
        - If scp: Clinical but unsettling, emphasizing the "secret government agency" vibe.
        - If life_advice: Direct, empowering, actionable, high status.
        - If news: Urgent, breaking news style, high impact.
        - If finance/tech: Professional, authoritative, focusing on "wealth creation", "future tech", and "insider info" (High CPM).
        - If luxury: Aspirational, premium, focusing on "exclusivity" and "high net worth" lifestyle.
        
        The script should be divided into {scene_count} logical scenes.
        
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
            logger.info(f"Successfully generated unified content for {niche} ({duration_type})")
            return data
        except Exception as e:
            logger.error(f"Unified content generation failed: {e}")
            return None

    def generate_content_from_topic(self, topic, niche, duration_type="short", duration_minutes=None):
        """
        Generates title, script, and scene keywords for a GIVEN topic in a SINGLE API call.
        """
        if not self.model:
            return None

        is_long = duration_type == "long"
        
        if duration_minutes:
            # Dynamic calculation based on requested duration
            words_per_minute = 150
            scenes_per_minute = 10 # Fast pacing
            
            target_words = int(duration_minutes * words_per_minute)
            target_scenes = int(duration_minutes * scenes_per_minute)
            
            script_length = f"{target_words}-{target_words + 50}"
            scene_count = f"{target_scenes}-{target_scenes + 5}"
            video_type = f"Video ({duration_minutes} mins)"
        else:
            # Fallback defaults
            script_length = "1500-2000" if is_long else "180-200"
            scene_count = "15-20" if is_long else "6-8"
            video_type = "Full Length Video (5-10 mins)" if is_long else "YouTube Short (60s)"

        prompt = f"""
        You are a viral YouTube creator. Generate content for a {video_type} about "{topic}" in the "{niche}" niche.
        
        GOAL: Maximize Audience Retention, Revenue (High CPM), and Subscriber Growth for the US Market.
        
        CONSTRAINTS:
        - Total Script Length: ~{script_length} words.
        - Total Scene Count: Exactly {scene_count} scenes.
        
        Return a JSON object with the following fields:
        1. "title": A short, clickbaity, ALL CAPS title (max 6 words).
        2. "script": The full spoken script for the video.
        3. "scenes": A list of {scene_count} objects, each with:
           - "text": The spoken text for this scene (part of the script).
           - "sfx": A short description of a contextual sound effect for this scene if needed (e.g., "dramatic jumpscare", "violent knocking", "heavy thunder", "footsteps on gravel"). Leave as null if no specific SFX is needed.
           - "keywords": A JSON LIST of 3 highly specific, descriptive visual search terms for Pexels stock footage.
             (e.g., ["dark eerie misty pine forest at night", "cinematic shot of wolf eyes", ...])
             CRITICAL: Keywords must be long and descriptive (>4 words) to ensure high quality visuals.
             DO NOT use generic words. Each keyword must be a full descriptive phrase.
        4. "description": A high-retention, SEO-optimized YouTube description. Include a hook, a brief summary of the video, and a Call to Action (CTA) to subscribe.
        5. "tags": A list of 10-15 high-CPM, relevant hashtags and keywords for YouTube SEO. Include both broad and niche-specific tags.
        
        Rules:
        - CRITICAL: The first 5-10 seconds (Scene 1) MUST be an attention-grabbing "HOOK". It should create curiosity, ask a shocking question, or show a mind-blowing fact so the user doesn't scroll away.
        - RETENTION: Use "Open Loops" - raise questions early and answer them late. Keep the pacing fast.
        - MONETIZATION: Include a subtle but clear "Subscribe for more wealth/knowledge" Call to Action in the middle or end.
        - The script should be divided into {scene_count} logical scenes.
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
            logger.info(f"Successfully generated content for topic: {topic} ({duration_type})")
            return data
        except Exception as e:
            logger.error(f"Content generation from topic failed: {e}")
            return None
