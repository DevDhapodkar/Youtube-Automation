import logging
import io
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
from config.settings import Config
from src.trends.trend_analyzer import TrendAnalyzer
from src.content.script_generator import ScriptGenerator
from src.content.audio_generator import AudioGenerator
from src.content.visual_generator import VisualGenerator
from src.content.thumbnail_generator import ThumbnailGenerator
from src.video.video_editor import VideoEditor
from src.upload.youtube_uploader import YouTubeUploader

import queue

# Global log queue
log_queue = queue.Queue()

class WebSocketHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            log_queue.put(msg)
        except Exception:
            self.handleError(record)

# Configure root logger to capture everything
logging.basicConfig(level=logging.INFO)
root_logger = logging.getLogger()
ws_handler = WebSocketHandler()
ws_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
root_logger.addHandler(ws_handler)

logger = logging.getLogger(__name__)

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# State
class AgentState:
    is_running = False
    current_action = "Idle"
    last_log = ""
    is_authenticated = os.path.exists(os.path.join(Config.BASE_DIR, '..', 'token.pickle'))

state = AgentState()
clients = []

# Models
class ConfigUpdate(BaseModel):
    gemini_key: str | None = None
    pexels_key: str | None = None
    upload_freq: int | None = None

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

# Background Task
async def log_broadcaster():
    while True:
        try:
            while not log_queue.empty():
                log = log_queue.get_nowait()
                await manager.broadcast({"type": "log", "data": log})
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Log broadcast error: {e}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(log_broadcaster())

async def run_automation_cycle():
    state.is_running = True
    state.current_action = "Starting Cycle..."
    await manager.broadcast({"type": "status", "data": state.current_action})
    
    try:
        # 1. Trends
        state.current_action = "Analyzing Trends..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        
        trend_analyzer = TrendAnalyzer()
        topic = trend_analyzer.select_topic()
        await manager.broadcast({"type": "log", "data": f"Selected Topic: {topic}"})
        
        if not topic:
            raise Exception("No topic selected")

        # 2. Content
        state.current_action = f"Generating Script for: {topic}"
        await manager.broadcast({"type": "status", "data": state.current_action})
        
        script_gen = ScriptGenerator()
        script = script_gen.generate_script(topic)
        await manager.broadcast({"type": "log", "data": "Script generated."})
        
        state.current_action = "Generating Audio..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        audio_gen = AudioGenerator()
        audio_path = os.path.join(Config.ASSETS_DIR, "temp_audio.mp3")
        audio_gen.generate_audio(script, audio_path)
        
        state.current_action = "Gathering Visuals..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        visual_gen = VisualGenerator()
        query = " ".join(topic.split()[:2])
        visual_paths = visual_gen.get_stock_videos(query)
        
        # 3. Production - Using FFmpeg (memory efficient)
        state.current_action = "Editing Video..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        
        video_editor = VideoEditor()
        video_path = os.path.join(Config.ASSETS_DIR, "final_video.mp4")
        final_video = video_editor.create_short(audio_path, visual_paths, script, video_path)
        
        # 4. Upload
        state.current_action = "Uploading..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        
        # Ensure auth before upload
        uploader = YouTubeUploader()
        if not uploader.youtube:
             await manager.broadcast({"type": "error", "data": "YouTube Auth failed. Please authenticate first."})
             raise Exception("Not Authenticated")

        if final_video:
             description = f"An AI generated video about {topic}.\n\n#shorts #ai #facts"
             tags = ["shorts", "ai", "facts", topic.split()[0]]
             
             # UNCOMMENT TO ENABLE REAL UPLOAD
             # video_id = uploader.upload_video(final_video, topic, description, tags)
             # await manager.broadcast({"type": "log", "data": f"Uploaded! ID: {video_id}"})
             
             await manager.broadcast({"type": "log", "data": "Upload simulated (Safety Mode). Uncomment in api/main.py to enable."})
        
        state.current_action = "Cycle Complete"
        await manager.broadcast({"type": "status", "data": state.current_action})

    except Exception as e:
        state.current_action = f"Error: {str(e)}"
        await manager.broadcast({"type": "error", "data": str(e)})
    finally:
        state.is_running = False
        await manager.broadcast({"type": "state", "data": {"is_running": False}})

# Routes
@app.get("/")
def read_root():
    return {"status": "Online", "agent": "YouTube Automation"}

@app.get("/status")
def get_status():
    return {
        "is_running": state.is_running, 
        "current_action": state.current_action,
        "is_authenticated": os.path.exists(os.path.join(Config.BASE_DIR, '..', 'token.pickle'))
    }

@app.post("/start")
async def start_agent():
    if state.is_running:
        return {"message": "Already running"}
    asyncio.create_task(run_automation_cycle())
    return {"message": "Started"}

@app.post("/stop")
def stop_agent():
    state.is_running = False 
    return {"message": "Stopping..."}

@app.post("/auth")
def authenticate_youtube():
    """
    Trigger OAuth flow explicitly
    """
    try:
        uploader = YouTubeUploader()
        if uploader.youtube:
            state.is_authenticated = True
            return {"message": "Authenticated successfully", "success": True}
        else:
            return {"message": "Authentication failed", "success": False}
    except Exception as e:
        return {"message": str(e), "success": False}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
