# 🎵 Discord Music Bot

A feature-rich Discord music bot with AI capabilities, web dashboard, and comprehensive music management features.

[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Discord.py](https://img.shields.io/badge/discord.py-2.0+-blue.svg)](https://github.com/Rapptz/discord.py)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## ✨ Features

### Core Features
- 🎵 **YouTube Streaming** - Play music directly from YouTube
- 📁 **Local File Playback** - Support for MP3, WAV, FLAC, OGG, and more
- 📋 **Queue Management** - Advanced queue system with shuffle, loop, and skip
- 📝 **Playlist System** - Create, save, and load custom playlists
- 🎮 **Natural Language Commands** - Use `!/` prefix for conversational commands
- 🌐 **Web Dashboard** - Real-time monitoring and control via web interface

### AI-Powered Features
- 🤖 **AI Music Generation** - Generate custom music from text descriptions
- 🎭 **Mood-Based Playlists** - Create playlists based on mood and atmosphere
- 🎧 **Auto-DJ Mode** - AI-powered automatic music selection
- 🔍 **Similar Song Discovery** - Find songs similar to what's playing
- 📊 **Song Analysis** - Get detailed information about tracks

### Advanced Features
- 🔄 **Real-time Updates** - WebSocket-based live status updates
- 📈 **Service Health Monitoring** - Built-in health checks for all services
- 🎚️ **Volume Control** - Per-guild volume settings
- ⏸️ **Playback Control** - Pause, resume, skip, and stop
- 🔁 **Loop Modes** - Loop single tracks or entire queues
- 🎲 **Queue Shuffle** - Randomize your music queue

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Discord Bot Token ([Get one here](https://discord.com/developers/applications))
- FFmpeg installed on your system

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/ModerateUser/Python_Discord_MusicBot.git
   cd Python_Discord_MusicBot
   ```

2. **Create configuration file**
   ```bash
   cp config.example.json config.json
   ```

3. **Edit config.json**
   - Add your Discord bot token
   - Set your Discord user ID as owner
   - Configure other settings as needed

4. **Launch the bot**

   **Windows:**
   ```bash
   # Interactive menu
   launch_all.bat
   
   # Or choose specific mode:
   launch.bat              # Bot only
   launch_integrated.bat   # Bot + Dashboard
   launch_gui.bat          # Dashboard only
   ```

   **Linux/Mac:**
   ```bash
   # Make scripts executable
   chmod +x launch.sh launch_integrated.sh
   
   # Launch
   ./launch.sh              # Bot only
   ./launch_integrated.sh   # Bot + Dashboard
   ```

The launcher will automatically:
- ✅ Check Python installation
- ✅ Create virtual environment
- ✅ Install dependencies
- ✅ Verify configuration
- ✅ Start the bot

## 📖 Usage

### Basic Commands

#### Music Playback
```
!play <song name or URL>    - Play a song
!pause                      - Pause playback
!resume                     - Resume playback
!skip                       - Skip current song
!stop                       - Stop and clear queue
!volume <0-100>             - Set volume
!nowplaying                 - Show current song
!loop                       - Toggle loop mode
```

#### Queue Management
```
!queue [page]               - Show queue
!clear                      - Clear queue
!shuffle                    - Shuffle queue
!remove <position>          - Remove song from queue
!move <from> <to>           - Move song in queue
```

#### Playlists
```
!playlist create <name>     - Create new playlist
!playlist save <name>       - Save current queue
!playlist load <name>       - Load playlist
!playlist list              - List all playlists
!playlist delete <name>     - Delete playlist
```

#### AI Features (when enabled)
```
!aiplay <description>       - Generate AI music
!mood <mood>                - Create mood playlist
!similar                    - Find similar songs
!autodj                     - Enable auto-DJ mode
```

#### Utility
```
!help [command]             - Show help
!info                       - Bot information
!ping                       - Check latency
!health                     - Service health check
```

### Natural Language Commands

When LLM is enabled, use the `!/` prefix for conversational commands:

```
!/ play something relaxing
!/ skip this song and play something upbeat
!/ create a playlist of happy songs
!/ what's playing right now?
```

### Web Dashboard

Access the web dashboard at `http://localhost:8000` when running in integrated mode:

- 📊 Real-time bot status
- 🎵 View all active queues
- 🎮 Control playback remotely
- 📈 Monitor service health
- ⚙️ View configuration

API documentation available at `http://localhost:8000/docs`

## ⚙️ Configuration

### Basic Configuration

Edit `config.json`:

```json
{
  "token": "YOUR_BOT_TOKEN",
  "owner_id": "YOUR_DISCORD_USER_ID",
  "command_prefix": "!",
  "playing": "!help for commands",
  "max_queue_size": 100,
  "max_playlist_size": 500
}
```

### Optional Features

#### AI Music Generation

Add to `config.json`:

```json
{
  "music_synthesis": {
    "enabled": true,
    "backend": "musicgen",
    "model": "facebook/musicgen-small",
    "cache_dir": "./cache/synthesis"
  }
}
```

#### LLM Integration

Add to `config.json`:

```json
{
  "llm": {
    "enabled": true,
    "provider": "openai",
    "api_key": "YOUR_API_KEY",
    "model": "gpt-4"
  }
}
```

#### Local Music Files

Add to `config.json`:

```json
{
  "music_directory": "./music",
  "allowed_file_extensions": [".mp3", ".wav", ".flac", ".ogg", ".m4a"]
}
```

## 🏗️ Architecture

### Project Structure

```
Python_Discord_MusicBot/
├── bot.py                      # Basic bot entry point
├── bot_with_dashboard.py       # Integrated bot + dashboard
├── config.json                 # Configuration file
├── requirements.txt            # Python dependencies
├── launch*.bat                 # Windows launchers
├── launch*.sh                  # Linux/Mac launchers
│
├── core/                       # Core bot functionality
│   ├── bot_core.py            # Main bot class
│   ├── config.py              # Configuration management
│   ├── service_manager.py     # Service dependency injection
│   └── nlp_handler.py         # Natural language processing
│
├── cogs/                       # Command modules
│   ├── help.py                # Help system
│   ├── music.py               # Music playback
│   ├── playlist.py            # Playlist management
│   ├── queue_manager.py       # Queue operations
│   └── ai_music.py            # AI features
│
├── services/                   # Backend services
│   ├── dashboard_bridge.py    # Dashboard integration
│   ├── audio_service.py       # Audio processing
│   ├── synthesis_service.py   # AI music generation
│   └── advanced_ai_service.py # Advanced AI features
│
├── web_dashboard/              # Web interface
│   ├── app.py                 # FastAPI application
│   ├── templates/             # HTML templates
│   └── static/                # CSS/JS assets
│
├── utils/                      # Utility functions
│   ├── logger.py              # Logging setup
│   └── validators.py          # Input validation
│
├── models/                     # Data models
│   └── queue.py               # Queue data structures
│
├── tests/                      # Unit tests
│   └── test_*.py              # Test files
│
└── docs/                       # Documentation
    └── API.md                 # API documentation
```

### Key Components

#### Service Manager
Dependency injection system for managing bot services:
- Audio Service
- Synthesis Service
- Advanced AI Service
- Dashboard Bridge

#### Dashboard Bridge
Real-time communication between Discord bot and web dashboard:
- WebSocket updates
- Command execution
- Status monitoring
- Queue synchronization

#### Music Queue System
Advanced queue management with:
- Thread-safe operations
- Loop modes (single, queue)
- Shuffle support
- Position tracking
- History tracking

## 🔧 Development

### Running Tests

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run with coverage
pytest --cov=. tests/
```

### Code Style

This project follows PEP 8 style guidelines:

```bash
# Format code
black .

# Check style
flake8 .

# Type checking
mypy .
```

### Adding New Features

1. Create a new cog in `cogs/` directory
2. Implement commands using discord.py command decorators
3. Register the cog in `core/bot_core.py`
4. Add tests in `tests/`
5. Update documentation

## 🐛 Troubleshooting

### Bot won't start

**Problem:** `Invalid bot token`
- **Solution:** Check your `config.json` and ensure the token is correct

**Problem:** `FFmpeg not found`
- **Solution:** Install FFmpeg and add it to your system PATH

**Problem:** `Module not found`
- **Solution:** Run `pip install -r requirements.txt` in your virtual environment

### Music won't play

**Problem:** `Not connected to voice channel`
- **Solution:** Join a voice channel before using music commands

**Problem:** `Age-restricted video`
- **Solution:** Some YouTube videos require authentication and cannot be played

**Problem:** `Download error`
- **Solution:** Update yt-dlp: `pip install -U yt-dlp`

### Dashboard issues

**Problem:** Dashboard won't load
- **Solution:** Ensure you're using `launch_integrated.bat` or `bot_with_dashboard.py`

**Problem:** Real-time updates not working
- **Solution:** Check WebSocket connection in browser console

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/ModerateUser/Python_Discord_MusicBot/issues)
- **Documentation:** [Wiki](https://github.com/ModerateUser/Python_Discord_MusicBot/wiki)
- **Discord:** [Support Server](https://discord.gg/your-invite-link)

## 🙏 Acknowledgments

- [discord.py](https://github.com/Rapptz/discord.py) - Discord API wrapper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [FastAPI](https://fastapi.tiangolo.com/) - Web framework
- [MusicGen](https://github.com/facebookresearch/audiocraft) - AI music generation

## 📊 Status

### Current Version: 1.0.0

### Recent Updates

- ✅ **FIX CRITICAL #1-4:** Implemented all launch scripts (Windows & Linux/Mac)
- ✅ **FIX MEDIUM #1:** Removed config validation bypass, added proper error handling
- ✅ **FIX MEDIUM #2:** Implemented comprehensive help command system
- ✅ **FIX MEDIUM #3:** Integrated help cog into bot core
- ✅ **DOCS:** Created comprehensive README with setup instructions

### Known Issues

- Audio service duplication (two versions exist)
- Some API endpoints are stubbed (config update, bot control)
- Static assets created on-the-fly instead of pre-existing

### Roadmap

- [ ] Resolve audio service duplication
- [ ] Implement config update API
- [ ] Add rate limiting to endpoints
- [ ] Improve WebSocket error handling
- [ ] Add reconnection logic
- [ ] Implement comprehensive test coverage
- [ ] Add Docker support
- [ ] Create installation wizard

## 🌟 Features in Detail

### Music Playback

The bot supports multiple audio sources:
- **YouTube:** Direct streaming from YouTube videos and playlists
- **Local Files:** Play music from your local filesystem
- **URLs:** Support for direct audio file URLs

### Queue System

Advanced queue management features:
- **Unlimited Queue Size:** Configurable maximum (default: 100)
- **Position Tracking:** Know exactly where you are in the queue
- **History:** Track previously played songs
- **Loop Modes:** Loop single tracks or entire queue
- **Shuffle:** Randomize queue order

### AI Integration

When enabled, the bot can:
- **Generate Music:** Create original music from text descriptions
- **Analyze Songs:** Get detailed information about tracks
- **Mood Detection:** Automatically detect and categorize song moods
- **Smart Recommendations:** AI-powered song suggestions
- **Auto-DJ:** Automatically select and play music based on context

### Web Dashboard

Real-time web interface featuring:
- **Live Status:** See bot status and connected guilds
- **Queue Viewer:** View and manage queues for all servers
- **Remote Control:** Control playback from your browser
- **Health Monitoring:** Check service health and uptime
- **Configuration:** View and manage bot settings
- **API Access:** RESTful API with OpenAPI documentation

## 💡 Tips & Tricks

### Performance Optimization

1. **Use Local Files:** Local playback is faster than streaming
2. **Limit Queue Size:** Smaller queues use less memory
3. **Enable Caching:** Cache frequently played songs
4. **Adjust Buffer Size:** Tune audio buffer for your network

### Best Practices

1. **Regular Updates:** Keep dependencies up to date
2. **Monitor Logs:** Check logs regularly for issues
3. **Backup Playlists:** Export important playlists
4. **Use Virtual Environment:** Isolate dependencies
5. **Configure Permissions:** Set appropriate bot permissions

### Advanced Usage

#### Custom Commands

Add custom commands by creating a new cog:

```python
from discord.ext import commands

class CustomCog(commands.Cog):
    @commands.command()
    async def mycommand(self, ctx):
        await ctx.send("Hello!")

async def setup(bot):
    await bot.add_cog(CustomCog(bot))
```

#### Service Integration

Integrate custom services:

```python
from core.service_manager import ServiceManager

class MyService:
    async def initialize(self):
        # Setup code
        pass
    
    async def shutdown(self):
        # Cleanup code
        pass

# Register in bot_core.py
bot.service_manager.register_service('my_service', MyService())
```

## 🔐 Security

### Best Practices

- **Never commit** your `config.json` with tokens
- **Use environment variables** for sensitive data
- **Restrict bot permissions** to minimum required
- **Enable 2FA** on your Discord account
- **Regular updates** to patch security vulnerabilities

### Token Security

Store your bot token securely:

```bash
# Use environment variables
export DISCORD_TOKEN="your_token_here"

# Or use .env file (add to .gitignore)
echo "DISCORD_TOKEN=your_token_here" > .env
```

Update config to use environment variables:

```json
{
  "token": "${DISCORD_TOKEN}",
  "owner_id": "${DISCORD_OWNER_ID}"
}
```

---

Made with ❤️ by the Discord Music Bot Team

**Star ⭐ this repository if you find it useful!**
