import time
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from config.settings import Config
import os
from src.trends.trend_analyzer import TrendAnalyzer
from src.content.script_generator import ScriptGenerator
from src.content.audio_generator import AudioGenerator
from src.content.visual_generator import VisualGenerator
from src.content.thumbnail_generator import ThumbnailGenerator
from src.video.video_editor import VideoEditor
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
    Main execution cycle:
    1. Analyze Trends
    2. Generate Content
    3. Produce Video
    4. Upload
    """
    logger.info("Starting automated job cycle...")
    
    try:
        # Initialize Modules
        trend_analyzer = TrendAnalyzer()
        script_gen = ScriptGenerator()
        audio_gen = AudioGenerator()
        visual_gen = VisualGenerator()
        thumb_gen = ThumbnailGenerator()
        video_editor = VideoEditor()
        uploader = YouTubeUploader()

        # Step 1: Trends
        logger.info("Step 1: Analyzing trends...")
        topic = trend_analyzer.select_topic()
        if not topic:
            logger.error("No topic selected. Aborting cycle.")
            return

        # Step 2: Content
        logger.info(f"Step 2: Generating content for '{topic}'...")
        script = script_gen.generate_script(topic, duration_type="short")
        
        audio_path = os.path.join(Config.ASSETS_DIR, "temp_audio.mp3")
        audio_gen.generate_audio(script, audio_path)
        
        # Get visuals based on keywords from topic
        # Simple keyword extraction (first 2 words)
        query = " ".join(topic.split()[:2])
        visual_paths = visual_gen.get_stock_videos(query, count=3)
        
        # Step 3: Production
        logger.info("Step 3: Producing video...")
        video_path = os.path.join(Config.ASSETS_DIR, "final_video.mp4")
        final_video = video_editor.create_short(audio_path, visual_paths, script, video_path)
        
        thumb_path = os.path.join(Config.ASSETS_DIR, "thumbnail.jpg")
        thumb_gen.create_thumbnail(topic, output_path=thumb_path)
        
        # Step 4: Upload
        if final_video and os.path.exists(final_video):
            logger.info("Step 4: Uploading...")
            # Generate description
            description = f"An AI generated video about {topic}.\n\n#shorts #ai #facts"
            tags = ["shorts", "ai", "facts", topic.split()[0]]
            
            uploader.upload_video(final_video, topic, description, tags)
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
