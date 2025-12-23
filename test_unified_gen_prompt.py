import logging
from src.content.unified_generator import UnifiedContentGenerator

# Mock genai to avoid actual API calls
import google.generativeai as genai
from unittest.mock import MagicMock

genai.GenerativeModel = MagicMock()

def test_prompts():
    generator = UnifiedContentGenerator()
    generator.model = MagicMock()
    
    # Test Short
    generator.generate_full_content("general", "short")
    call_args = generator.model.generate_content.call_args[0][0]
    print("--- Short Prompt ---")
    print(call_args)
    if "180-200 words" in call_args and "6-8 logical scenes" in call_args:
        print("✅ Short prompt looks correct")
    else:
        print("❌ Short prompt incorrect")

    # Test Long
    generator.generate_full_content("general", "long")
    call_args = generator.model.generate_content.call_args[0][0]
    print("\n--- Long Prompt ---")
    print(call_args)
    if "1500-2000 words" in call_args and "15-20 logical scenes" in call_args:
        print("✅ Long prompt looks correct")
    else:
        print("❌ Long prompt incorrect")

if __name__ == "__main__":
    test_prompts()
