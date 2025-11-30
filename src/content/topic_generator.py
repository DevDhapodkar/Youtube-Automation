import logging
import google.generativeai as genai
from config.settings import Config

logger = logging.getLogger(__name__)

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
            response = self.model.generate_content(prompt)
            topic = response.text.strip()
            logger.info(f"Generated topic for {niche}: {topic}")
            return topic
        except Exception as e:
            logger.error(f"Topic generation failed: {e}")
            return f"Trending {niche.replace('_', ' ').title()} Topic"
