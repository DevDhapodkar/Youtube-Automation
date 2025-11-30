import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=api_key)

models_to_try = [
    'gemini-flash-latest',
    'models/gemini-flash-latest',
    'gemini-pro-latest',
    'models/gemini-pro-latest'
]

for model_name in models_to_try:
    print(f"Trying model: {model_name}")
    try:
        model = genai.GenerativeModel(model_name)
        response = model.generate_content("Hello, are you working?")
        print(f"Success with {model_name}: {response.text}")
        break
    except Exception as e:
        print(f"Failed with {model_name}: {e}")
