# Dashboard Backend API Fixes

This document contains all the code changes needed to complete the dashboard backend integration.

## File 1: web_dashboard/app.py

### Changes Required:

#### 1. Add Template Context Helper Function (after line 300, before route definitions)

```python
# ============================================================================
# TEMPLATE CONTEXT HELPER
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
```

#### 2. Update Template Rendering Routes (replace existing routes)

```python
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard page"""
    try:
        return templates.TemplateResponse("dashboard.html", 
            get_template_context(request, status=bot_state.get("status", "offline")))
    except Exception as e:
        logger.error(f"Error rendering dashboard: {e}")
        # ... keep existing fallback HTML


@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Configuration page"""
    try:
        return templates.TemplateResponse("config.html", 
            get_template_context(request))
    except Exception as e:
        logger.error(f"Error rendering config page: {e}")
        # ... keep existing fallback HTML


@app.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request):
    """Logs viewer page"""
    try:
        return templates.TemplateResponse("logs.html", 
            get_template_context(request))
    except Exception as e:
        logger.error(f"Error rendering logs page: {e}")
        # ... keep existing fallback HTML
```

#### 3. Add New API Endpoints (after /api/logs endpoint, before /ws endpoint)

```python
# ============================================================================
# NEW API ENDPOINTS - Dashboard Integration
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
```

---

## File 2: bot_with_dashboard.py

### Changes Required:

#### 1. Remove Duplicate Event Handler (DELETE THIS ENTIRE BLOCK)

```python
# ❌ DELETE THIS - It conflicts with lifespan handler in app.py
@dashboard_app.on_event("startup")
async def dashboard_startup():
    """Dashboard startup event"""
    logger.info("Dashboard startup - checking for bridge...")
    # ... entire function
```

#### 2. Remove Duplicate API Endpoints (DELETE THESE ENTIRE BLOCKS)

```python
# ❌ DELETE THIS - Should be in app.py
@dashboard_app.post("/api/guild/{guild_id}/command")
async def execute_guild_command(guild_id: int, command: str, params: dict = None):
    # ... entire function

# ❌ DELETE THIS - Should be in app.py
@dashboard_app.get("/api/guild/{guild_id}/queue")
async def get_guild_queue_api(guild_id: int):
    # ... entire function

# ❌ DELETE THIS - Should be in app.py
@dashboard_app.get("/api/status/live")
async def get_live_status():
    # ... entire function

# ❌ DELETE THIS - Should be in app.py
@dashboard_app.get("/api/health/services")
async def get_services_health():
    # ... entire function
```

#### 3. Add WebSocket Manager Connection (in setup() method)

Find the `async def setup(self):` method and update it:

```python
async def setup(self):
    """Setup bot and dashboard components"""
    logger.info("Setting up integrated bot system...")
    
    # Create bot instance
    self.bot = create_bot()
    
    # Create dashboard bridge
    self.dashboard_bridge = DashboardBridge(self.bot)
    set_dashboard_bridge(self.dashboard_bridge)
    
    # ✅ ADD THIS: Connect WebSocket manager to bridge
    from web_dashboard.app import manager as websocket_manager
    self.dashboard_bridge.set_websocket_manager(websocket_manager)
    logger.info("✅ WebSocket manager connected to dashboard bridge")
    
    # Subscribe dashboard to bridge updates
    self.dashboard_bridge.subscribe(self._handle_bridge_update)
    
    # Register bot event handlers for dashboard
    self._register_bot_events()
    
    logger.info("✅ Integrated system setup complete")
```

---

## Summary of Changes

### web_dashboard/app.py
- ✅ Add `get_template_context()` helper function
- ✅ Update 3 template rendering routes to use helper
- ✅ Add 5 new API endpoints:
  - `POST /api/guild/{guild_id}/command`
  - `GET /api/guild/{guild_id}/queue/detailed`
  - `GET /api/status/live`
  - `GET /api/health/services`
  - `GET /api/queues/all`

### bot_with_dashboard.py
- ✅ Remove duplicate `@dashboard_app.on_event("startup")`
- ✅ Remove 4 duplicate API endpoint definitions
- ✅ Add `bridge.set_websocket_manager(manager)` call in setup()

---

## Testing After Changes

### 1. Test Standalone Dashboard
```bash
cd web_dashboard
python app.py
```
Expected: Dashboard starts, shows "bridge unavailable" status

### 2. Test Integrated Mode
```bash
python bot_with_dashboard.py
```
Expected: Both bot and dashboard start, dashboard shows "Connected"

### 3. Test API Endpoints
```bash
# Test health
curl http://localhost:8000/api/health/services

# Test live status
curl http://localhost:8000/api/status/live

# Test command execution (when bot is running)
curl -X POST http://localhost:8000/api/guild/123456789/command \
  -H "Content-Type: application/json" \
  -d '{"command": "pause"}'
```

### 4. Test WebSocket
- Open dashboard in browser
- Open browser console
- Should see WebSocket connection established
- Should see real-time updates when bot events occur

### 5. Test Music Controls
- Join bot to Discord server
- Play music
- Use dashboard controls (pause/resume/skip/stop)
- Verify bot responds to commands
- Verify dashboard updates in real-time

---

## Implementation Priority

1. **HIGH PRIORITY**: Add missing API endpoints to app.py
2. **HIGH PRIORITY**: Fix bot_with_dashboard.py integration
3. **MEDIUM PRIORITY**: Test all endpoints
4. **LOW PRIORITY**: Add additional features

---

## Expected Results

After implementing these changes:

✅ Dashboard will have consistent UI across all pages
✅ All API endpoints will be functional
✅ WebSocket real-time updates will work
✅ Music controls from dashboard will work
✅ Bridge integration will be complete
✅ Both standalone and integrated modes will work

---

## Files Modified

1. `web_dashboard/app.py` - Add endpoints and helper function
2. `bot_with_dashboard.py` - Remove duplicates, add WebSocket connection

## Files Already Fixed

1. ✅ `web_dashboard/templates/base.html` - Unified base template
2. ✅ `web_dashboard/templates/dashboard.html` - Refactored
3. ✅ `web_dashboard/templates/config.html` - Refactored
4. ✅ `web_dashboard/templates/logs.html` - Refactored
5. ✅ `services/dashboard_bridge.py` - Already correct
6. ✅ `cogs/music.py` - Already calling bridge notifications

---

## Completion Status

- UI/UX: 100% ✅
- Backend API: 60% → Will be 100% after these changes ✅
- Integration: 30% → Will be 100% after these changes ✅
- Testing: 0% → Needs to be done after changes ⚠️

**Total Progress: 60% → 90% (after implementation)**
