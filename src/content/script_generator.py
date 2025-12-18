import logging
import google.generativeai as genai
from config.settings import Config

logger = logging.getLogger(__name__)

from enum import Enum

class Niche(str, Enum):
    GENERAL = "general"
    HORROR = "horror"
    HORROR_STORIES = "horror_stories"
    HISTORY = "history"
    SCP = "scp"
    LIFE_ADVICE = "life_advice"
    NEWS = "news"
    TRENDING = "trending"

class ScriptGenerator:
    def __init__(self):
        if Config.GEMINI_API_KEY:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-flash-latest')
        else:
            logger.error("GEMINI_API_KEY is missing. Script generation will fail.")
            self.model = None

    def generate_script(self, topic, niche=Niche.GENERAL, duration_type="short"):
        """
        Generates a script for a YouTube video.
        duration_type: 'short' (60s) or 'long' (5-10 mins)
        """
        if not self.model:
            return "Error: No API Key"

        logger.info(f"Generating script for topic: {topic} ({niche}, {duration_type})")
        
        # Base instructions for Shorts
        base_short = """
        Write a highly engaging, viral YouTube Short script.
        The script must be exactly 180-200 words long (perfect for 60 seconds).
        Output ONLY the spoken text. Do not include scene directions or timestamps.
        Make it COMPLETE - with a clear beginning, middle, and satisfying ending.
        """
        
        # Niche-specific prompts
        if niche == Niche.HORROR:
            prompt = f"""
            {base_short}
            Topic: {topic} (Horror/Scary Story)
            Style: Eerie, suspenseful, fast-paced.
            Structure:
            1. Hook (0-8s): Start with a terrifying fact or shocking question that forces the viewer to stay.
            2. Body: Tell a mini-horror story or creepy fact. Build tension.
            3. Climax/CTA: A shocking twist or "Subscribe for more nightmares".
            """
        elif niche == Niche.HORROR_STORIES:
            prompt = f"""
            {base_short}
            Topic: {topic} (Horror Story Premise)
            Style: Narrative, suspenseful, cinematic. First-person or third-person storytelling.
            Structure:
            1. Hook (0-8s): Set the eerie scene immediately with a curiosity gap. "I was working the night shift when I saw something that shouldn't exist..."
            2. Body: Build suspense with creepy details. Something is wrong. Tension escalates.
            3. Climax: The terrifying reveal or cliffhanger. "That's when I realized..." Leave them wanting more.
            
            Make it feel like a real person's terrifying experience. Use vivid, unsettling details.
            """
        elif niche == Niche.HISTORY:
            prompt = f"""
            {base_short}
            Topic: {topic} (History)
            Style: Educational but dramatic, "Did you know?" style.
            Structure:
            1. Hook (0-8s): "You won't believe this about [Historical Figure/Event]..." or "The dark secret history doesn't want you to know..."
            2. Body: Reveal a mind-blowing historical fact or misconception.
            3. CTA: "Subscribe for daily history facts."
            """
        elif niche == Niche.SCP:
            prompt = f"""
            {base_short}
            Topic: {topic} (SCP Foundation)
            Style: Clinical but unsettling, "Classified" vibe.
            Structure:
            1. Hook (0-8s): "Item #: {topic}... Level 5 Clearance Required. What you're about to see is strictly classified."
            2. Body: Describe the anomaly's containment procedures and scary properties.
            3. CTA: "Secure. Contain. Protect. Subscribe."
            """
        elif niche == Niche.LIFE_ADVICE:
            prompt = f"""
            {base_short}
            Topic: {topic} (Life Advice/Psychology)
            Style: Direct, empowering, "dark psychology" or "stoic" vibe.
            Structure:
            1. Hook (0-8s): "Stop doing this if you want to be successful..." or "The 1% know this secret about human psychology..."
            2. Body: 3 quick, actionable psychological tricks or advice.
            3. CTA: "Save this video and subscribe to level up."
            """
        elif niche == Niche.NEWS:
            prompt = f"""
            {base_short}
            Topic: {topic} (News/Tech)
            Style: Urgent, breaking news style.
            Structure:
            1. Hook (0-8s): "BREAKING: {topic} just changed everything. This is not a drill."
            2. Body: What happened, why it matters, and what's next.
            3. CTA: "Subscribe to stay updated."
            """

        else: # GENERAL / TRENDING
            prompt = f"""
            {base_short}
            Topic: {topic}
            Style: High energy, viral curiosity gap.
            Structure:
            1. Hook (0-8s): Grab attention immediately with a curiosity gap or shocking statement.
            2. Body: Deliver value/facts quickly.
            3. CTA: Ask to subscribe.
            """

        try:
            # Simple retry logic
            import time
            import random
            
            for i in range(3):
                try:
                    response = self.model.generate_content(prompt)
                    return response.text
                except Exception as e:
                    if "429" in str(e) or "Quota" in str(e):
                        if i == 2: raise e
                        sleep_time = 5 * (i + 1)
                        logger.warning(f"Gemini quota exceeded. Retrying in {sleep_time}s...")
                        time.sleep(sleep_time)
                    else:
                        raise e
                        
        except Exception as e:
            logger.error(f"Script generation failed: {e}")
            return None

if __name__ == "__main__":
    gen = ScriptGenerator()
    print(gen.generate_script("The Rake", niche=Niche.HORROR))
