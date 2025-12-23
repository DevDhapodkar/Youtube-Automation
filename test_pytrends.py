from pytrends.request import TrendReq
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_pytrends():
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        
        logger.info("Fetching trending searches...")
        trending = pytrends.trending_searches(pn='united_states')
        print("Trending Searches (US):")
        print(trending.head())
        
        logger.info("Fetching real-time trending searches...")
        realtime = pytrends.realtime_trending_searches(pn='US')
        print("\nReal-time Trending Searches (US):")
        print(realtime.head())
        
    except Exception as e:
        logger.error(f"pytrends failed: {e}")

if __name__ == "__main__":
    test_pytrends()
