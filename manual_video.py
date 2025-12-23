import logging
import os
import sys
from config.settings import Config
from src.content.unified_generator import UnifiedContentGenerator
from src.video.scene_based_orchestrator import SceneBasedVideoOrchestrator
from src.content.thumbnail_generator import ThumbnailGenerator
from src.upload.youtube_uploader import YouTubeUploader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_user_input():
    print("\n" + "="*50)
    print("MANUAL VIDEO GENERATOR")
    print("="*50)
    
    # 1. Niche Selection
    niches = ["horror", "history", "scp", "life_advice", "news", "finance", "tech", "luxury", "custom"]
    print("\nAvailable Niches:")
    for i, n in enumerate(niches):
        print(f"{i+1}. {n}")
    
    while True:
        try:
            choice = input("\nSelect Niche (number) or type custom name: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(niches):
                niche = niches[int(choice)-1]
                if niche == "custom":
                    niche = input("Enter custom niche name: ").strip()
                break
            elif choice:
                niche = choice
                break
        except ValueError:
            pass
            
    # 2. Topic Selection
    topic = input("\nEnter specific topic (leave empty for AI auto-generation): ").strip()
    
    # 3. Video Type (Orientation)
    print("\nVideo Type:")
    print("1. YouTube Short (Portrait 9:16)")
    print("2. Long Form Video (Landscape 16:9)")
    
    while True:
        choice = input("Select Type (1/2): ").strip()
        if choice == "1":
            orientation = "portrait"
            duration_type = "short"
            default_duration = 60
            break
        elif choice == "2":
            orientation = "landscape"
            duration_type = "long"
            default_duration = 300
            break
            
    # 4. Duration
    try:
        dur_input = input(f"\nTarget Duration in seconds (default {default_duration}): ").strip()
        duration = int(dur_input) if dur_input else default_duration
    except ValueError:
        duration = default_duration
        
    # 5. Upload?
    upload = input("\nUpload to YouTube after generation? (y/n): ").lower().strip() == 'y'
    
    return {
        "niche": niche,
        "topic": topic,
        "orientation": orientation,
        "duration_type": duration_type,
        "duration": duration,
        "upload": upload
    }

def generate_video(params):
    logger.info(f"Starting generation with params: {params}")
    
    # Initialize components
    unified_gen = UnifiedContentGenerator()
    orchestrator = SceneBasedVideoOrchestrator()
    thumbnail_gen = ThumbnailGenerator()
    uploader = YouTubeUploader()
    
    # 1. Generate Content
    if params["topic"]:
        logger.info(f"Generating content for topic: {params['topic']}")
        content = unified_gen.generate_content_from_topic(
            topic=params["topic"], 
            niche=params["niche"],
            duration_type=params["duration_type"]
        )
    else:
        logger.info(f"Generating viral topic for niche: {params['niche']}")
        content = unified_gen.generate_full_content(
            niche=params["niche"],
            duration_type=params["duration_type"]
        )
        
    if not content:
        logger.error("Content generation failed.")
        return
        
    logger.info(f"Title: {content['title']}")
    logger.info(f"Topic: {content.get('topic', 'N/A')}")
    
    # 2. Create Video
    output_filename = f"manual_{params['niche']}_{params['orientation']}.mp4"
    output_path = os.path.join(Config.ASSETS_DIR, output_filename)
    
    final_video = orchestrator.create_video(
        script=content['script'],
        output_path=output_path,
        target_duration=params["duration"],
        niche=params["niche"],
        pre_generated_scenes=content.get('scenes'),
        orientation=params["orientation"]
    )
    
    if not final_video:
        logger.error("Video creation failed.")
        return

    logger.info(f"Video created successfully: {final_video}")
    
    # 3. Generate Thumbnail
    logger.info("Generating thumbnail...")
    thumbnail_path = thumbnail_gen.generate_thumbnail(
        topic=content.get('topic', params['topic'] or content['title']),
        niche=params["niche"],
        viral_title=content['title']
    )
    
    if thumbnail_path:
        logger.info(f"Thumbnail created: {thumbnail_path}")
    
    # 4. Upload (Optional)
    if params["upload"]:
        logger.info("Uploading to YouTube...")
        video_id = uploader.upload_video(
            file_path=final_video,
            title=content['title'],
            description=f"{content['title']} #shorts #{params['niche']}" if params['duration_type'] == 'short' else f"{content['title']} - {params['niche']} documentary",
            tags=[params['niche'], "viral", "ai"],
            thumbnail_path=thumbnail_path
        )
        if video_id:
            logger.info(f"Uploaded successfully! Video ID: {video_id}")
    else:
        logger.info("Skipping upload as requested.")

if __name__ == "__main__":
    try:
        params = get_user_input()
        generate_video(params)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        logger.error(f"An error occurred: {e}", exc_info=True)
