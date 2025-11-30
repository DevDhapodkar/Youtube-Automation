import os
from dotenv import load_dotenv

load_dotenv()

keys = ["YOUTUBE_API_KEY", "GEMINI_API_KEY", "PEXELS_API_KEY"]
print("Environment Variable Check:")
for key in keys:
    value = os.getenv(key)
    if value:
        print(f"{key}: Present (Length: {len(value)})")
    else:
        print(f"{key}: MISSING")
