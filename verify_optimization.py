import logging
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from src.content.unified_generator import UnifiedContentGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_unified_generation():
    print("\n--- Testing Unified Content Generation ---")
    gen = UnifiedContentGenerator()
    
    # Test full generation (topic + title + script + scenes)
    print("\n1. Testing full generation for 'horror' niche...")
    data = gen.generate_full_content("horror")
    
    if data:
        print(f"✓ Topic: {data.get('topic')}")
        print(f"✓ Title: {data.get('title')}")
        print(f"✓ Script Length: {len(data.get('script', '').split())} words")
        print(f"✓ Scenes: {len(data.get('scenes', []))}")
        
        for i, scene in enumerate(data.get('scenes', [])):
            print(f"  Scene {i+1}: {len(scene.get('keywords', []))} keywords")
    else:
        print("✗ Full generation failed")

    # Test generation from topic
    print("\n2. Testing generation from topic 'The Voynich Manuscript'...")
    data = gen.generate_content_from_topic("The Voynich Manuscript", "history")
    
    if data:
        print(f"✓ Topic: {data.get('topic')}")
        print(f"✓ Title: {data.get('title')}")
        print(f"✓ Script Length: {len(data.get('script', '').split())} words")
        print(f"✓ Scenes: {len(data.get('scenes', []))}")
    else:
        print("✗ Generation from topic failed")

if __name__ == "__main__":
    test_unified_generation()
