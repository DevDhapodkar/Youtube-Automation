from src.content.thumbnail_generator import ThumbnailGenerator
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_thumbnail():
    try:
        gen = ThumbnailGenerator()
        
        topic = "The Mystery of the Bermuda Triangle"
        niche = "history"
        title = "BERMUDA TRIANGLE EXPLAINED"
        
        logger.info("Generating test thumbnail...")
        path = gen.generate_thumbnail(topic, niche, title)
        
        if path and os.path.exists(path):
            logger.info(f"SUCCESS: Thumbnail generated at {path}")
        else:
            logger.error("FAILURE: Thumbnail generation failed.")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    test_thumbnail()
