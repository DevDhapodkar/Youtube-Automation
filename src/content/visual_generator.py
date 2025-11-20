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

    def get_stock_videos(self, query, count=3, duration_min=5, orientation='portrait'):
        """
        Fetch stock videos from Pexels.
        orientation: 'portrait' (for Shorts) or 'landscape'
        """
        if not self.api_key:
            logger.error("PEXELS_API_KEY is missing.")
            return []

        headers = {'Authorization': self.api_key}
        params = {
            'query': query,
            'per_page': count,
            'orientation': orientation,
            'size': 'medium' # Save bandwidth
        }

        try:
            logger.info(f"Searching Pexels for: {query}")
            response = requests.get(self.base_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            video_files = []
            for video in data.get('videos', []):
                # Find a suitable video file url
                files = video.get('video_files', [])
                # Sort by quality (width)
                files.sort(key=lambda x: x['width'], reverse=True)
                
                if files:
                    video_url = files[0]['link']
                    # Download the video
                    filename = f"{video['id']}.mp4"
                    filepath = os.path.join(Config.ASSETS_DIR, filename)
                    
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
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(filepath, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

if __name__ == "__main__":
    gen = VisualGenerator()
    # gen.get_stock_videos("nature", 1)
