# 🔑 API & Cloud Setup Guide

To run the YouTube Automation Agent, you need several keys from different providers. This guide walks you through getting each one.

## 1. Google Gemini (AI Brain)
- **Status**: Required
- **Purpose**: Scriptwriting, topic discovery, and AI logic.
- **Link**: [Google AI Studio](https://aistudio.google.com/app/apikey)
- **Steps**:
    1. Sign in with your Google account.
    2. Click "Create API key".
    3. Copy the key to `GEMINI_API_KEY` in your `.env`.

## 2. Pexels (Stock Video)
- **Status**: Required
- **Purpose**: Main visual source for videos.
- **Link**: [Pexels API](https://www.pexels.com/api/)
- **Steps**:
    1. Sign up/Login to Pexels.
    2. Visit the API documentation and "Request API Key".
    3. Copy to `PEXELS_API_KEY`.

## 3. YouTube & Google Cloud (Automation)
- **Status**: Required for Uploads
- **Purpose**: Automated video uploads and trending analysis.
- **Link**: [Google Cloud Console](https://console.cloud.google.com/)
- **Steps**:
    1. Create a new project.
    2. Enable **YouTube Data API v3**.
    3. Go to **Credentials** -> **Create Credentials** -> **OAuth Client ID** (Type: Desktop App).
    4. Download the JSON and rename it to `client_secrets.json` in your project root.
    5. Also create an **API Key** (restricted to YouTube Data API) and copy to `YOUTUBE_API_KEY`.

## 4. Optional Enhancements
| Provider | Purpose | Where to Get |
|----------|---------|--------------|
| **Hugging Face** | AI Image Generation | [Tokens Page](https://huggingface.co/settings/tokens) |
| **Pixabay** | Sound Effects | [API Docs](https://pixabay.com/api/docs/) |
| **Freesound** | Ambient Audio | [API Apply](https://freesound.org/apiv2/apply) |

---

### [Advanced] Vertex AI Setup
If you prefer using Vertex AI over standard Gemini API:
1. Enable **Vertex AI API** in Google Cloud.
2. Ensure your Service Account has `Vertex AI User` role.
3. Set `GOOGLE_APPLICATION_CREDENTIALS` to your service account key path.
