import logging
from pytrends.request import TrendReq
from googleapiclient.discovery import build
from config.settings import Config
import random

logger = logging.getLogger(__name__)

class TrendAnalyzer:
    def __init__(self):
        self.pytrends = TrendReq(hl='en-US', tz=360)
        self.youtube = None
        if Config.YOUTUBE_API_KEY:
            self.youtube = build('youtube', 'v3', developerKey=Config.YOUTUBE_API_KEY)
        else:
            logger.warning("YOUTUBE_API_KEY not found. YouTube specific trend data will be limited.")

    def get_google_trends(self, keywords=['technology', 'AI', 'future', 'gadgets']):
        """
        Fetch interest over time for given keywords to find rising topics.
        """
        try:
            logger.info(f"Fetching Google Trends for: {keywords}")
            self.pytrends.build_payload(keywords, cat=0, timeframe='now 7-d', geo='', gprop='youtube')
            data = self.pytrends.interest_over_time()
            if not data.empty:
                # Find the keyword with the highest recent interest
                latest_data = data.iloc[-1]
                top_keyword = latest_data.idxmax()
                logger.info(f"Top trending keyword: {top_keyword}")
                return top_keyword
            return random.choice(keywords)
        except Exception as e:
            logger.error(f"Error fetching Google Trends: {e}")
            return random.choice(keywords)

    def get_youtube_trends(self, region_code='US', max_results=5):
        """
        Fetch trending videos from YouTube directly.
        """
        if not self.youtube:
            return []
        
        try:
            logger.info("Fetching YouTube Trends...")
            request = self.youtube.videos().list(
                part="snippet,statistics",
                chart="mostPopular",
                regionCode=region_code,
                maxResults=max_results
            )
            response = request.execute()
            
            trends = []
            for item in response.get('items', []):
                title = item['snippet']['title']
                trends.append(title)
            
            return trends
        except Exception as e:
            logger.error(f"Error fetching YouTube Trends: {e}")
            return []

    def select_topic(self, niche_keywords=None):
        """
        Main method to decide on a video topic.
        """
        if niche_keywords is None:
            niche_keywords = ['Artificial Intelligence', 'Space Exploration', 'Coding', 'Tech News']
            
        # 1. Try to get a specific trending keyword from Google Trends
        trending_keyword = self.get_google_trends(niche_keywords)
        
        # 2. Get general YouTube trends to see if we can piggyback (optional context)
        yt_trends = self.get_youtube_trends()
        
        # 3. Formulate a topic
        # In a real scenario, we might use an LLM here to combine the trending keyword 
        # with a viral structure. For now, we return the keyword.
        
        topic = f"The Future of {trending_keyword}"
        logger.info(f"Selected Topic: {topic}")
        return topic

if __name__ == "__main__":
    # Test
    analyzer = TrendAnalyzer()
    print(analyzer.select_topic())
