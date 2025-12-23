from src.trends.trend_analyzer import TrendAnalyzer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_intelligent_niche_selection():
    try:
        analyzer = TrendAnalyzer()
        if not analyzer.youtube:
            logger.error("YouTube API not initialized (check API key).")
            return

        logger.info("Testing select_niche_and_topic...")
        niche, topic = analyzer.select_niche_and_topic()
        
        print(f"\nSelected Niche: {niche}")
        print(f"Selected Topic: {topic}")
        
        if niche and topic:
            logger.info("SUCCESS: Intelligent niche selection worked.")
        else:
            logger.error("FAILURE: Niche or topic missing.")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    test_intelligent_niche_selection()
