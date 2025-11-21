"""
Web Dashboard for Discord Music Bot
FastAPI-based control panel with real-time monitoring

FIXES APPLIED:
- FIX GUI #1: Handle missing static directory gracefully
- FIX GUI #2: Fix import errors from config changes
- FIX GUI #3: Add proper error handling for all endpoints
- FIX GUI #4: Add bot integration support
- FIX GUI #5: Fix LLM service initialization
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
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from core.config import config
except ImportError as e:
    print(f"ERROR: Could not import config: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

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

# Templates directory
templates_dir = Path(__file__).parent / "templates"
if not templates_dir.exists():
    print(f"ERROR: Templates directory not found: {templates_dir}")
    print("Creating templates directory...")
    templates_dir.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=str(templates_dir))

# FIX GUI #1: Only mount static directory if it exists
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    logger.info(f"Mounted static directory: {static_dir}")
else:
    logger.warning(f"Static directory not found: {static_dir}")
    logger.info("Creating static directory for future use...")
    static_dir.mkdir(parents=True, exist_ok=True)
    # Create a basic CSS file
    css_dir = static_dir / "css"
    css_dir.mkdir(exist_ok=True)
    with open(css_dir / "style.css", "w") as f:
        f.write("""
/* Discord Music Bot Dashboard Styles */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    margin: 0;
    padding: 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #333;
}

.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 20px;
}

.header {
    background: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.card {
    background: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    margin-bottom: 20px;
}

.status-online {
    color: #10b981;
    font-weight: bold;
}

.status-offline {
    color: #ef4444;
    font-weight: bold;
}

button {
    background: #667eea;
    color: white;
    border: none;
    padding: 10px 20px;
    border-radius: 5px;
    cursor: pointer;
    font-size: 16px;
}

button:hover {
    background: #5568d3;
}
""")
    logger.info("Created basic static files")

# Global state (will be populated by bot)
bot_state = {
    "connected": False,
    "guilds": [],
    "queues": {},
    "status": "offline",
    "uptime": None,
    "start_time": None,
    "version": "1.0.0"
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
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    try:
        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "bot_name": "Discord Music Bot",
            "version": bot_state.get("version", "1.0.0"),
            "status": bot_state.get("status", "offline")
        })
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Dashboard Error</title></head>
                <body>
                    <h1>Dashboard Error</h1>
                    <p>Could not load dashboard template: {str(e)}</p>
                    <p>Please ensure templates/dashboard.html exists</p>
                    <a href="/api/status">View API Status</a>
                </body>
            </html>
            """,
            status_code=500
        )


@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Configuration page"""
    try:
        return templates.TemplateResponse("config.html", {
            "request": request,
            "bot_name": "Discord Music Bot"
        })
    except Exception as e:
        logger.error(f"Error rendering config page: {e}")
        # FIX GUI #3: Provide fallback HTML
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Configuration</title></head>
                <body>
                    <h1>Configuration</h1>
                    <p>Template not found. Use <a href="/api/config">API endpoint</a> instead.</p>
                    <a href="/">Back to Dashboard</a>
                </body>
            </html>
            """,
            status_code=200
        )


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Logs viewer page"""
    try:
        return templates.TemplateResponse("logs.html", {
            "request": request,
            "bot_name": "Discord Music Bot"
        })
    except Exception as e:
        logger.error(f"Error rendering logs page: {e}")
        # FIX GUI #3: Provide fallback HTML
        return HTMLResponse(
            content=f"""
            <html>
                <head><title>Logs</title></head>
                <body>
                    <h1>Logs</h1>
                    <p>Template not found. Use <a href="/api/logs">API endpoint</a> instead.</p>
                    <a href="/">Back to Dashboard</a>
                </body>
            </html>
            """,
            status_code=200
        )


@app.get("/api/status")
async def get_status():
    """Get bot status"""
    try:
        uptime_str = None
        if bot_state.get("start_time"):
            uptime_seconds = (datetime.now() - bot_state["start_time"]).total_seconds()
            hours = int(uptime_seconds // 3600)
            minutes = int((uptime_seconds % 3600) // 60)
            uptime_str = f"{hours}h {minutes}m"
        
        return JSONResponse({
            "status": bot_state.get("status", "offline"),
            "connected": bot_state.get("connected", False),
            "guilds": len(bot_state.get("guilds", [])),
            "active_queues": len(bot_state.get("queues", {})),
            "uptime": uptime_str,
            "timestamp": datetime.now().isoformat(),
            "version": bot_state.get("version", "1.0.0")
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/guilds")
async def get_guilds():
    """Get list of guilds"""
    try:
        guilds = bot_state.get("guilds", [])
        return JSONResponse({
            "guilds": guilds,
            "count": len(guilds)
        })
    except Exception as e:
        logger.error(f"Error getting guilds: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/queue/{guild_id}")
async def get_queue(guild_id: int):
    """Get queue for specific guild"""
    try:
        queue = bot_state.get("queues", {}).get(str(guild_id))
        if not queue:
            raise HTTPException(status_code=404, detail="Queue not found")
        return JSONResponse(queue)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting queue for guild {guild_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/config")
async def get_config():
    """Get current configuration (sanitized)"""
    try:
        # FIX GUI #2: Handle config attributes safely
        config_data = {
            "command_prefix": getattr(config, 'command_prefix', '!'),
            "playing": getattr(config, 'playing', '!help for commands'),
            "max_queue_size": getattr(config, 'max_queue_size', 100),
            "max_playlist_size": getattr(config, 'max_playlist_size', 500),
            "allowed_file_extensions": getattr(config, 'allowed_file_extensions', []),
            "music_directory": getattr(config, 'music_directory', None),
            "token_set": bool(getattr(config, 'token', None)),
            "owner_id_set": bool(getattr(config, 'owner_id', None))
        }
        
        # Add LLM config if available
        llm_config = getattr(config, 'llm', None)
        if llm_config:
            config_data["llm"] = {
                "enabled": llm_config.get('enabled', False),
                "provider": llm_config.get('provider', 'none'),
                "model": llm_config.get('model', 'none')
            }
        
        # Add music synthesis config if available
        synthesis_config = getattr(config, 'music_synthesis', None)
        if synthesis_config:
            config_data["music_synthesis"] = {
                "enabled": synthesis_config.get('enabled', False),
                "backend": synthesis_config.get('backend', 'disabled')
            }
        
        return JSONResponse(config_data)
    except Exception as e:
        logger.error(f"Error getting config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config")
async def update_config(config_data: dict):
    """Update configuration"""
    try:
        # FIX GUI #3: Add validation
        if not config_data:
            raise HTTPException(status_code=400, detail="No configuration data provided")
        
        # TODO: Implement config update logic
        # This would need to write to config.json and reload
        return JSONResponse({
            "success": False,
            "message": "Configuration update not yet implemented (requires bot restart)"
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/llm/status")
async def get_llm_status():
    """Get LLM service status"""
    try:
        # FIX GUI #5: Handle LLM service safely
        llm_config = getattr(config, 'llm', None)
        if not llm_config:
            return JSONResponse({
                "enabled": False,
                "provider": "none",
                "available": False,
                "message": "LLM not configured"
            })
        
        # Try to import and check LLM service
        try:
            from services.llm_service import LLMService
            
            # Create LLM service instance
            llm = LLMService(llm_config)
            is_available = await llm.is_available()
            
            return JSONResponse({
                "enabled": llm.enabled,
                "provider": llm.provider.value if hasattr(llm.provider, 'value') else str(llm.provider),
                "model": llm.model,
                "available": is_available
            })
        except ImportError as e:
            logger.warning(f"LLM service not available: {e}")
            return JSONResponse({
                "enabled": False,
                "provider": "error",
                "available": False,
                "error": "LLM service module not found"
            })
        except Exception as e:
            logger.error(f"Error checking LLM status: {e}", exc_info=True)
            return JSONResponse({
                "enabled": False,
                "provider": "error",
                "available": False,
                "error": str(e)
            })
    except Exception as e:
        logger.error(f"Error in LLM status endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs")
async def get_logs(lines: int = 100):
    """Get recent log entries"""
    try:
        # FIX GUI #3: Validate input
        if lines < 1 or lines > 10000:
            raise HTTPException(status_code=400, detail="Lines must be between 1 and 10000")
        
        log_file = Path("logs/bot.log")
        if not log_file.exists():
            return JSONResponse({
                "logs": [],
                "count": 0,
                "message": "Log file not found"
            })
        
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:]
        
        return JSONResponse({
            "logs": [line.strip() for line in recent_lines],
            "count": len(recent_lines),
            "total": len(all_lines)
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading logs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        # Send initial state
        await websocket.send_json({
            "type": "initial_state",
            "data": bot_state,
            "timestamp": datetime.now().isoformat()
        })
        
        while True:
            # Keep connection alive and receive messages
            data = await websocket.receive_text()
            
            # Parse command
            try:
                command = json.loads(data)
                command_type = command.get("type")
                
                if command_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                elif command_type == "get_status":
                    await websocket.send_json({
                        "type": "status",
                        "data": bot_state,
                        "timestamp": datetime.now().isoformat()
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "message": f"Unknown command type: {command_type}",
                        "timestamp": datetime.now().isoformat()
                    })
            except json.JSONDecodeError:
                # Echo back for non-JSON messages
                await websocket.send_json({
                    "type": "echo",
                    "data": data,
                    "timestamp": datetime.now().isoformat()
                })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}", exc_info=True)
        manager.disconnect(websocket)


@app.post("/api/bot/start")
async def start_bot():
    """Start the bot (if not running)"""
    # FIX GUI #4: This would need integration with the bot process
    return JSONResponse({
        "success": False,
        "message": "Bot control requires integration with bot process (not yet implemented)"
    })


@app.post("/api/bot/stop")
async def stop_bot():
    """Stop the bot"""
    # FIX GUI #4: This would need integration with the bot process
    return JSONResponse({
        "success": False,
        "message": "Bot control requires integration with bot process (not yet implemented)"
    })


@app.post("/api/bot/restart")
async def restart_bot():
    """Restart the bot"""
    # FIX GUI #4: This would need integration with bot process
    return JSONResponse({
        "success": False,
        "message": "Bot control requires integration with bot process (not yet implemented)"
    })


# FIX GUI #4: Helper function to update bot state (called from bot)
async def update_bot_state(new_state: Dict[str, Any]):
    """Update bot state and broadcast to connected clients"""
    try:
        bot_state.update(new_state)
        await manager.broadcast({
            "type": "state_update",
            "data": bot_state,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error updating bot state: {e}", exc_info=True)


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bot_connected": bot_state.get("connected", False)
    })


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("Web Dashboard starting up...")
    logger.info(f"Templates directory: {templates_dir}")
    logger.info(f"Static directory: {static_dir}")
    
    # Set initial state
    bot_state["start_time"] = datetime.now()
    bot_state["status"] = "dashboard_online"


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Web Dashboard shutting down...")
    
    # Disconnect all WebSocket clients
    for connection in manager.active_connections[:]:
        try:
            await connection.close()
        except:
            pass
    manager.active_connections.clear()


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("🎵 Discord Music Bot - Web Dashboard")
    print("=" * 70)
    print(f"Dashboard URL: http://localhost:8000")
    print(f"API Docs: http://localhost:8000/docs")
    print(f"Health Check: http://localhost:8000/health")
    print("=" * 70)
    print()
    print("Note: The dashboard runs independently of the bot.")
    print("To integrate with the bot, run both bot.py and this dashboard.")
    print()
    print("=" * 70)
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\nDashboard stopped by user")
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
