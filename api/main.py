import logging
import io
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
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
# Configure root logger to capture everything
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler("backend.log"),
                        logging.StreamHandler()
                    ])
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

# Serve Static Files
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "web", "dist")
if os.path.exists(frontend_dir):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dir, "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Allow API and WS routes to pass through
        if full_path.startswith("api") or full_path == "ws" or full_path == "status" or full_path == "start" or full_path == "stop" or full_path == "auth" or full_path == "update_config" or full_path == "order_video":
            return None # This will fall through to other routes
        
        # Check if the requested file exists in dist
        path = os.path.join(frontend_dir, full_path)
        if os.path.isfile(path):
            return FileResponse(path)
        
        # Default to index.html for SPA routing
        return FileResponse(os.path.join(frontend_dir, "index.html"))
else:
    logger.warning(f"Frontend directory not found at {frontend_dir}. UI will not be served.")

# State
class AgentState:
    is_running = False
    current_action = "Idle"
    last_log = ""
    is_authenticated = os.path.exists(os.path.join(Config.BASE_DIR, '..', 'token.pickle'))
    selected_niche = Niche.GENERAL
    schedule = [] # ["10:00", "18:00"]
    daily_short_count = 2
    daily_long_count = 1
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
    daily_short_count: int | None = None
    daily_long_count: int | None = None

class VideoOrder(BaseModel):
    niche: str
    topic: str | None = None
    orientation: str = "portrait" # "portrait" or "landscape"
    duration: int = 60
    upload: bool = True

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

async def _execute_cycle(niche: Niche, duration_type: str):
    """Core execution logic without state management"""
    state.current_action = f"Starting Cycle ({niche.value}, {duration_type})..."
    await manager.broadcast({"type": "status", "data": state.current_action})
    
    try:
        # 1. Topic Selection based on Niche
        state.current_action = "Selecting Topic..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        
        # Check if stopped
        if not state.is_running:
            raise asyncio.CancelledError("Task stopped by user")
        
        # Use AI to generate topics dynamically
        from src.content.unified_generator import UnifiedContentGenerator
        unified_gen = UnifiedContentGenerator()
        
        # Run blocking topic generation in thread
        trend_analyzer = TrendAnalyzer()
        
        content_data = None
        if niche == Niche.NEWS:
            topic = await asyncio.to_thread(trend_analyzer.select_topic)
            if topic:
                content_data = await asyncio.to_thread(unified_gen.generate_content_from_topic, topic, niche.value, duration_type)
        elif niche == Niche.GENERAL or niche == Niche.TRENDING:
            topic = await asyncio.to_thread(trend_analyzer.select_topic)
            if topic:
                content_data = await asyncio.to_thread(unified_gen.generate_content_from_topic, topic, niche.value, duration_type)
        else:
            content_data = await asyncio.to_thread(unified_gen.generate_full_content, niche.value, duration_type)
            
        if not content_data:
            raise Exception("Content generation failed")

        topic = content_data.get("topic")
        viral_title = content_data.get("title")
        script = content_data.get("script")
        pre_generated_scenes = content_data.get("scenes")

        await manager.broadcast({"type": "log", "data": f"Selected Topic: {topic}"})
        await manager.broadcast({"type": "log", "data": f"Generated Title: {viral_title}"})

        # Check if stopped
        if not state.is_running:
            raise asyncio.CancelledError("Task stopped by user")

        # 2. Content Generation
        state.current_action = f"Content Ready for: {topic}"
        await manager.broadcast({"type": "status", "data": state.current_action})
        await manager.broadcast({"type": "log", "data": "Script and scenes generated in one call."})
        
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
            target_duration=60 if duration_type == "short" else 600,
            niche=niche.value,
            stop_check=lambda: not state.is_running,
            pre_generated_scenes=pre_generated_scenes
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
             tag_type = "shorts" if duration_type == "short" else "video"
             description = f"An AI generated {tag_type} about {topic}.\n\n#{tag_type} #ai #facts #{niche.value}"
             tags = [tag_type, "ai", "facts", niche.value, topic.split()[0]]
             
             # Upload to YouTube
             logger.info(f"Uploading video: {viral_title}")
             await manager.broadcast({"type": "log", "data": "Uploading to YouTube..."})
             
             # UNCOMMENT TO ENABLE REAL UPLOAD
             video_id = await asyncio.to_thread(uploader.upload_video, final_video, viral_title, description, tags)
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
        raise # Re-raise to let caller know
    except Exception as e:
        state.current_action = f"Error: {str(e)}"
        await manager.broadcast({"type": "error", "data": str(e)})
        logger.error(f"Automation cycle error: {e}", exc_info=True)
        raise

async def run_automation_cycle(niche: Niche = Niche.GENERAL, duration_type: str = "short"):
    if state.is_running:
        logger.warning("Agent already running, skipping cycle.")
        return

    state.is_running = True
    await manager.broadcast({"type": "state", "data": {"is_running": True}})
    
    try:
        await _execute_cycle(niche, duration_type)
    except Exception:
        pass # Error already handled/logged in _execute_cycle
    finally:
        state.is_running = False
        state.current_task = None
        await manager.broadcast({"type": "state", "data": {"is_running": False}})

async def run_daily_batch_job(niche: Niche):
    """
    Runs the daily batch of videos:
    - daily_short_count x Shorts
    - daily_long_count x Long Videos
    """
    if state.is_running:
        logger.warning("Agent already running, skipping batch.")
        return

    state.is_running = True
    await manager.broadcast({"type": "state", "data": {"is_running": True}})
    
    try:
        total_videos = state.daily_short_count + state.daily_long_count
        logger.info(f"Starting daily batch: {state.daily_short_count} Shorts, {state.daily_long_count} Long Videos")
        await manager.broadcast({"type": "log", "data": f"🚀 Starting Daily Batch: {state.daily_short_count} Shorts, {state.daily_long_count} Long Videos"})
        
        # Run Shorts
        for i in range(state.daily_short_count):
            if not state.is_running: break
            logger.info(f"Batch: Generating Short {i+1}/{state.daily_short_count}")
            await manager.broadcast({"type": "log", "data": f"🎬 Batch: Generating Short {i+1}/{state.daily_short_count}"})
            try:
                await _execute_cycle(niche, "short")
                # Wait a bit between videos to avoid rate limits and let things cool down
                if i < state.daily_short_count - 1 or state.daily_long_count > 0:
                    await asyncio.sleep(60) 
            except Exception as e:
                logger.error(f"Short {i+1} failed: {e}")
                await manager.broadcast({"type": "error", "data": f"Short {i+1} failed, continuing batch..."})

        # Run Long Videos
        for i in range(state.daily_long_count):
            if not state.is_running: break
            logger.info(f"Batch: Generating Long Video {i+1}/{state.daily_long_count}")
            await manager.broadcast({"type": "log", "data": f"🎥 Batch: Generating Long Video {i+1}/{state.daily_long_count}"})
            try:
                await _execute_cycle(niche, "long")
                if i < state.daily_long_count - 1:
                    await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Long Video {i+1} failed: {e}")
                await manager.broadcast({"type": "error", "data": f"Long Video {i+1} failed, continuing batch..."})
                
        await manager.broadcast({"type": "log", "data": "✅ Daily Batch Complete!"})

    except Exception as e:
        logger.error(f"Batch failed: {e}")
        await manager.broadcast({"type": "error", "data": f"Batch failed: {e}"})
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
        "schedule": state.schedule,
        "daily_short_count": state.daily_short_count,
        "daily_long_count": state.daily_long_count
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
                # Schedule the BATCH job
                scheduler.add_job(run_daily_batch, CronTrigger(hour=hour, minute=minute), args=[state.selected_niche])
                logger.info(f"Scheduled batch job for {time_str}")
            except Exception as e:
                logger.error(f"Invalid time format {time_str}: {e}")
    
    if config.daily_short_count is not None:
        state.daily_short_count = config.daily_short_count
    if config.daily_long_count is not None:
        state.daily_long_count = config.daily_long_count
        
    return {
        "message": "Config updated", 
        "niche": state.selected_niche, 
        "schedule": state.schedule,
        "daily_short_count": state.daily_short_count,
        "daily_long_count": state.daily_long_count
    }

@app.post("/start")
async def start_agent():
    if state.is_running:
        return {"message": "Already running"}
    
    # Create and store task reference
    task = asyncio.create_task(run_automation_cycle(state.selected_niche))
    state.current_task = task
    
    return {"message": "Started"}

async def run_manual_order(order: VideoOrder):
    """
    Execute a single manual video order.
    """
    state.current_action = f"Processing Order: {order.niche} ({order.orientation})"
    await manager.broadcast({"type": "status", "data": state.current_action})
    
    try:
        # Imports
        from src.content.unified_generator import UnifiedContentGenerator
        from src.video.scene_based_orchestrator import SceneBasedVideoOrchestrator
        from src.content.thumbnail_generator import ThumbnailGenerator
        
        unified_gen = UnifiedContentGenerator()
        orchestrator = SceneBasedVideoOrchestrator()
        thumbnail_gen = ThumbnailGenerator()
        uploader = YouTubeUploader()
        
        # 1. Content Generation
        state.current_action = "Generating Content..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        
        duration_type = "short" if order.orientation == "portrait" else "long"
        duration_minutes = order.duration / 60
        
        content_data = None
        if order.topic:
            logger.info(f"Generating manual content for topic: {order.topic}")
            content_data = await asyncio.to_thread(
                unified_gen.generate_content_from_topic, 
                order.topic, 
                order.niche, 
                duration_type,
                duration_minutes
            )
        else:
            logger.info(f"Generating viral topic for niche: {order.niche}")
            content_data = await asyncio.to_thread(
                unified_gen.generate_full_content, 
                order.niche, 
                duration_type,
                duration_minutes
            )
            
        if not content_data:
            raise Exception("Content generation failed")
            
        topic = content_data.get("topic", order.topic)
        title = content_data.get("title")
        script = content_data.get("script")
        scenes = content_data.get("scenes")
        
        await manager.broadcast({"type": "log", "data": f"📝 Topic: {topic}"})
        await manager.broadcast({"type": "log", "data": f"📝 Title: {title}"})
        
        # 2. Video Creation
        state.current_action = "Creating Video..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        
        output_filename = f"manual_{order.niche}_{order.orientation}_{int(asyncio.get_event_loop().time())}.mp4"
        output_path = os.path.join(Config.ASSETS_DIR, output_filename)
        
        final_video = await asyncio.to_thread(
            orchestrator.create_video,
            script=script,
            output_path=output_path,
            target_duration=order.duration,
            niche=order.niche,
            pre_generated_scenes=scenes,
            orientation=order.orientation
        )
        
        if not final_video:
            raise Exception("Video creation failed")
            
        await manager.broadcast({"type": "log", "data": f"✅ Video Created: {output_filename}"})
        
        # 3. Thumbnail
        state.current_action = "Generating Thumbnail..."
        await manager.broadcast({"type": "status", "data": state.current_action})
        
        thumbnail_path = await asyncio.to_thread(
            thumbnail_gen.generate_thumbnail,
            topic=topic or title,
            niche=order.niche,
            viral_title=title
        )
        
        if thumbnail_path:
            await manager.broadcast({"type": "log", "data": "🖼️ Thumbnail Created"})
            
        # 4. Upload
        if order.upload:
            state.current_action = "Uploading..."
            await manager.broadcast({"type": "status", "data": state.current_action})
            
            if not uploader.youtube:
                 await manager.broadcast({"type": "error", "data": "YouTube Auth failed. Cannot upload."})
            else:
                tag_type = "shorts" if duration_type == "short" else "video"
                description = content_data.get("description", f"{title}\n\n#{tag_type} #{order.niche} #ai")
                tags = content_data.get("tags", [order.niche, "ai", tag_type])
                
                video_id = await asyncio.to_thread(
                    uploader.upload_video,
                    final_video,
                    title,
                    description,
                    tags,
                    thumbnail_path=thumbnail_path
                )
                
                if video_id:
                    await manager.broadcast({"type": "log", "data": f"🚀 Uploaded! ID: {video_id}"})
                else:
                    await manager.broadcast({"type": "error", "data": "Upload failed."})
        
        state.current_action = "Order Complete"
        await manager.broadcast({"type": "status", "data": state.current_action})
        await manager.broadcast({"type": "log", "data": "✨ Manual Order Completed Successfully!"})

    except Exception as e:
        logger.error(f"Manual order failed: {e}", exc_info=True)
        state.current_action = f"Error: {str(e)}"
        await manager.broadcast({"type": "error", "data": f"Order failed: {str(e)}"})
    finally:
        state.current_task = None

@app.post("/order_video")
async def order_video(order: VideoOrder):
    if state.is_running or state.current_task is not None:
        return {"message": "Agent is busy. Please wait.", "success": False}
        
    task = asyncio.create_task(run_manual_order(order))
    state.current_task = task
    
    return {"message": "Order received. Starting generation...", "success": True}

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
async def authenticate_youtube():
    """
    Trigger OAuth flow explicitly in background
    """
    # Always allow re-authentication if requested
    # if state.is_authenticated:
    #     return {"message": "Already authenticated", "success": True}

    token_path = os.path.join(Config.BASE_DIR, '..', 'token.pickle')
    logger.info(f"Checking token at: {token_path}")
    logger.info(f"Token exists: {os.path.exists(token_path)}")

    def run_auth():
        try:
            logger.info("Starting interactive authentication...")
            
            def auth_callback(url):
                # We need to run this async broadcast in a sync callback
                # This is tricky because we are in a thread.
                # We can put it in the log queue or use run_coroutine_threadsafe
                logger.info(f"Broadcasting Auth URL: {url}")
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast({"type": "auth_url", "data": url}),
                    loop
                )

            # This will block until user authenticates in browser
            uploader = YouTubeUploader(interactive=True, url_callback=auth_callback)
            if uploader.youtube:
                state.is_authenticated = True
                logger.info("Authentication successful!")
                return True
            return False
        except Exception as e:
            logger.error(f"Auth failed: {e}")
            return False

    # Get the running loop to schedule the broadcast
    loop = asyncio.get_running_loop()

    # Run in thread so we don't block the API
    asyncio.create_task(asyncio.to_thread(run_auth))
    
    return {"message": "Authentication started. Please check the opened browser window or click the link in the logs.", "success": True}

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
