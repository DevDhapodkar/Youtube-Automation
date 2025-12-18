import time
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from config.settings import Config
import os
from src.trends.trend_analyzer import TrendAnalyzer
from src.content.unified_generator import UnifiedContentGenerator
from src.video.scene_based_orchestrator import SceneBasedVideoOrchestrator
from src.upload.youtube_uploader import YouTubeUploader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def job_cycle():
    """
    Main execution cycle with scene-based video generation:
    1. Analyze Trends
    2. Generate Script
    3. Create Video (Scene-Based)
    4. Upload
    """
    logger.info("Starting automated job cycle...")
    
    try:
        # Initialize Modules
        trend_analyzer = TrendAnalyzer()
        unified_gen = UnifiedContentGenerator()
        orchestrator = SceneBasedVideoOrchestrator()
        uploader = YouTubeUploader()

        # Step 1 & 2: Content Generation (Optimized)
        logger.info("Step 1 & 2: Generating content...")
        topic = trend_analyzer.select_topic()
        if not topic:
            logger.error("No topic selected. Aborting cycle.")
            return

        content_data = unified_gen.generate_content_from_topic(topic, niche="general")
        if not content_data:
            logger.error("Content generation failed. Aborting cycle.")
            return

        topic = content_data.get("topic")
        viral_title = content_data.get("title")
        script = content_data.get("script")
        pre_generated_scenes = content_data.get("scenes")
        
        logger.info(f"Generated Topic: {topic}")
        logger.info(f"Generated Title: {viral_title}")
        
        # Step 3: Create Video using Scene-Based System
        logger.info("Step 3: Creating video with scene-based system...")
        video_path = os.path.join(Config.ASSETS_DIR, "final_video.mp4")
        
        final_video = orchestrator.create_video(
            script=script,
            output_path=video_path,
            target_duration=60,  # 60 seconds for YouTube Shorts
            niche="general",
            pre_generated_scenes=pre_generated_scenes
        )
        
        # Step 4: Upload
        if final_video and os.path.exists(final_video):
            logger.info("Step 4: Uploading...")
            # Generate description
            description = f"An AI generated video about {topic}.\n\n#shorts #ai #facts"
            tags = ["shorts", "ai", "facts", topic.split()[0]]
            
            uploader.upload_video(final_video, viral_title, description, tags)
        else:
            logger.error("Video generation failed, skipping upload.")
        
        logger.info("Job cycle completed successfully.")
        
    except Exception as e:
        logger.error(f"Job cycle failed: {e}", exc_info=True)

def main():
    logger.info("Initializing YouTube Automation Agent...")
    Config.validate()
    
    # Ensure assets dir exists
    if not os.path.exists(Config.ASSETS_DIR):
        os.makedirs(Config.ASSETS_DIR)
    
    scheduler = BlockingScheduler()
    
    # Schedule the job
    scheduler.add_job(job_cycle, 'interval', hours=Config.UPLOAD_FREQUENCY_HOURS)
    
    logger.info(f"Scheduler started. Running every {Config.UPLOAD_FREQUENCY_HOURS} hours.")
    
    try:
        # Run once immediately for verification
        logger.info("Running initial verification cycle...")
        job_cycle()
        
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Agent stopped.")

if __name__ == "__main__":
    main()
