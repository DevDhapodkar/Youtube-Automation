import logging
from pytrends.request import TrendReq
from googleapiclient.discovery import build
from config.settings import Config
import random

logger = logging.getLogger(__name__)

import google.generativeai as genai
import json

class TrendAnalyzer:
    def __init__(self):
        self.pytrends = TrendReq(hl='en-US', tz=360)
        self.youtube = None
        if Config.YOUTUBE_API_KEY:
            self.youtube = build('youtube', 'v3', developerKey=Config.YOUTUBE_API_KEY)
        else:
            logger.warning("YOUTUBE_API_KEY not found. YouTube specific trend data will be limited.")
        
        if Config.GEMINI_API_KEY:
            genai.configure(api_key=Config.GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-flash-latest')
        else:
            logger.error("GEMINI_API_KEY is missing. Trend analysis will be limited.")
            self.model = None

    def get_google_trends(self, keywords=['technology', 'AI', 'future', 'gadgets']):
        """
        Fetch interest over time for given keywords to find rising topics.
        """
        try:
            logger.info(f"Fetching Google Trends for: {keywords}")
            # Locked to US (geo='US') and YouTube search (gprop='youtube')
            self.pytrends.build_payload(keywords, cat=0, timeframe='now 7-d', geo='US', gprop='youtube')
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

    def get_youtube_trends(self, region_code='US', max_results=10):
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

    def analyze_trends_with_gemini(self, trends_list):
        """
        Uses Gemini to analyze trending titles and select the best niche/topic.
        """
        if not self.model or not trends_list:
            return None

        prompt = f"""
        You are a YouTube Trend Analyst. Analyze these trending video titles:
        {trends_list}
        
        Your Goal: Identify a "Blue Ocean" opportunity for the US MARKET - a niche/topic with high demand, high CPM (maximum money making potential), but low competition.
        
        1. Select the BEST niche from this list: ["horror", "history", "scp", "life_advice", "news", "finance", "tech", "luxury", "general"]
           - CRITICAL: Prioritize high CPM niches like Finance, Tech, and Luxury to maximize revenue.
           - Ensure the topic is highly relevant to US culture and trends.
        2. Formulate a specific, viral topic based on the trends but adapted for the chosen niche.
           - The topic must be "Clickbaity" and "High Engagement".
        
        Return ONLY a JSON object:
        {{
            "topic": "The New AI Model Everyone Is Talking About"
        }}
        
        Return ONLY the JSON.
        """

        try:
            response = self.model.generate_content(prompt)
            text = response.text.strip()
            
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]
                
            data = json.loads(text)
            logger.info(f"Gemini selected niche: {data.get('niche')} with topic: {data.get('topic')}")
            return data
        except Exception as e:
            logger.error(f"Gemini trend analysis failed: {e}")
            return None

    def select_niche_and_topic(self):
        """
        Main method to decide on a niche and video topic based on real-time trends.
        """
        # 1. Get real-time YouTube trends
        yt_trends = self.get_youtube_trends(max_results=15)
        
        # 2. Use Gemini to analyze and pick best niche/topic
        if yt_trends:
            analysis = self.analyze_trends_with_gemini(yt_trends)
            if analysis:
                return analysis.get("niche", "general"), analysis.get("topic", "Trending Topic")
        
        # Fallback if API fails
        logger.warning("Using fallback topic selection.")
        return "general", "Interesting Facts You Didn't Know"

if __name__ == "__main__":
    # Test
    analyzer = TrendAnalyzer()
    print(analyzer.select_niche_and_topic())
