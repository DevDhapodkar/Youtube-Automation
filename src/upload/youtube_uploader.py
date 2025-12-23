import logging
import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from config.settings import Config

logger = logging.getLogger(__name__)

class YouTubeUploader:
    def __init__(self, interactive=False, url_callback=None):
        self.SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.readonly']
        self.client_secrets_file = os.path.join(Config.BASE_DIR, '..', 'client_secrets.json')
        self.token_file = os.path.join(Config.BASE_DIR, '..', 'token.pickle')
        self.youtube = self._authenticate(interactive, url_callback)

    def _authenticate(self, interactive=False, url_callback=None):
        creds = None
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            elif interactive:
                if not os.path.exists(self.client_secrets_file):
                    logger.error("client_secrets.json not found. Cannot authenticate.")
                    return None
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, self.SCOPES)
                
                # Generate and print URL for manual access if browser fails
                auth_url, _ = flow.authorization_url(prompt='consent')
                logger.info(f"If the browser does not open, please visit this URL to authorize: {auth_url}")
                logger.info(f"AUTH URL: {auth_url}")
                
                if url_callback:
                    url_callback(auth_url)
                
                # Write URL to file for debugging
                with open(os.path.join(Config.BASE_DIR, '..', 'auth_url.txt'), 'w') as f:
                    f.write(auth_url)
                
                creds = flow.run_local_server(port=8080, prompt='consent')
            else:
                return None
            
            with open(self.token_file, 'wb') as token:
                pickle.dump(creds, token)

        return build('youtube', 'v3', credentials=creds)

    def upload_video(self, file_path, title, description, tags=[], category_id="22", thumbnail_path=None): # 22 is People & Blogs
        if not self.youtube:
            logger.error("Not authenticated.")
            return None

        logger.info(f"Uploading {file_path}...")
        
        body = {
            'snippet': {
                'title': title[:100], # Max 100 chars
                'description': description,
                'tags': tags,
                'categoryId': category_id
            },
            'status': {
                'privacyStatus': 'private', # Start private for safety
                'selfDeclaredMadeForKids': False,
            }
        }

        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
        
        try:
            request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            response = request.execute()
            video_id = response['id']
            logger.info(f"Upload Complete! Video ID: {video_id}")
            
            # Upload Thumbnail if provided
            if thumbnail_path and os.path.exists(thumbnail_path):
                logger.info(f"Uploading thumbnail: {thumbnail_path}")
                try:
                    self.youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(thumbnail_path)
                    ).execute()
                    logger.info("Thumbnail uploaded successfully.")
                except Exception as e:
                    logger.error(f"Thumbnail upload failed: {e}")
            
            return video_id
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return None

    def get_channel_stats(self):
        if not self.youtube:
            return None
        
        try:
            request = self.youtube.channels().list(
                part="statistics",
                mine=True
            )
            response = request.execute()
            stats = response['items'][0]['statistics']
            logger.info(f"Channel Stats: {stats}")
            return stats
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return None

if __name__ == "__main__":
    # Test auth
    uploader = YouTubeUploader()
    uploader.get_channel_stats()
