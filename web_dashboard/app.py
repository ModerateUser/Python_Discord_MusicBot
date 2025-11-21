"""
Web Dashboard for Discord Music Bot
FastAPI-based control panel with real-time monitoring

FIXES APPLIED:
- FIX GUI #1: Handle missing static directory gracefully
- FIX GUI #2: Fix import errors from config changes
- FIX GUI #3: Add proper error handling for all endpoints
- FIX GUI #4: Add bot integration support
- FIX GUI #5: Fix LLM service initialization
- FIX WEBUI #1: Fix config import to handle missing/malformed config gracefully
- FIX WEBUI #2: Replace deprecated on_event with modern lifespan handler
- FIX WEBUI #5: Integrate with dashboard bridge for real-time bot data
- FIX BACKEND #1: Add template context helper function
- FIX BACKEND #2: Add missing API endpoints for dashboard integration
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
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

# FIX WEBUI #1: Import config safely without triggering validation
config = None
config_error = None

try:
    # Import Config class but don't instantiate yet
    from core.config import Config, ConfigurationError
    
    # Try to load config without validation (for WebUI display purposes)
    try:
        config = Config(validate=False)
        # Try to load the config file
        config.load()
    except ConfigurationError as e:
        config_error = str(e)
        logging.warning(f"Config validation failed (WebUI will run in limited mode): {e}")
        # Create a minimal config for WebUI to function
        config = type('MinimalConfig', (), {
            'command_prefix': '!',
            'playing': '!help for commands',
            'max_queue_size': 100,
            'max_playlist_size': 500,
            'allowed_file_extensions': ['.mp3', '.wav', '.flac', '.ogg'],
            'music_directory': None,
            'token': None,
            'owner_id': None,
            'llm': {'enabled': False},
            'music_synthesis': {'enabled': False}
        })()
    except FileNotFoundError:
        config_error = "Config file not found. Please create config.json"
        logging.warning("Config file not found - WebUI running in limited mode")
        # Create a minimal config
        config = type('MinimalConfig', (), {
            'command_prefix': '!',
            'playing': '!help for commands',
            'max_queue_size': 100,
            'max_playlist_size': 500,
            'allowed_file_extensions': ['.mp3', '.wav', '.flac', '.ogg'],
            'music_directory': None,
            'token': None,
            'owner_id': None,
            'llm': {'enabled': False},
            'music_synthesis': {'enabled': False}
        })()
    except Exception as e:
        config_error = f"Unexpected config error: {e}"
        logging.error(f"Unexpected error loading config: {e}", exc_info=True)
        # Create a minimal config
        config = type('MinimalConfig', (), {
            'command_prefix': '!',
            'playing': '!help for commands',
            'max_queue_size': 100,
            'max_playlist_size': 500,
            'allowed_file_extensions': ['.mp3', '.wav', '.flac', '.ogg'],
            'music_directory': None,
            'token': None,
            'owner_id': None,
            'llm': {'enabled': False},
            'music_synthesis': {'enabled': False}
        })()
        
except ImportError as e:
    config_error = f"Could not import config module: {e}"
    print(f"ERROR: {config_error}")
    print("Make sure you're running from the project root directory")
    # Create a minimal config to allow WebUI to start
    config = type('MinimalConfig', (), {
        'command_prefix': '!',
        'playing': '!help for commands',
        'max_queue_size': 100,
        'max_playlist_size': 500,
        'allowed_file_extensions': ['.mp3', '.wav', '.flac', '.ogg'],
        'music_directory': None,
        'token': None,
        'owner_id': None,
        'llm': {'enabled': False},
        'music_synthesis': {'enabled': False}
    })()

logger = logging.getLogger('discord_bot')

# Global state (will be populated by bot)
bot_state = {
    "connected": False,
    "guilds": [],
    "queues": {},
    "status": "offline",
    "uptime": None,
    "start_time": None,
    "version": "1.0.0",
    "config_error": config_error,  # FIX WEBUI #1: Track config errors
    "bridge_connected": False  # FIX WEBUI #5: Track bridge connection
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
        
        # FIX WEBUI #5: Send initial state when client connects
        await self.send_initial_state(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_initial_state(self, websocket: WebSocket):
        """Send initial state to newly connected client"""
        try:
            # Get current state from bridge if available
            bridge = get_dashboard_bridge()
            if bridge:
                status = await bridge.get_bot_status()
                bot_state.update(status.to_dict())
                bot_state['bridge_connected'] = True
                
                # Get all queues
                queues = await bridge.get_all_queues()
                bot_state['queues'] = {
                    str(q.guild_id): q.to_dict() for q in queues
                }
            
            await websocket.send_json({
                "type": "initial_state",
                "data": bot_state,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error sending initial state: {e}")
    
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


# FIX WEBUI #5: Import dashboard bridge
try:
    from services.dashboard_bridge import get_dashboard_bridge
except ImportError:
    logger.warning("Dashboard bridge not available - running in standalone mode")
    def get_dashboard_bridge():
        return None


# FIX WEBUI #2: Modern lifespan event handler (replaces deprecated on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Modern lifespan event handler for FastAPI
    Replaces deprecated @app.on_event("startup") and @app.on_event("shutdown")
    """
    # Startup
    logger.info("Web Dashboard starting up...")
    logger.info(f"Templates directory: {templates_dir}")
    logger.info(f"Static directory: {static_dir}")
    
    if config_error:
        logger.warning(f"Dashboard started with config error: {config_error}")
    
    bot_state["start_time"] = datetime.now()
    bot_state["status"] = "dashboard_online"
    
    # FIX WEBUI #5: Check for dashboard bridge
    bridge = get_dashboard_bridge()
    if bridge:
        logger.info("✅ Dashboard connected to bot bridge")
        bot_state["bridge_connected"] = True
        
        # Subscribe to bridge updates
        async def handle_bridge_update(message: dict):
            """Handle updates from dashboard bridge"""
            try:
                # Update bot_state based on message type
                if message['type'] == 'status_update':
                    bot_state.update(message['data'])
                elif message['type'] == 'guild_join':
                    # Add new guild to list
                    guild_data = message['data']
                    bot_state['guilds'].append({
                        "id": guild_data['guild_id'],
                        "name": guild_data['guild_name'],
                        "member_count": guild_data['member_count']
                    })
                elif message['type'] == 'guild_remove':
                    # Remove guild from list
                    guild_id = message['data']['guild_id']
                    bot_state['guilds'] = [g for g in bot_state['guilds'] if g['id'] != guild_id]
                elif message['type'] == 'queue_update':
                    # Update queue for guild
                    guild_id = str(message['data']['guild_id'])
                    queue_info = await bridge.get_guild_queue(int(guild_id))
                    if queue_info:
                        bot_state['queues'][guild_id] = queue_info.to_dict()
                    elif guild_id in bot_state['queues']:
                        del bot_state['queues'][guild_id]
                
                # Broadcast to WebSocket clients
                await manager.broadcast(message)
                
            except Exception as e:
                logger.error(f"Error handling bridge update: {e}", exc_info=True)
        
        bridge.subscribe(handle_bridge_update)
        
        # Get initial state
        try:
            status = await bridge.get_bot_status()
            bot_state.update(status.to_dict())
            
            # Get all queues
            queues = await bridge.get_all_queues()
            bot_state['queues'] = {
                str(q.guild_id): q.to_dict() for q in queues
            }
        except Exception as e:
            logger.error(f"Error getting initial state from bridge: {e}")
    else:
        logger.warning("⚠️ Dashboard running without bot bridge (standalone mode)")
        bot_state["bridge_connected"] = False
    
    yield  # Application runs here
    
    # Shutdown
    logger.info("Web Dashboard shutting down...")
    
    for connection in manager.active_connections[:]:
        try:
            await connection.close()
        except:
            pass
    manager.active_connections.clear()


# Create FastAPI app with lifespan handler
app = FastAPI(
    title="Discord Music Bot Dashboard",
    description="Web-based control panel for Discord Music Bot",
    version="1.0.0",
    lifespan=lifespan  # FIX WEBUI #2: Use modern lifespan handler
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
    print(f"Creating templates directory: {templates_dir}")
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

.error {
    background: #fee;
    border: 1px solid #fcc;
    padding: 10px;
    border-radius: 5px;
    color: #c00;
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


# ============================================================================
# FIX BACKEND #1: TEMPLATE CONTEXT HELPER
# ============================================================================

def get_template_context(request: Request, **kwargs):
    """Get standard template context for all pages"""
    return {
        "request": request,
        "bot_name": "Discord Music Bot",
        "version": bot_state.get("version", "1.0.0"),
        "config_error": config_error,
        "bridge_connected": bot_state.get("bridge_connected", False),
        **kwargs
    }


# ============================================================================
# TEMPLATE RENDERING ROUTES (Updated to use helper)
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    try:
        return templates.TemplateResponse("dashboard.html", 
            get_template_context(request, status=bot_state.get("status", "offline")))
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Discord Music Bot Dashboard</title>
                    <style>
                        body {{
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            margin: 0;
                            padding: 20px;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        }}
                        .container {{
                            max-width: 800px;
                            margin: 0 auto;
                            background: white;
                            padding: 30px;
                            border-radius: 10px;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        }}
                        .error {{
                            background: #fee;
                            border: 1px solid #fcc;
                            padding: 15px;
                            border-radius: 5px;
                            color: #c00;
                            margin: 20px 0;
                        }}
                        .info {{
                            background: #eff;
                            border: 1px solid #cef;
                            padding: 15px;
                            border-radius: 5px;
                            color: #06c;
                            margin: 20px 0;
                        }}
                        h1 {{ color: #667eea; }}
                        a {{ color: #667eea; text-decoration: none; }}
                        a:hover {{ text-decoration: underline; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>🎵 Discord Music Bot Dashboard</h1>
                        
                        {'<div class="error"><strong>⚠️ Configuration Error:</strong><br>' + config_error + '</div>' if config_error else ''}
                        
                        <div class="info">
                            <strong>Dashboard Status:</strong> Online<br>
                            <strong>Bot Status:</strong> {bot_state.get("status", "offline")}<br>
                            <strong>Bridge Connected:</strong> {'Yes' if bot_state.get("bridge_connected") else 'No'}<br>
                            <strong>Version:</strong> {bot_state.get("version", "1.0.0")}
                        </div>
                        
                        <h2>Quick Links</h2>
                        <ul>
                            <li><a href="/api/status">API Status</a></li>
                            <li><a href="/api/config">Configuration</a></li>
                            <li><a href="/health">Health Check</a></li>
                            <li><a href="/docs">API Documentation</a></li>
                        </ul>
                        
                        <h2>Setup Instructions</h2>
                        <ol>
                            <li>Create a <code>config.json</code> file in the project root</li>
                            <li>Add your Discord bot token and owner ID</li>
                            <li>Run <code>python bot_with_dashboard.py</code> for integrated mode</li>
                        </ol>
                        
                        <p><a href="/api/config">View current configuration →</a></p>
                    </div>
                </body>
            </html>
            """,
            status_code=200
        )


@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Configuration page"""
    try:
        return templates.TemplateResponse("config.html", 
            get_template_context(request))
    except Exception as e:
        logger.error(f"Error rendering config page: {e}")
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
                <head>
                    <title>Configuration - Discord Music Bot</title>
                    <style>
                        body {{
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            margin: 0;
                            padding: 20px;
                            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        }}
                        .container {{
                            max-width: 800px;
                            margin: 0 auto;
                            background: white;
                            padding: 30px;
                            border-radius: 10px;
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        }}
                        h1 {{ color: #667eea; }}
                        a {{ color: #667eea; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <h1>Configuration</h1>
                        <p>Use the <a href="/api/config">API endpoint</a> to view configuration.</p>
                        <p><a href="/">← Back to Dashboard</a></p>
                    </div>
                </body>
            </html>
            """,
            status_code=200
        )


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Logs viewer page"""
    try:
        return templates.TemplateResponse("logs.html", 
            get_template_context(request))
    except Exception as e:
        logger.error(f"Error rendering logs page: {e}")
        return HTMLResponse(
            content=f"""
            <!DOCTYPE html>
            <html>
                <head><title>Logs - Discord Music Bot</title></head>
                <body>
                    <h1>Logs</h1>
                    <p>Use the <a href="/api/logs">API endpoint</a> to view logs.</p>
                    <p><a href="/">← Back to Dashboard</a></p>
                </body>
            </html>
            """,
            status_code=200
        )


# ============================================================================
# EXISTING API ENDPOINTS
# ============================================================================

@app.get("/api/status")
async def get_status():
    """Get bot status"""
    try:
        # FIX WEBUI #5: Get live status from bridge if available
        bridge = get_dashboard_bridge()
        if bridge:
            status = await bridge.get_bot_status()
            return JSONResponse(status.to_dict())
        
        # Fallback to cached state
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
            "version": bot_state.get("version", "1.0.0"),
            "config_error": config_error,  # FIX WEBUI #1: Include config error in status
            "bridge_connected": bot_state.get("bridge_connected", False)  # FIX WEBUI #5
        })
    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/guilds")
async def get_guilds():
    """Get list of guilds"""
    try:
        # FIX WEBUI #5: Get from bridge if available
        bridge = get_dashboard_bridge()
        if bridge:
            status = await bridge.get_bot_status()
            guilds = status.guilds
        else:
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
        # FIX WEBUI #5: Get from bridge if available
        bridge = get_dashboard_bridge()
        if bridge:
            queue_info = await bridge.get_guild_queue(guild_id)
            if queue_info:
                return JSONResponse(queue_info.to_dict())
        
        # Fallback to cached state
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
        # FIX WEBUI #1: Handle config safely
        if config is None:
            return JSONResponse({
                "error": "Configuration not loaded",
                "config_error": config_error
            })
        
        # FIX GUI #2: Handle config attributes safely
        config_data = {
            "command_prefix": getattr(config, 'command_prefix', '!'),
            "playing": getattr(config, 'playing', '!help for commands'),
            "max_queue_size": getattr(config, 'max_queue_size', 100),
            "max_playlist_size": getattr(config, 'max_playlist_size', 500),
            "allowed_file_extensions": getattr(config, 'allowed_file_extensions', []),
            "music_directory": getattr(config, 'music_directory', None),
            "token_set": bool(getattr(config, 'token', None)),
            "owner_id_set": bool(getattr(config, 'owner_id', None)),
            "config_error": config_error  # FIX WEBUI #1: Include error info
        }
        
        # Add LLM config if available
        llm_config = getattr(config, 'llm', None)
        if llm_config:
            config_data["llm"] = {
                "enabled": llm_config.get('enabled', False) if isinstance(llm_config, dict) else False,
                "provider": llm_config.get('provider', 'none') if isinstance(llm_config, dict) else 'none',
                "model": llm_config.get('model', 'none') if isinstance(llm_config, dict) else 'none'
            }
        
        # Add music synthesis config if available
        synthesis_config = getattr(config, 'music_synthesis', None)
        if synthesis_config:
            config_data["music_synthesis"] = {
                "enabled": synthesis_config.get('enabled', False) if isinstance(synthesis_config, dict) else False,
                "backend": synthesis_config.get('backend', 'disabled') if isinstance(synthesis_config, dict) else 'disabled'
            }
        
        return JSONResponse(config_data)
    except Exception as e:
        logger.error(f"Error getting config: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config")
async def update_config(config_data: dict):
    """Update configuration"""
    try:
        if not config_data:
            raise HTTPException(status_code=400, detail="No configuration data provided")
        
        # TODO: Implement config update logic
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
        # FIX WEBUI #5: Get from bridge if available
        bridge = get_dashboard_bridge()
        if bridge:
            health = await bridge.get_service_health()
            llm_available = health.get('llm_service', False)
            
            if llm_available:
                return JSONResponse({
                    "enabled": True,
                    "provider": "configured",
                    "available": True,
                    "message": "LLM service is operational"
                })
        
        # Fallback to config check
        llm_config = getattr(config, 'llm', None)
        if not llm_config:
            return JSONResponse({
                "enabled": False,
                "provider": "none",
                "available": False,
                "message": "LLM not configured"
            })
        
        return JSONResponse({
            "enabled": llm_config.get('enabled', False),
            "provider": llm_config.get('provider', 'none'),
            "available": False,
            "message": "LLM status unknown (no bridge connection)"
        })
    except Exception as e:
        logger.error(f"Error in LLM status endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs")
async def get_logs(lines: int = 100):
    """Get recent log entries"""
    try:
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


# ============================================================================
# FIX BACKEND #2: NEW API ENDPOINTS - Dashboard Integration
# ============================================================================

@app.post("/api/guild/{guild_id}/command")
async def execute_guild_command(guild_id: int, command: str, params: dict = None):
    """
    Execute music command from dashboard
    
    Commands:
    - pause: Pause current track
    - resume: Resume paused track
    - skip: Skip current track
    - stop: Stop playback and clear queue
    - volume: Set volume (requires params={'volume': 0-100})
    - loop: Toggle loop mode
    """
    try:
        bridge = get_dashboard_bridge()
        if not bridge:
            raise HTTPException(status_code=503, detail="Bot bridge not available")
        
        result = await bridge.execute_command(guild_id, command, **(params or {}))
        
        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error', 'Command failed'))
        
        return JSONResponse(result)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing command {command} for guild {guild_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/guild/{guild_id}/queue/detailed")
async def get_guild_queue_detailed(guild_id: int):
    """Get detailed queue information for specific guild"""
    try:
        bridge = get_dashboard_bridge()
        if not bridge:
            raise HTTPException(status_code=503, detail="Bot bridge not available")
        
        queue_info = await bridge.get_guild_queue(guild_id)
        
        if not queue_info:
            raise HTTPException(status_code=404, detail="Queue not found or bot not in voice channel")
        
        return JSONResponse(queue_info.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting detailed queue for guild {guild_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status/live")
async def get_live_bot_status():
    """Get real-time bot status directly from bridge"""
    try:
        bridge = get_dashboard_bridge()
        
        if not bridge:
            return JSONResponse({
                "connected": False,
                "status": "bridge_unavailable",
                "message": "Dashboard running in standalone mode",
                "timestamp": datetime.now().isoformat()
            })
        
        status = await bridge.get_bot_status()
        return JSONResponse(status.to_dict())
    except Exception as e:
        logger.error(f"Error getting live status: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/health/services")
async def get_all_services_health():
    """Get health status of all services (bot, bridge, dashboard)"""
    try:
        bridge = get_dashboard_bridge()
        
        if not bridge:
            return JSONResponse({
                "dashboard": True,
                "bridge": False,
                "bot": False,
                "message": "Dashboard running in standalone mode"
            })
        
        health = await bridge.get_service_health()
        health["dashboard"] = True  # Dashboard is always healthy if responding
        
        return JSONResponse(health)
    except Exception as e:
        logger.error(f"Error getting service health: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/queues/all")
async def get_all_queues():
    """Get all active queues across all guilds"""
    try:
        bridge = get_dashboard_bridge()
        
        if not bridge:
            return JSONResponse({
                "queues": [],
                "count": 0,
                "message": "Bridge not available"
            })
        
        queues = await bridge.get_all_queues()
        
        return JSONResponse({
            "queues": [q.to_dict() for q in queues],
            "count": len(queues)
        })
    except Exception as e:
        logger.error(f"Error getting all queues: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WEBSOCKET ENDPOINT
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            
            try:
                command = json.loads(data)
                command_type = command.get("type")
                
                if command_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                elif command_type == "get_status":
                    # FIX WEBUI #5: Get live status
                    bridge = get_dashboard_bridge()
                    if bridge:
                        status = await bridge.get_bot_status()
                        await websocket.send_json({
                            "type": "status",
                            "data": status.to_dict(),
                            "timestamp": datetime.now().isoformat()
                        })
                    else:
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


# ============================================================================
# BOT CONTROL ENDPOINTS
# ============================================================================

@app.post("/api/bot/start")
async def start_bot():
    """Start the bot (if not running)"""
    return JSONResponse({
        "success": False,
        "message": "Bot control through integrated launcher only. Use bot_with_dashboard.py"
    })


@app.post("/api/bot/stop")
async def stop_bot():
    """Stop the bot"""
    return JSONResponse({
        "success": False,
        "message": "Bot control through integrated launcher only. Use bot_with_dashboard.py"
    })


@app.post("/api/bot/restart")
async def restart_bot():
    """Restart the bot"""
    return JSONResponse({
        "success": False,
        "message": "Bot control through integrated launcher only. Use bot_with_dashboard.py"
    })


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

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


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    # FIX WEBUI #5: Check bridge health
    bridge = get_dashboard_bridge()
    bridge_healthy = False
    bot_connected = False
    
    if bridge:
        try:
            health = await bridge.get_service_health()
            bridge_healthy = health.get('dashboard_bridge', False)
            bot_connected = health.get('bot', False)
        except:
            pass
    
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bot_connected": bot_connected,
        "bridge_connected": bridge_healthy,
        "config_loaded": config is not None,
        "config_error": config_error
    })


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("🎵 Discord Music Bot - Web Dashboard")
    print("=" * 70)
    print(f"Dashboard URL: http://localhost:8000")
    print(f"API Docs: http://localhost:8000/docs")
    print(f"Health Check: http://localhost:8000/health")
    print("=" * 70)
    
    if config_error:
        print()
        print("⚠️  WARNING: Configuration Error Detected")
        print(f"   {config_error}")
        print("   Dashboard will run in limited mode.")
        print()
    
    print("NOTE: For integrated bot+dashboard, run: python bot_with_dashboard.py")
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
