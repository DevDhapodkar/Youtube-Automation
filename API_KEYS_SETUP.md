# YouTube Automation Agent - Environment Setup

## Required API Keys

Add these to your `.env` file:

```bash
# Core APIs (Required)
GEMINI_API_KEY=your_gemini_key_here
PEXELS_API_KEY=your_pexels_key_here
YOUTUBE_API_KEY=your_youtube_key_here

# Optional APIs (Enhances quality)
HUGGINGFACE_API_KEY=your_huggingface_key_here  # For AI image generation
PIXABAY_API_KEY=your_pixabay_key_here          # For sound effects
```

## How to Get API Keys

### 1. Hugging Face (Free - for AI Images)
1. Go to https://huggingface.co/
2. Sign up for free account
3. Go to Settings → Access Tokens
4. Create new token (Read access is enough)
5. Copy and paste into `.env`

### 2. Pixabay (Free - for Sound Effects)
1. Go to https://pixabay.com/api/docs/
2. Sign up for free account
3. Get your API key from dashboard
4. Copy and paste into `.env`

## What Each Key Does

- **GEMINI_API_KEY**: Generates scripts and topics
- **PEXELS_API_KEY**: Downloads stock video footage
- **YOUTUBE_API_KEY**: Fetches trending topics
- **HUGGINGFACE_API_KEY**: Generates realistic AI images when stock footage unavailable
- **PIXABAY_API_KEY**: Adds ambient sound effects (horror sounds, music, etc.)

## Without Optional Keys

- No HUGGINGFACE_API_KEY → Uses simple gradient placeholders instead of AI images
- No PIXABAY_API_KEY → Videos have voice only, no ambient sounds
