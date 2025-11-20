# YouTube Automation Agent - Usage Guide

This agent automates the entire process of running a faceless YouTube channel, from trend analysis to video upload.

## Prerequisites

1.  **Python 3.10+**
2.  **FFmpeg** (Required by MoviePy)
    - Mac: `brew install ffmpeg`
3.  **API Keys** (See Configuration)

## Installation

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Google Cloud Setup (Crucial)**
    - Go to [Google Cloud Console](https://console.cloud.google.com/).
    - Create a project.
    - Enable **YouTube Data API v3**.
    - Create OAuth 2.0 Credentials (Desktop App).
    - Download the JSON file, rename it to `client_secrets.json`, and place it in the project root (outside `src`).

3.  **Environment Variables**
    - Create a `.env` file in the root directory:
    ```env
    GEMINI_API_KEY=your_gemini_key_here
    PEXELS_API_KEY=your_pexels_key_here
    YOUTUBE_API_KEY=your_youtube_api_key_here # Optional, for trends
    UPLOAD_FREQUENCY_HOURS=24
    ```

## Running the Agent

Start the agent:
```bash
python main.py
```

- On the first run, it will open a browser window to authenticate with your Google account for YouTube uploads.
- It will then run the cycle immediately for verification.
- After that, it will run on the scheduled interval (default: every 24 hours).

## Features

- **Trend Analysis**: Checks Google Trends and YouTube for viral topics.
- **Scripting**: Uses Gemini Pro to write engaging scripts.
- **Voice**: Uses Microsoft Edge TTS for high-quality neural voiceovers.
- **Visuals**: Fetches stock footage from Pexels.
- **Editing**: Assembles video with subtitles using MoviePy.
- **Upload**: Uploads to YouTube as a Private video (configurable).

## Troubleshooting

- **MoviePy Error**: Ensure FFmpeg is installed and accessible in your PATH.
- **Authentication Error**: Delete `token.pickle` and run `main.py` again to re-authenticate.
