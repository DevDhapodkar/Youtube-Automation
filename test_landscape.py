from src.video.scene_based_orchestrator import SceneBasedVideoOrchestrator
from config.settings import Config
import logging
import os
import subprocess
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_landscape_video():
    try:
        orchestrator = SceneBasedVideoOrchestrator()
        
        # Short script for testing
        script = "This is a test of the landscape video generation capabilities. We are checking if the output is 16 by 9."
        
        output_path = os.path.join(Config.ASSETS_DIR, "test_landscape.mp4")
        
        logger.info("Generating landscape video...")
        result = orchestrator.create_video(
            script=script,
            output_path=output_path,
            target_duration=10,
            niche="general",
            orientation="landscape"
        )
        
        if result and os.path.exists(result):
            logger.info(f"Video created at {result}")
            
            # Verify dimensions
            cmd = [
                'ffprobe', 
                '-v', 'error', 
                '-select_streams', 'v:0', 
                '-show_entries', 'stream=width,height', 
                '-of', 'json', 
                result
            ]
            probe = subprocess.run(cmd, capture_output=True, text=True)
            data = json.loads(probe.stdout)
            width = data['streams'][0]['width']
            height = data['streams'][0]['height']
            
            logger.info(f"Dimensions: {width}x{height}")
            
            if width == 1920 and height == 1080:
                logger.info("SUCCESS: Video is 1920x1080 (Landscape)")
            else:
                logger.error(f"FAILURE: Dimensions are {width}x{height}")
                
        else:
            logger.error("FAILURE: Video generation failed.")
            
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    test_landscape_video()
