import logging
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

class TopicGenerator:
    def __init__(self):
        if Config.GEMINI_API_KEY:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-flash-latest')
        else:
            logger.error("GEMINI_API_KEY is missing. Topic generation will fail.")
            self.model = None

    def generate_topic(self, niche):
        """
        Generate a topic using AI based on the niche.
        """
        if not self.model:
            return "Default Topic"

        prompts = {
            "horror": """Generate ONE viral horror topic for a YouTube Short. 
            Examples: "The Rake Cryptid", "The Russian Sleep Experiment", "The Hat Man"
            Output ONLY the topic name, nothing else.""",
            
            "horror_stories": """Generate ONE creepy, suspenseful story premise for a horror YouTube Short.
            Style: "A [person] [discovers/experiences] [something unsettling]"
            Examples: 
            - "A night-shift nurse hears a patient calling for help from a room that's been empty for months"
            - "A programmer finds comments in their code written in a language that doesn't exist"
            Output ONLY the premise, one sentence, nothing else.""",
            
            "history": """Generate ONE fascinating historical topic for a YouTube Short.
            Examples: "The Dancing Plague of 1518", "The Voynich Manuscript", "Cleopatra's Lost Tomb"
            Output ONLY the topic name, nothing else.""",
            
            "scp": """Generate ONE SCP Foundation topic for a YouTube Short.
            Format: "SCP-[number] [nickname]"
            Examples: "SCP-173 The Sculpture", "SCP-096 The Shy Guy"
            Output ONLY the SCP designation and name, nothing else.""",
            
            "life_advice": """Generate ONE viral life advice/psychology topic for a YouTube Short.
            Style: "How to [achieve something desirable]" or "[Psychology concept] That Actually Works"
            Examples: "How to Read Anyone's Body Language", "Dark Psychology Tricks That Work"
            Output ONLY the topic, nothing else.""",
            
            "news": """Generate ONE trending tech/news topic that would be viral right now.
            Style: Something current, exciting, or controversial
            Examples: "AI Breakthrough Changes Everything", "New Discovery Shocks Scientists"
            Output ONLY the topic, nothing else.""",
            
            "general": """Generate ONE viral, curiosity-gap topic for a YouTube Short.
            Style: Surprising facts, mind-blowing revelations, "You won't believe..."
            Examples: "The Truth About Dreams", "Why Humans Can't Breathe Underwater"
            Output ONLY the topic, nothing else."""
        }

        prompt = prompts.get(niche, prompts["general"])
        
        try:
            response = retry_with_backoff(lambda: self.model.generate_content(prompt))
            topic = response.text.strip()
            logger.info(f"Generated topic for {niche}: {topic}")
            return topic
        except Exception as e:
            logger.error(f"Topic generation failed: {e}")
            return f"Trending {niche.replace('_', ' ').title()} Topic"

    def generate_catchy_title(self, topic):
        """
        Generate a short, clickable, viral YouTube title based on the topic.
        """
        if not self.model:
            return topic

        prompt = f"""
        Rewrite this topic into a SINGLE, short, viral, clickbaity YouTube Short title.
        Topic: "{topic}"
        
        Rules:
        - Max 6 words.
        - Use ALL CAPS for key words.
        - No hashtags.
        - No quotes.
        - Make it sound like something a human would click.
        - Examples: "I Found The SCARIEST Website", "The TRUTH About Dreams", "Do NOT Go Here"
        
        Output ONLY the title.
        """
        
        try:
            response = retry_with_backoff(lambda: self.model.generate_content(prompt))
            title = response.text.strip().replace('"', '')
            logger.info(f"Generated catchy title: {title}")
            return title
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            return topic
