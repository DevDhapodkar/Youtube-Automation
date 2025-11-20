import logging
import requests
import random
import os
from config.settings import Config

logger = logging.getLogger(__name__)

class VisualGenerator:
    def __init__(self):
        self.api_key = Config.PEXELS_API_KEY
        self.base_url = "https://api.pexels.com/videos/search"

    def get_stock_videos(self, query, count=2, duration_min=5, orientation='portrait'):
        """
        Fetch stock videos from Pexels.
        orientation: 'portrait' (for Shorts) or 'landscape'
        NOTE: Reduced count to 2 to prevent system overload
        """
        if not self.api_key:
            logger.error("PEXELS_API_KEY is missing.")
            return []

        headers = {'Authorization': self.api_key}
        params = {
            'query': query,
            'per_page': count,
            'orientation': orientation,
            'size': 'small'  # Use smaller size to save memory/bandwidth
        }

        try:
            logger.info(f"Searching Pexels for: {query}")
            response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            video_files = []
            for video in data.get('videos', []):
                # Find a suitable video file url
                files = video.get('video_files', [])
                
                # Filter for smaller files (width <= 1080) to reduce memory usage
                files = [f for f in files if f.get('width', 9999) <= 1080]
                
                if not files:
                    continue
                    
                # Sort by quality (width) but prefer smaller for memory efficiency
                files.sort(key=lambda x: x['width'])
                
                if files:
                    video_url = files[0]['link']
                    # Download the video
                    filename = f"{video['id']}.mp4"
                    filepath = os.path.join(Config.ASSETS_DIR, filename)
                    
                    # Skip if already downloaded
                    if os.path.exists(filepath):
                        logger.info(f"Video already exists: {filepath}")
                        video_files.append(filepath)
                        continue
                    
                    if not os.path.exists(Config.ASSETS_DIR):
                        os.makedirs(Config.ASSETS_DIR)
                        
                    self._download_file(video_url, filepath)
                    video_files.append(filepath)
            
            return video_files

        except Exception as e:
            logger.error(f"Failed to fetch stock videos: {e}")
            return []

    def _download_file(self, url, filepath):
        logger.info(f"Downloading {url} to {filepath}")
        try:
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                # Limit total download size
                total_size = int(r.headers.get('content-length', 0))
                if total_size > 50 * 1024 * 1024:  # 50MB limit per video
                    logger.warning(f"Video too large ({total_size/1024/1024:.1f}MB), skipping")
                    return
                
                with open(filepath, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1MB chunks
                        f.write(chunk)
        except Exception as e:
            logger.error(f"Download failed: {e}")
            if os.path.exists(filepath):
                os.remove(filepath)

if __name__ == "__main__":
    gen = VisualGenerator()
    # gen.get_stock_videos("nature", 1)
