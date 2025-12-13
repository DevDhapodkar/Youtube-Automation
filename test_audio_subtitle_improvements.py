#!/usr/bin/env python3
"""
Test script to verify audio generation with new SSML settings
and sentence-based subtitle generation.
"""

from src.content.audio_generator import AudioGenerator
from src.video.video_editor import VideoEditor
import os

def test_audio_and_subtitles():
    print("Testing Audio Generation with SSML and Sentence-based Subtitles")
    print("=" * 70)
    
    # Test script with multiple sentences
    test_script = """
    Welcome to this amazing video about artificial intelligence. 
    AI is transforming the world in incredible ways. 
    From healthcare to entertainment, the possibilities are endless. 
    Let's explore how this technology is shaping our future.
    """.strip()
    
    print(f"\nTest Script:\n{test_script}\n")
    
    # Generate audio
    print("Step 1: Generating audio with SSML and JennyNeural voice...")
    gen = AudioGenerator()
    audio_path = 'test_audio_sync.mp3'
    
    result = gen.generate_audio(test_script, audio_path, target_duration=15)
    
    if result and os.path.exists(audio_path):
        print(f"✓ Audio generated successfully: {audio_path}")
        
        # Check for timestamps
        timestamps_path = audio_path.replace('.mp3', '_timestamps.json')
        if os.path.exists(timestamps_path):
            print(f"✓ Timestamps generated: {timestamps_path}")
            
            import json
            with open(timestamps_path, 'r') as f:
                timestamps = json.load(f)
            print(f"  Found {len(timestamps)} timestamp entries")
        else:
            print("✗ No timestamps file found")
    else:
        print("✗ Audio generation failed")
        return
    
    # Generate subtitles
    print("\nStep 2: Generating sentence-based subtitles...")
    editor = VideoEditor()
    srt_path = 'test_subtitles_sync.srt'
    
    duration = editor._get_audio_duration(audio_path)
    editor._generate_srt(test_script, duration, srt_path, audio_path)
    
    if os.path.exists(srt_path):
        print(f"✓ Subtitles generated: {srt_path}")
        
        # Display the SRT content
        print("\nGenerated Subtitles:")
        print("-" * 70)
        with open(srt_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print(content)
        print("-" * 70)
    else:
        print("✗ Subtitle generation failed")
        return
    
    print("\n✓ Test completed successfully!")
    print("\nNext steps:")
    print("1. Listen to the audio file to verify natural speech quality")
    print("2. Review the subtitles to ensure they are sentence-based")
    print("3. Generate a full video to test synchronization")

if __name__ == "__main__":
    test_audio_and_subtitles()
