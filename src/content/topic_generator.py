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
            "horror": """Generate ONE high-engagement viral horror topic for a US YouTube audience. 
            Focus on extreme curiosity or shocking facts.
            Examples: "The Terrifying Truth of SCP-096", "Why You Should NEVER Visit This Forest In Maine", "The Russian Sleep Experiment: What They Hid"
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
            
            "life_advice": """Generate ONE viral life advice/psychology topic for a high-status US YouTube audience.
            Style: "How to [achieve something extremely desirable]" or "[Dark Psychology] That Actually Works"
            Examples: "How to Read Anyone INSTANTLY", "The $10,000/Month Morning Routine", "Dark Psychology: How to Make Anyone Like You"
            Output ONLY the topic, nothing else.""",
            
            "news": """Generate ONE trending tech/news topic that would be viral right now.
            Style: Something current, exciting, or controversial
            Examples: "AI Breakthrough Changes Everything", "New Discovery Shocks Scientists"
            Output ONLY the topic, nothing else.""",
            
            "general": """Generate ONE viral, curiosity-gap topic for a US YouTube audience.
            Style: Extreme curiosity, "Breaking the Simulation", or "Things You Weren't Supposed to See".
            Examples: "The Secret Map Found in the Vatican", "Why The Moon Landing Was Actually Faked?", "NASA Just Found Something Terrifying"
            Output ONLY the topic, nothing else.""",
            
            "finance": """Generate ONE high-CPM finance/wealth topic for a US YouTube audience.
            Style: Wealth creation, passive income, or economic warnings.
            Examples: "How To Retire in 5 Years", "The Coming Economic Collapse of 2025", "Why 99% of People Will Always Be Poor"
            Output ONLY the topic, nothing else.""",
            
            "tech": """Generate ONE viral tech/AI topic for a US YouTube audience.
            Style: Future tech, AI breakthroughs, or "The End of [Industry]".
            Examples: "Elon Musk: 'AI Is Already Among Us'", "The New iPhone Feature That Changes Everything", "Why AI Will Replace Your Job by 2026"
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
