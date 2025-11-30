import asyncio
import os
import logging
from src.content.audio_generator import AudioGenerator
from src.content.image_generator import ImageGenerator
from src.video.video_editor import VideoEditor
from config.settings import Config

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify():
    logger.info("Starting verification...")
    
    # Ensure assets dir exists
    if not os.path.exists(Config.ASSETS_DIR):
        os.makedirs(Config.ASSETS_DIR)

    # 1. Test Audio & Timestamps
    logger.info("Testing Audio & Timestamps...")
    audio_gen = AudioGenerator()
    text = "This is a test of the accurate subtitle synchronization system. Each word should appear exactly when spoken."
    audio_path = os.path.join(Config.ASSETS_DIR, "test_verify_audio.mp3")
    
    # Run sync wrapper which calls async implementation
    audio_gen.generate_audio(text, audio_path, target_duration=10)
    
    timestamp_path = audio_path.replace('.mp3', '_timestamps.json')
    if os.path.exists(timestamp_path):
        logger.info(f"SUCCESS: Timestamp file created at {timestamp_path}")
    else:
        logger.error("FAILURE: Timestamp file NOT created")
        return

    # 2. Test Image Generation (Gemini)
    logger.info("Testing Image Generation...")
    img_gen = ImageGenerator()
    img_path = os.path.join(Config.ASSETS_DIR, "test_verify_image.jpg")
    
    # Use a simple prompt
    result = img_gen.generate_image("A futuristic city with flying cars", "general", img_path)
    
    if result and os.path.exists(img_path):
        logger.info(f"SUCCESS: Image generated at {img_path}")
    else:
        logger.error("FAILURE: Image generation failed")
        # Don't return, try to proceed with placeholder if possible or just skip

    # 3. Test Video Assembly with Subtitles
    logger.info("Testing Video Assembly...")
    video_editor = VideoEditor()
    
    # Use the generated image and maybe a duplicate to make a video
    visuals = [img_path, img_path] 
    
    output_video = os.path.join(Config.ASSETS_DIR, "test_verify_video.mp4")
    
    # Create short
    final_video = video_editor.create_short(audio_path, visuals, text, output_video)
    
    if final_video and os.path.exists(final_video):
        logger.info(f"SUCCESS: Video created at {final_video}")
        
        # Check SRT content
        srt_path = os.path.join(Config.ASSETS_DIR, "subtitles.srt")
        if os.path.exists(srt_path):
            with open(srt_path, 'r') as f:
                content = f.read()
                logger.info(f"SRT Content Preview:\n{content[:200]}...")
        else:
            logger.error("FAILURE: SRT file not found")
            
    else:
        logger.error("FAILURE: Video creation failed")

if __name__ == "__main__":
    asyncio.run(verify())
