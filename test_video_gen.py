import logging
import os
import sys

# Setup logging
logging.basicConfig(level=logging.INFO)

# Add current dir to path
sys.path.append(os.getcwd())

from src.content.visual_generator import VideoGenerator

def test_video():
    print("Testing Video Generation...")
    gen = VideoGenerator()
    output = "test_video.mp4"
    if os.path.exists(output):
        os.remove(output)
        
    result = gen.generate_video("A cinematic drone shot of a futuristic city", output)
    
    if result and os.path.exists(result):
        print(f"SUCCESS: Video generated at {result}")
    else:
        print("FAILURE: Video generation failed")

if __name__ == "__main__":
    test_video()
