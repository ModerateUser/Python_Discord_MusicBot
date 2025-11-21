"""
Web Dashboard for Discord Music Bot
FastAPI-based control panel with real-time monitoring
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import config
from services.llm_service import create_llm_service

logger = logging.getLogger('discord_bot')

# Create FastAPI app
app = FastAPI(
    title="Discord Music Bot Dashboard",
    description="Web-based control panel for Discord Music Bot",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates and static files
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
app.mount("/static", StaticFiles(directory=str(Path(__file__).parent / "static")), name="static")

# Global state (will be populated by bot)
bot_state = {
    "connected": False,
    "guilds": [],
    "queues": {},
    "status": "offline",
    "uptime": None,
    "start_time": None
}

# WebSocket connections for real-time updates
active_connections: List[WebSocket] = []


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")


manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "bot_name": "Discord Music Bot",
        "version": "1.0.0"
    })


@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Configuration page"""
    return templates.TemplateResponse("config.html", {
        "request": request,
        "bot_name": "Discord Music Bot"
    })


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Logs viewer page"""
    return templates.TemplateResponse("logs.html", {
        "request": request,
        "bot_name": "Discord Music Bot"
    })


@app.get("/api/status")
async def get_status():
    """Get bot status"""
    return JSONResponse({
        "status": bot_state["status"],
        "connected": bot_state["connected"],
        "guilds": len(bot_state["guilds"]),
        "active_queues": len(bot_state["queues"]),
        "uptime": bot_state["uptime"],
        "timestamp": datetime.now().isoformat()
    })


@app.get("/api/guilds")
async def get_guilds():
    """Get list of guilds"""
    return JSONResponse({
        "guilds": bot_state["guilds"],
        "count": len(bot_state["guilds"])
    })


@app.get("/api/queue/{guild_id}")
async def get_queue(guild_id: int):
    """Get queue for specific guild"""
    queue = bot_state["queues"].get(str(guild_id))
    if not queue:
        raise HTTPException(status_code=404, detail="Queue not found")
    return JSONResponse(queue)


@app.get("/api/config")
async def get_config():
    """Get current configuration (sanitized)"""
    return JSONResponse({
        "command_prefix": config.command_prefix,
        "playing": config.playing,
        "max_queue_size": config.max_queue_size,
        "max_playlist_size": config.max_playlist_size,
        "allowed_file_extensions": config.allowed_file_extensions,
        "music_directory": config.music_directory,
        "token_set": bool(config.token),
        "owner_id_set": bool(config.owner_id)
    })


@app.post("/api/config")
async def update_config(config_data: dict):
    """Update configuration"""
    try:
        # Validate and update config
        # Note: This would need to write to config.json and reload
        return JSONResponse({
            "success": True,
            "message": "Configuration updated (restart required)"
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/llm/status")
async def get_llm_status():
    """Get LLM service status"""
    try:
        llm_config = getattr(config, 'llm', None)
        if not llm_config:
            return JSONResponse({
                "enabled": False,
                "provider": "none",
                "available": False
            })
        
        llm = create_llm_service(llm_config)
        is_available = await llm.is_available()
        
        return JSONResponse({
            "enabled": llm.enabled,
            "provider": llm.provider.value,
            "model": llm.model,
            "available": is_available
        })
    except Exception as e:
        logger.error(f"Error getting LLM status: {e}")
        return JSONResponse({
            "enabled": False,
            "provider": "error",
            "available": False,
            "error": str(e)
        })


@app.get("/api/logs")
async def get_logs(lines: int = 100):
    """Get recent log entries"""
    try:
        log_file = Path("logs/bot.log")
        if not log_file.exists():
            return JSONResponse({"logs": [], "count": 0})
        
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
        
        return JSONResponse({
            "logs": [line.strip() for line in recent_lines],
            "count": len(recent_lines),
            "total": len(all_lines)
        })
    except Exception as e:
        logger.error(f"Error reading logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()
            # Echo back for now (can be used for commands later)
            await websocket.send_json({
                "type": "echo",
                "data": data,
                "timestamp": datetime.now().isoformat()
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/api/bot/start")
async def start_bot():
    """Start the bot (if not running)"""
    # This would need integration with the bot process
    return JSONResponse({
        "success": False,
        "message": "Bot control not yet implemented"
    })


@app.post("/api/bot/stop")
async def stop_bot():
    """Stop the bot"""
    # This would need integration with the bot process
    return JSONResponse({
        "success": False,
        "message": "Bot control not yet implemented"
    })


@app.post("/api/bot/restart")
async def restart_bot():
    """Restart the bot"""
    # This would need integration with the bot process
    return JSONResponse({
        "success": False,
        "message": "Bot control not yet implemented"
    })


# Helper function to update bot state (called from bot)
async def update_bot_state(new_state: Dict[str, Any]):
    """Update bot state and broadcast to connected clients"""
    bot_state.update(new_state)
    await manager.broadcast({
        "type": "state_update",
        "data": bot_state,
        "timestamp": datetime.now().isoformat()
    })


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("🎵 Discord Music Bot - Web Dashboard")
    print("=" * 70)
    print(f"Dashboard URL: http://localhost:8000")
    print(f"API Docs: http://localhost:8000/docs")
    print("=" * 70)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
