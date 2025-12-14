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
    current_task = None  # Store reference to running task

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
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.debug(f"Failed to send to connection: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Background Task for real-time log broadcasting
async def log_broadcaster():
    while True:
        try:
            if not log_queue.empty():
                # Process all available logs immediately
                logs_to_send = []
                while not log_queue.empty():
                    try:
                        log = log_queue.get_nowait()
                        logs_to_send.append(log)
                    except queue.Empty:
                        break
                
                # Broadcast all logs
                for log in logs_to_send:
                    await manager.broadcast({"type": "log", "data": log})
            
            # Short sleep for responsiveness
            await asyncio.sleep(0.05)  # 50ms for near real-time updates
        except Exception as e:
            logger.error(f"Log broadcast error: {e}")
            await asyncio.sleep(0.5)

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
    await manager.broadcast({"type": "state", "data": {"is_running": True}})
    
    try:
        # 1. Topic Selection based on Niche
        state.current_action = "Selecting Topic..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        
        # Check if stopped
        if not state.is_running:
            raise asyncio.CancelledError("Task stopped by user")
        
        # Use AI to generate topics dynamically
        from src.content.topic_generator import TopicGenerator
        
        # Run blocking topic generation in thread
        if niche == Niche.NEWS:
            trend_analyzer = TrendAnalyzer()
            topic = await asyncio.to_thread(trend_analyzer.select_topic)
            if topic:
                topic = f"Breaking: {topic}"
        elif niche == Niche.GENERAL or niche == Niche.TRENDING:
            trend_analyzer = TrendAnalyzer()
            topic = await asyncio.to_thread(trend_analyzer.select_topic)
        else:
            topic_gen = TopicGenerator()
            topic = await asyncio.to_thread(topic_gen.generate_topic, niche.value)
            
        await manager.broadcast({"type": "log", "data": f"Selected Topic: {topic}"})
        
        if not topic:
            raise Exception("No topic selected")

        # Check if stopped
        if not state.is_running:
            raise asyncio.CancelledError("Task stopped by user")

        # 2. Content Generation
        state.current_action = f"Generating Script for: {topic}"
        await manager.broadcast({"type": "status", "data": state.current_action})
        
        script_gen = ScriptGenerator()
        # Run blocking script generation in thread
        script = await asyncio.to_thread(script_gen.generate_script, topic, niche=niche)
        await manager.broadcast({"type": "log", "data": "Script generated."})
        
        # Check if stopped
        if not state.is_running:
            raise asyncio.CancelledError("Task stopped by user")
        
        # 3. Scene-Based Video Creation
        state.current_action = "Creating Video (Scene-Based)..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        
        from src.video.scene_based_orchestrator import SceneBasedVideoOrchestrator
        orchestrator = SceneBasedVideoOrchestrator()
        
        video_path = os.path.join(Config.ASSETS_DIR, "final_video.mp4")
        
        # Run blocking video creation in thread
        # This is the heavy lifting - definitely needs to be in a thread!
        final_video = await asyncio.to_thread(
            orchestrator.create_video,
            script=script,
            output_path=video_path,
            target_duration=60,
            niche=niche.value
        )
        
        # Check if stopped
        if not state.is_running:
            raise asyncio.CancelledError("Task stopped by user")
        
        # 4. Upload
        state.current_action = "Uploading..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        
        # Ensure auth before upload
        uploader = YouTubeUploader()
        if not uploader.youtube:
             await manager.broadcast({"type": "error", "data": "YouTube Auth failed. Please authenticate first."})
             raise Exception("Not Authenticated")

        if final_video and os.path.exists(final_video):
             description = f"An AI generated video about {topic}.\n\n#shorts #ai #facts #{niche.value}"
             tags = ["shorts", "ai", "facts", niche.value, topic.split()[0]]
             
             # UNCOMMENT TO ENABLE REAL UPLOAD
             video_id = await asyncio.to_thread(uploader.upload_video, final_video, topic, description, tags)
             await manager.broadcast({"type": "log", "data": f"Uploaded! ID: {video_id}"})
             
             # await manager.broadcast({"type": "log", "data": "Upload simulated (Safety Mode). Uncomment in api/main.py to enable."})
        else:
            logger.error("Video generation failed")
            await manager.broadcast({"type": "error", "data": "Video generation failed"})
        
        state.current_action = "Cycle Complete"
        await manager.broadcast({"type": "status", "data": state.current_action})

    except asyncio.CancelledError:
        state.current_action = "Stopped by user"
        await manager.broadcast({"type": "status", "data": state.current_action})
        await manager.broadcast({"type": "log", "data": "⚠️ Task cancelled by user"})
    except Exception as e:
        state.current_action = f"Error: {str(e)}"
        await manager.broadcast({"type": "error", "data": str(e)})
        logger.error(f"Automation cycle error: {e}", exc_info=True)
    finally:
        state.is_running = False
        state.current_task = None
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
    
    # Create and store task reference
    task = asyncio.create_task(run_automation_cycle(state.selected_niche))
    state.current_task = task
    
    return {"message": "Started"}

@app.post("/stop")
async def stop_agent():
    """Stop the running automation task."""
    if not state.is_running:
        return {"message": "Not running"}
    
    # Set flag to stop
    state.is_running = False
    
    # Cancel the task if it exists
    if state.current_task and not state.current_task.done():
        state.current_task.cancel()
        try:
            await state.current_task
        except asyncio.CancelledError:
            pass
    
    state.current_action = "Stopped"
    await manager.broadcast({"type": "status", "data": "Stopped"})
    await manager.broadcast({"type": "log", "data": "🛑 Agent stopped"})
    
    return {"message": "Stopped"}

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
