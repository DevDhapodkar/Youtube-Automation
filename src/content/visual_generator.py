import logging
import requests
import random
import os
import time
from config.settings import Config
from gradio_client import Client

logger = logging.getLogger(__name__)

from src.content.image_generator import ImageGenerator

class VideoGenerator:
    """
    Generates AI videos using Hugging Face Spaces (Free).
    NOTE: Many free text-to-video spaces are gated or unreliable.
    This is kept as an optional feature that gracefully fails.
    """
    def __init__(self):
        # Note: Free video generation spaces are often gated or unavailable
        # This feature is experimental and may not work consistently
        self.enabled = False  # Disabled by default due to reliability issues
        self.space_id = None
        self.client = None
        logger.info("VideoGenerator initialized (disabled - free spaces unreliable)")
        
    def generate_video(self, prompt, output_path):
        """
        Generate a short video from text.
        Returns None if disabled or fails.
        """
        if not self.enabled:
            logger.debug("Video generation disabled - using images and stock videos instead")
            return None
            
        try:
            if not self.client:
                logger.info(f"Connecting to Hugging Face Space: {self.space_id}")
                self.client = Client(self.space_id)
            
            logger.info(f"Generating AI video for: {prompt[:50]}...")
            
            result = self.client.predict(
				prompt,
				-1,
				api_name="/infer"
            )
            
            video_path = result
            
            if os.path.exists(video_path):
                import shutil
                shutil.copy(video_path, output_path)
                logger.info(f"AI video generated: {output_path}")
                return output_path
            else:
                logger.error("Generated video file not found.")
                return None
                
        except Exception as e:
            logger.warning(f"Video generation failed (expected for free tier): {e}")
            return None

class VisualGenerator:
    def __init__(self):
        self.api_key = Config.PEXELS_API_KEY
        self.base_url = "https://api.pexels.com/videos/search"
        self.image_gen = ImageGenerator()
        self.video_gen = VideoGenerator()

    def get_mixed_visuals(self, query, script, niche="general", duration=60):
        """
        Get a mix of stock videos and AI generated images.
        Target: Change visual every 2-3 seconds.
        
        Mix: 50% Pexels stock videos + 50% Pollinations AI images
        """
        # Calculate needed visuals
        # Average 2.5s per visual
        needed_count = int(duration / 2.5) + 2 # Safety margin
        
        logger.info(f"Generating {needed_count} visuals for {duration}s video...")
        
        visuals = []
        
        # 1. Get Stock Videos (50% of visuals)
        stock_count = needed_count // 2
        stock_videos = self.get_stock_videos(query, count=stock_count)
        visuals.extend(stock_videos)
        
        # 2. Generate AI Images with Pollinations (50% of visuals)
        image_count = needed_count - len(stock_videos)
        
        if image_count > 0:
            logger.info(f"Generating {image_count} AI images with Pollinations.ai...")
            images = self.image_gen.create_images_for_script(script, niche, count=image_count)
            visuals.extend(images)
        
        # Shuffle to mix them up
        random.shuffle(visuals)
        
        logger.info(f"Total visuals generated: {len(visuals)} ({len(stock_videos)} videos, {len(visuals) - len(stock_videos)} AI images)")
        
        return visuals

    def get_stock_videos(self, queries, count=3, duration_min=5, orientation='portrait'):
        """
        Fetch stock videos from Pexels for a list of queries.
        queries: list of search terms (e.g. ["horror dark", "scary forest"])
        count: total number of videos to try to fetch
        """
        if not self.api_key:
            logger.error("PEXELS_API_KEY is missing.")
            return []
            
        if isinstance(queries, str):
            queries = [queries]

        headers = {'Authorization': self.api_key}
        video_files = []
        
        # Calculate videos per query
        videos_per_query = max(1, count // len(queries))
        
        for query in queries:
            if len(video_files) >= count:
                break
                
            params = {
                'query': query,
                'per_page': videos_per_query + 2, # Fetch a few extra to filter
                'orientation': orientation,
                'size': 'medium' # Use medium for better quality than small
            }

            try:
                logger.info(f"Searching Pexels for: {query}")
                response = requests.get(self.base_url, headers=headers, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                for video in data.get('videos', []):
                    if len(video_files) >= count:
                        break
                        
                    # Find a suitable video file url
                    files = video.get('video_files', [])
                    
                    # Filter for suitable width (720p to 1080p is good)
                    # We want vertical if possible, but Pexels 'orientation' param handles that mostly.
                    # Just ensure it's not too huge (4k) to save bandwidth.
                    files = [f for f in files if f.get('width', 9999) <= 1080 and f.get('width', 0) >= 500]
                    
                    if not files:
                        continue
                        
                    # Sort by quality (width) descending
                    files.sort(key=lambda x: x['width'], reverse=True)
                    
                    if files:
                        video_url = files[0]['link']
                        filename = f"{video['id']}.mp4"
                        filepath = os.path.join(Config.ASSETS_DIR, filename)
                        
                        # Skip if already downloaded
                        if os.path.exists(filepath):
                            logger.info(f"Video already exists: {filepath}")
                            if filepath not in video_files:
                                video_files.append(filepath)
                            continue
                        
                        if not os.path.exists(Config.ASSETS_DIR):
                            os.makedirs(Config.ASSETS_DIR)
                            
                        self._download_file(video_url, filepath)
                        if os.path.exists(filepath):
                            video_files.append(filepath)
                
            except Exception as e:
                logger.error(f"Failed to fetch stock videos for '{query}': {e}")
                continue
        
        # If we didn't get enough videos, try the first query again with more results
        if len(video_files) < count and queries:
            # ... (fallback logic could go here, but keeping it simple for now)
            pass
            
        return video_files

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
