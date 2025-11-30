import logging
import io
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import os
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config.settings import Config
from src.trends.trend_analyzer import TrendAnalyzer
from src.content.script_generator import ScriptGenerator, Niche
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
    selected_niche = Niche.GENERAL
    schedule = [] # ["10:00", "18:00"]

state = AgentState()
clients = []
scheduler = AsyncIOScheduler()

# Models
class ConfigUpdate(BaseModel):
    gemini_key: str | None = None
    pexels_key: str | None = None
    upload_freq: int | None = None
    niche: str | None = None
    schedule: list[str] | None = None

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
    scheduler.start()
    logger.info("Scheduler started.")

async def run_automation_cycle(niche: Niche = Niche.GENERAL):
    if state.is_running:
        logger.warning("Agent already running, skipping cycle.")
        return

    state.is_running = True
    state.current_action = f"Starting Cycle ({niche.value})..."
    await manager.broadcast({"type": "status", "data": state.current_action})
    
    try:
        # 1. Topic Selection based on Niche
        state.current_action = "Selecting Topic..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        
        # Use AI to generate topics dynamically
        from src.content.topic_generator import TopicGenerator
        topic_gen = TopicGenerator()
        
        if niche == Niche.NEWS:
            # For news, use trending topics
            trend_analyzer = TrendAnalyzer()
            topic = f"Breaking: {trend_analyzer.select_topic()}"
        elif niche == Niche.GENERAL or niche == Niche.TRENDING:
            # For general, use trending topics
            trend_analyzer = TrendAnalyzer()
            topic = trend_analyzer.select_topic()
        else:
            # For all other niches, generate AI topics
            topic = topic_gen.generate_topic(niche.value)
            
        await manager.broadcast({"type": "log", "data": f"Selected Topic: {topic}"})
        
        if not topic:
            raise Exception("No topic selected")

        # 2. Content
        state.current_action = f"Generating Script for: {topic}"
        await manager.broadcast({"type": "status", "data": state.current_action})
        
        script_gen = ScriptGenerator()
        script = script_gen.generate_script(topic, niche=niche)
        await manager.broadcast({"type": "log", "data": "Script generated."})
        
        state.current_action = "Generating Audio..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        audio_gen = AudioGenerator()
        audio_path = os.path.join(Config.ASSETS_DIR, "temp_audio.mp3")
        audio_gen.generate_audio(script, audio_path, target_duration=60)
        
        # Add ambient sound effects
        state.current_action = "Adding Sound Effects..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        from src.audio.sound_effects import SoundEffectGenerator
        sfx_gen = SoundEffectGenerator()
        ambient_sound = sfx_gen.get_ambient_sound(niche.value)
        
        if ambient_sound:
            mixed_audio_path = os.path.join(Config.ASSETS_DIR, "audio_with_sfx.mp3")
            audio_path = sfx_gen.mix_audio(audio_path, ambient_sound, mixed_audio_path, ambient_volume=0.2)
        
        state.current_action = "Gathering Visuals..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        visual_gen = VisualGenerator()
        
        # Generate multiple queries for better variety
        base_query = " ".join(topic.split()[:2])
        queries = [base_query]
        if niche == Niche.HORROR:
            queries.extend(["scary dark", "creepy forest", "nightmare"])
        elif niche == Niche.HORROR_STORIES:
            queries.extend(["dark hallway", "abandoned building night", "eerie shadows", "fog mysterious"])
        elif niche == Niche.HISTORY:
            queries.extend(["ancient ruins", "historical vintage", "museum"])
        elif niche == Niche.SCP:
            queries.extend(["laboratory dark", "military secret", "monster"])
        elif niche == Niche.LIFE_ADVICE:
            queries.extend(["meditation", "success business", "calm nature"])
        else:
            queries.extend(["cinematic", "technology", "abstract background"])
            
        visual_paths = visual_gen.get_stock_videos(queries, count=4)
        
        # If we don't have enough visuals, generate AI images
        if len(visual_paths) < 2:
            logger.info("Insufficient stock footage, generating AI images...")
            from src.content.image_generator import ImageGenerator
            img_gen = ImageGenerator()
            ai_images = img_gen.create_images_for_script(script, niche.value, count=3)
            visual_paths.extend(ai_images)
            await manager.broadcast({"type": "log", "data": f"Generated {len(ai_images)} AI images"})
        
        # 3. Production - Using FFmpeg (memory efficient)
        state.current_action = "Editing Video..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        
        video_editor = VideoEditor()
        video_path = os.path.join(Config.ASSETS_DIR, "final_video.mp4")
        final_video = video_editor.create_short(audio_path, visual_paths, script, video_path, niche=niche.value)
        
        # 4. Upload
        state.current_action = "Uploading..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        
        # Ensure auth before upload
        uploader = YouTubeUploader()
        if not uploader.youtube:
             await manager.broadcast({"type": "error", "data": "YouTube Auth failed. Please authenticate first."})
             raise Exception("Not Authenticated")

        if final_video:
             description = f"An AI generated video about {topic}.\n\n#shorts #ai #facts #{niche.value}"
             tags = ["shorts", "ai", "facts", niche.value, topic.split()[0]]
             
             # UNCOMMENT TO ENABLE REAL UPLOAD
             video_id = uploader.upload_video(final_video, topic, description, tags)
             await manager.broadcast({"type": "log", "data": f"Uploaded! ID: {video_id}"})
             
             # await manager.broadcast({"type": "log", "data": "Upload simulated (Safety Mode). Uncomment in api/main.py to enable."})
        
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
        "is_authenticated": os.path.exists(os.path.join(Config.BASE_DIR, '..', 'token.pickle')),
        "niche": state.selected_niche,
        "schedule": state.schedule
    }

@app.post("/update_config")
async def update_config(config: ConfigUpdate):
    if config.niche:
        try:
            state.selected_niche = Niche(config.niche)
            logger.info(f"Niche updated to: {state.selected_niche}")
        except ValueError:
            pass
            
    if config.schedule is not None:
        state.schedule = config.schedule
        # Update scheduler
        scheduler.remove_all_jobs()
        for time_str in state.schedule:
            try:
                hour, minute = map(int, time_str.split(':'))
                scheduler.add_job(run_automation_cycle, CronTrigger(hour=hour, minute=minute), args=[state.selected_niche])
                logger.info(f"Scheduled job for {time_str}")
            except Exception as e:
                logger.error(f"Invalid time format {time_str}: {e}")
        
    return {"message": "Config updated", "niche": state.selected_niche, "schedule": state.schedule}

@app.post("/start")
async def start_agent():
    if state.is_running:
        return {"message": "Already running"}
    asyncio.create_task(run_automation_cycle(state.selected_niche))
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
