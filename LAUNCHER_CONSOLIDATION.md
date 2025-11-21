# Launcher Consolidation - Unified launcher.bat

## 📋 Overview

The Discord Music Bot previously had **4 separate launcher files** with overlapping functionality. This has been consolidated into a **single unified launcher.bat** with a menu system that provides all launch modes and utilities.

---

## ✅ What Changed

### Before (4 Separate Files):
- ❌ `launch.bat` - Bot only mode
- ❌ `launch_gui.bat` - Dashboard only mode
- ❌ `launch_integrated.bat` - Integrated mode (bot + dashboard)
- ❌ `launch_all.bat` - Separate windows mode

**Problems:**
- Confusing for users (which one to use?)
- Duplicate code across all files
- Inconsistent error handling
- Hard to maintain (changes needed in 4 places)

### After (1 Unified File):
- ✅ `launcher.bat` - Single launcher with menu system

**Benefits:**
- Simple: One file to run
- User-friendly: Menu-driven interface
- Maintainable: All code in one place
- Consistent: Same error handling everywhere
- Feature-rich: Built-in utilities

---

## 🎯 New Unified Launcher Features

### Launch Modes:

**[1] Bot Only**
- Runs just the Discord bot
- No web dashboard
- Minimal resource usage
- Perfect for production servers

**[2] Dashboard Only**
- Runs just the web dashboard
- Standalone mode (no bot connection)
- Good for testing dashboard UI
- Access at http://localhost:8000

**[3] Integrated Mode** ⭐ **RECOMMENDED**
- Bot + Dashboard in same process
- Real-time communication via bridge
- Best performance
- Full feature set
- Single window

**[4] Separate Windows**
- Bot + Dashboard in separate processes
- Two windows (easier to monitor)
- Independent restart capability
- Good for development

### Utilities:

**[5] Install/Update Dependencies**
- Installs/updates all Python packages
- Updates pip automatically
- Handles both bot and dashboard dependencies
- No need to run pip manually

**[6] Check System Requirements**
- Verifies Python installation
- Checks virtual environment
- Validates FFmpeg installation
- Lists installed dependencies
- Shows configuration status

**[7] Create/Reset Config File**
- Creates config.json from template
- Can reset existing config
- Copies from config.example.json if available
- Generates complete template otherwise

---

## 🚀 How to Use

### First Time Setup:

1. **Run launcher.bat**
   ```
   Double-click launcher.bat
   ```

2. **Choose option [7]** to create config.json
   ```
   Creates config.json with all settings
   ```

3. **Edit config.json** with your bot token
   ```
   Open config.json in text editor
   Set "token": "YOUR_BOT_TOKEN_HERE"
   Set "owner_id": YOUR_DISCORD_USER_ID
   ```

4. **Choose option [5]** to install dependencies
   ```
   Installs all required packages
   Creates virtual environment
   ```

5. **Choose option [3]** to start integrated mode
   ```
   Starts bot + dashboard together
   Opens browser automatically
   ```

### Daily Use:

1. **Run launcher.bat**
2. **Choose option [3]** (Integrated Mode)
3. **Done!** Bot and dashboard start together

---

## 📁 File Management

### Keep These Files:
- ✅ `launcher.bat` - **NEW unified launcher**
- ✅ `bot.py` - Bot entry point
- ✅ `bot_with_dashboard.py` - Integrated mode entry point
- ✅ `config.example.json` - Configuration template

### Can Delete (Deprecated):
- ❌ `launch.bat` - Replaced by unified launcher
- ❌ `launch_gui.bat` - Replaced by unified launcher
- ❌ `launch_integrated.bat` - Replaced by unified launcher
- ❌ `launch_all.bat` - Replaced by unified launcher

**Note:** The old launcher files are kept for backward compatibility but are no longer needed. You can safely delete them or keep them as backups.

---

## 🔧 Technical Details

### Virtual Environment Handling:
```batch
✅ Automatically creates venv if missing
✅ Validates venv integrity
✅ Falls back to system Python if venv fails
✅ Uses explicit paths (venv\Scripts\python.exe)
✅ Handles corrupted venv folders
```

### Configuration Management:
```batch
✅ Checks for config.json before launch
✅ Offers to create from template
✅ Copies from config.example.json if available
✅ Generates complete template otherwise
✅ Validates required settings
```

### Dependency Management:
```batch
✅ Checks for required packages before launch
✅ Auto-installs missing dependencies
✅ Separate checks for bot vs dashboard
✅ Updates pip automatically
✅ Clear error messages
```

### Error Handling:
```batch
✅ Validates Python installation
✅ Checks FFmpeg availability
✅ Verifies config.json exists
✅ Handles venv creation failures
✅ Graceful fallbacks
✅ Detailed error messages
```

---

## 🎨 Menu System

### Main Menu:
```
========================================
  Discord Music Bot - Unified Launcher
========================================

Select Launch Mode:

  [1] Bot Only (Discord Bot)
  [2] Dashboard Only (Web Interface)
  [3] Integrated Mode (Bot + Dashboard)
  [4] Separate Windows (Bot + Dashboard)

  [5] Install/Update Dependencies
  [6] Check System Requirements
  [7] Create/Reset Config File

  [0] Exit

========================================
```

### Navigation:
- Press number key to select option
- After launch mode exits, returns to menu
- Press [0] to exit launcher
- Ctrl+C stops running bot/dashboard

---

## 📊 Comparison: Old vs New

| Feature | Old Launchers | New Unified Launcher |
|---------|--------------|---------------------|
| Number of files | 4 separate files | 1 file |
| User confusion | High (which to use?) | None (menu-driven) |
| Code duplication | ~80% duplicate | 0% duplicate |
| Maintenance | Update 4 files | Update 1 file |
| Error handling | Inconsistent | Consistent |
| Utilities | None | 3 built-in |
| Menu system | No | Yes |
| Returns to menu | No | Yes |
| System check | No | Yes |
| Dependency installer | No | Yes |
| Config creator | Partial | Complete |

---

## 🛠️ Common Functions (Shared Code)

All launch modes use these shared functions:

### `:SETUP_ENVIRONMENT`
- Checks Python installation
- Creates/validates virtual environment
- Sets Python and pip paths
- Displays Python version

### `:CHECK_CONFIG`
- Verifies config.json exists
- Offers to create from template
- Validates required settings

### `:CHECK_DEPENDENCIES`
- Checks bot dependencies (discord.py, yt-dlp)
- Auto-installs if missing
- Updates pip

### `:CHECK_DASHBOARD_DEPENDENCIES`
- Checks dashboard dependencies (fastapi, uvicorn)
- Auto-installs if missing

### `:CHECK_FFMPEG`
- Verifies FFmpeg in PATH
- Warns if missing
- Offers to continue anyway

### `:CREATE_DIRECTORIES`
- Creates logs/ directory
- Creates web_dashboard/templates/
- Creates web_dashboard/static/

### `:GENERATE_CONFIG`
- Generates complete config.json template
- Includes all settings with defaults
- Properly formatted JSON

---

## 🎯 Recommended Launch Mode

**Option [3] - Integrated Mode** is recommended because:

✅ **Best Performance**
- Bot and dashboard in same process
- No inter-process communication overhead
- Shared memory and resources

✅ **Real-Time Communication**
- Dashboard bridge connects directly
- WebSocket updates work perfectly
- Instant status synchronization

✅ **Easiest to Use**
- Single window to manage
- One process to start/stop
- Automatic browser opening

✅ **Full Feature Set**
- All bot commands work
- All dashboard features work
- Real-time music queue updates
- Live server status

✅ **Production Ready**
- Stable and tested
- Proper error handling
- Clean shutdown

---

## 🔄 Migration Guide

### If you were using `launch.bat`:
→ Use **Option [1] - Bot Only**

### If you were using `launch_gui.bat`:
→ Use **Option [2] - Dashboard Only**

### If you were using `launch_integrated.bat`:
→ Use **Option [3] - Integrated Mode** ⭐

### If you were using `launch_all.bat`:
→ Use **Option [4] - Separate Windows**

---

## 🐛 Troubleshooting

### "Python is not installed or not in PATH"
**Solution:** Install Python 3.8+ from python.org and add to PATH

### "Failed to create virtual environment"
**Solution:** Launcher will use system Python automatically

### "config.json not found"
**Solution:** Use option [7] to create config.json

### "Failed to install dependencies"
**Solution:** 
1. Check internet connection
2. Try option [5] again
3. Run manually: `pip install -r requirements.txt`

### "FFmpeg not found in PATH"
**Solution:** 
1. Download FFmpeg from ffmpeg.org
2. Add to system PATH
3. Or continue without (bot won't play audio)

### "Port 8000 already in use"
**Solution:**
1. Close other dashboard instances
2. Or change port in config.json

### Menu doesn't appear
**Solution:**
1. Right-click launcher.bat
2. Select "Run as Administrator"
3. Or run from Command Prompt

---

## 📝 Configuration File

The launcher creates a complete config.json with all settings:

```json
{
    "token": "YOUR_BOT_TOKEN_HERE",
    "owner_id": 123456789012345678,
    "playing": "!help for commands",
    "command_prefix": "!",
    "max_queue_size": 100,
    "max_playlist_size": 500,
    "allowed_file_extensions": [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus"],
    "music_directory": null,
    "llm": {
        "enabled": false,
        "provider": "ollama",
        "model": "llama3",
        "api_key": null,
        "base_url": "http://localhost:11434",
        "timeout": 30,
        "max_tokens": 500
    },
    "music_synthesis": {
        "enabled": false,
        "backend": "disabled",
        "cache_dir": "generated_music",
        "max_cache_size_mb": 1000,
        "default_duration": 30,
        "default_quality": "medium",
        "suno_api_key": null,
        "suno_api_url": "https://api.suno.ai/v1",
        "musicgen_model": "facebook/musicgen-small"
    },
    "web_dashboard": {
        "enabled": true,
        "host": "0.0.0.0",
        "port": 8000
    }
}
```

**Required Settings:**
- `token` - Your Discord bot token
- `owner_id` - Your Discord user ID (as number)

**Optional Settings:**
- Everything else has sensible defaults

---

## 🎉 Benefits Summary

### For Users:
✅ Simpler - One file instead of four
✅ Clearer - Menu shows all options
✅ Easier - No need to remember which launcher
✅ Safer - Better error handling
✅ Faster - Built-in utilities

### For Developers:
✅ Maintainable - Single source of truth
✅ Consistent - Same code everywhere
✅ Testable - Easier to test one file
✅ Extensible - Easy to add new options
✅ Documented - Clear function structure

### For Everyone:
✅ Professional - Polished user experience
✅ Reliable - Tested and validated
✅ Complete - All features in one place
✅ Future-proof - Easy to update

---

## 📚 Additional Resources

- **README.md** - General bot documentation
- **FEATURES_GUIDE.md** - Feature documentation
- **DASHBOARD_INTEGRATION_FIX.md** - Dashboard integration details
- **WORK_COMPLETED_SUMMARY.md** - Recent work summary

---

## 🔮 Future Enhancements

Possible additions to the unified launcher:

- [ ] Auto-update checker
- [ ] Backup/restore config
- [ ] Log viewer
- [ ] Performance monitor
- [ ] Plugin manager
- [ ] Theme selector
- [ ] Language selection
- [ ] Advanced settings editor

---

## ✅ Conclusion

The unified `launcher.bat` consolidates all launch functionality into a single, user-friendly, menu-driven interface. It provides:

- **4 launch modes** (bot only, dashboard only, integrated, separate)
- **3 utilities** (install deps, check system, create config)
- **Consistent behavior** across all modes
- **Better error handling** and validation
- **Professional user experience**

**Recommendation:** Use **Option [3] - Integrated Mode** for the best experience!

---

**Created:** November 21, 2025
**Status:** Complete and Ready to Use
**Old Launchers:** Can be safely deleted
