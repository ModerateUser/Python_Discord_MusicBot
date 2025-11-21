# 🎵 Python Discord Music Bot

A feature-rich Discord music bot with comprehensive security, playlist management, advanced AI features, and **AI Music Synthesis** capabilities.

## ✨ Features

### Core Features
- 🎶 **Music Playback**: Stream from YouTube or play local files
- 📚 **Playlist Management**: Create, manage, and play custom playlists
- 🔊 **Audio Controls**: Volume, pause, resume, skip, loop
- 🔍 **YouTube Search**: Search and play songs directly
- 🔒 **Security Hardened**: Rate limiting, input validation, path traversal protection
- 🛡️ **Production Ready**: Comprehensive error handling and logging

### 🤖 Advanced AI Features
- 🎼 **AI Music Synthesis**: Generate original music from text descriptions
- 🧠 **Natural Language Commands**: Control the bot with plain English (`!/`)
- 🎵 **Mood-Based Playlists**: AI-generated playlists based on mood and energy
- 🎧 **Auto-DJ Mode**: Intelligent song selection based on listening history
- 🎭 **Mood Transitions**: Smooth transitions between different musical moods
- 🔍 **Similar Song Discovery**: Find songs similar to what's playing
- 📊 **Song Analysis**: Analyze tempo, mood, energy, and musical characteristics
- 🎨 **Personalized Recommendations**: Context-aware suggestions based on history
- ⚡ **Complex Action Chaining**: Execute multiple actions with temporal triggers

### 🎼 AI Music Synthesis
- **Generate Original Music**: Create unique tracks from text prompts
- **Multiple Backends**: Suno API (high quality) or MusicGen (local, private)
- **Personalized Creation**: Uses listening history for better results
- **Context-Aware**: Understands mood, style, tempo, and genre
- **Smart Caching**: Reuses previously generated music
- **Seamless Integration**: Works with natural language and action chaining

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- FFmpeg installed and in PATH
- Discord Bot Token ([Get one here](https://discord.com/developers/applications))
- *Optional*: LLM for AI features (Ollama, OpenAI, Anthropic, etc.)
- *Optional*: Suno API key or GPU for music synthesis

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ModerateUser/Python_Discord_MusicBot.git
cd Python_Discord_MusicBot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt

# Optional: For local music synthesis (MusicGen)
# Uncomment audiocraft, torch, torchaudio in requirements.txt
# pip install audiocraft torch torchaudio
```

3. **Configure the bot**
```bash
cp config.example.json config.json
# Edit config.json with your bot token and settings
```

4. **Run the bot**
```bash
python bot.py
```

## ⚙️ Configuration

### Basic Configuration (config.json)

```json
{
    "token": "YOUR_BOT_TOKEN_HERE",
    "owner_id": 123456789012345678,
    "playing": "!help for commands",
    "command_prefix": "!",
    "max_queue_size": 100,
    "max_playlist_size": 500,
    "allowed_file_extensions": [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus"],
    "music_directory": null
}
```

### LLM Configuration (Optional - for AI features)

```json
{
    "llm": {
        "enabled": true,
        "provider": "ollama",
        "model": "llama3",
        "api_key": null,
        "base_url": "http://localhost:11434",
        "timeout": 30,
        "max_tokens": 500
    }
}
```

See [docs/LLM_INTEGRATION.md](docs/LLM_INTEGRATION.md) for detailed LLM setup.

### Music Synthesis Configuration (Optional)

```json
{
    "music_synthesis": {
        "enabled": true,
        "backend": "suno_api",
        "suno_api_key": "your-api-key-here",
        "cache_dir": "generated_music",
        "max_cache_size_mb": 1000,
        "default_duration": 30,
        "default_quality": "medium"
    }
}
```

**Backends**:
- `suno_api`: High-quality, requires API key ($10/500 songs)
- `musicgen_local`: Free, local generation, requires GPU (8GB+ VRAM)
- `disabled`: Turn off synthesis

See [docs/MUSIC_SYNTHESIS.md](docs/MUSIC_SYNTHESIS.md) for complete setup guide.

## 🎮 Commands

### Basic Music Commands
- `!play <song/url>` - Play a song from YouTube or local file
- `!pause` - Pause the current song
- `!resume` - Resume playback
- `!skip` - Skip to the next song
- `!stop` - Stop playback and clear queue
- `!loop` - Toggle loop mode for current song
- `!volume <0-100>` - Set volume
- `!nowplaying` - Show currently playing song
- `!search <query>` - Search YouTube for songs

### Playlist Commands
- `!playlist create <name>` - Create a new playlist
- `!playlist add <name> <song>` - Add song to playlist
- `!playlist play <name>` - Play a playlist
- `!playlist list` - List all playlists
- `!playlist show <name>` - Show songs in playlist
- `!playlist delete <name>` - Delete playlist (owner only)

### Voice Commands
- `!join` - Join your voice channel
- `!leave` - Leave voice channel

### 🤖 Natural Language Commands (with LLM)

Use `!/` prefix for natural language:

```
!/ play something upbeat
!/ create a chill playlist with 10 songs
!/ skip this and play jazz
!/ what's in the queue
!/ set volume to 50
!/ find songs similar to what's playing
!/ analyze the current song
!/ enable auto-dj mode with energetic music
```

### 🎼 AI Music Synthesis Commands

```
!/ synthesize upbeat electronic music
!/ create chill lofi beats for studying
!/ generate energetic rock music
!/ make original music based on what I've been listening to
!/ compose calm ambient music for 60 seconds
```

### ⚡ Complex Action Chaining

```
!/ play jazz for 10 minutes then switch to rock
!/ create a workout playlist with 15 energetic songs
!/ synthesize upbeat music then play it on loop
!/ play chill music, set volume to 30, and loop it
!/ find songs similar to what's playing and queue them
!/ transition from calm to energetic over 10 songs
```

## 🔒 Security Features

### Implemented Protections
- ✅ **Path Traversal Protection**: Prevents unauthorized file access
- ✅ **Input Validation**: All user inputs sanitized and validated
- ✅ **Rate Limiting**: 10 requests per 60 seconds for YouTube API
- ✅ **Timeout Protection**: 45s for extraction, 30s for search
- ✅ **File Extension Whitelist**: Only allowed audio formats
- ✅ **Type-Safe Comparisons**: Prevents confusion attacks
- ✅ **Token Protection**: .gitignore prevents accidental commits
- ✅ **Atomic File Operations**: Prevents data corruption
- ✅ **Comprehensive Logging**: Security event monitoring

### Configuration Security
- **owner_id**: Must be integer (not string) to prevent type confusion
- **music_directory**: Optional restriction to specific folder
- **allowed_file_extensions**: Whitelist of safe audio formats
- **LLM API Keys**: Stored securely, never logged

## 📁 Project Structure

```
Python_Discord_MusicBot/
├── bot.py                          # Main bot entry point
├── config.json                     # Configuration (gitignored)
├── config.example.json             # Configuration template
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore rules
│
├── core/
│   ├── __init__.py
│   └── config.py                  # Configuration management
│
├── cogs/
│   ├── __init__.py
│   ├── music.py                   # Music playback commands
│   ├── playlist.py                # Playlist management
│   ├── queue_manager.py           # Queue management
│   └── ai_music.py                # AI music features
│
├── models/
│   ├── __init__.py
│   └── song.py                    # Song and queue models
│
├── services/
│   ├── __init__.py
│   ├── audio_service.py           # YouTube/audio handling
│   ├── playlist_service.py        # Playlist file operations
│   ├── llm_service.py             # LLM integration
│   ├── ai_music_service.py        # Advanced AI features
│   └── music_synthesis_service.py # AI music generation
│
├── utils/
│   ├── __init__.py
│   ├── embeds.py                  # Discord embed formatting
│   └── logger.py                  # Logging configuration
│
└── docs/
    ├── LLM_INTEGRATION.md         # LLM setup guide
    └── MUSIC_SYNTHESIS.md         # Music synthesis guide
```

## 🔧 Troubleshooting

### Bot won't start
- Check your token is correct in config.json
- Ensure owner_id is an **integer**, not a string
- Verify FFmpeg is installed: `ffmpeg -version`

### Voice connection issues
- Ensure PyNaCl is installed: `pip install PyNaCl>=1.5.0`
- Check bot has "Connect" and "Speak" permissions
- Verify you're in a voice channel

### YouTube playback fails
- Update yt-dlp: `pip install --upgrade yt-dlp`
- Check rate limiting (10 requests per 60 seconds)
- Verify internet connection

### Natural language commands not working
- Ensure LLM is configured in config.json
- Check LLM service is running (e.g., Ollama)
- Verify API key if using cloud provider
- See [docs/LLM_INTEGRATION.md](docs/LLM_INTEGRATION.md)

### Music synthesis not available
- Check `music_synthesis.enabled` is `true` in config.json
- For Suno: Verify API key is valid
- For MusicGen: Ensure dependencies installed (`audiocraft`, `torch`)
- Check GPU availability for MusicGen
- See [docs/MUSIC_SYNTHESIS.md](docs/MUSIC_SYNTHESIS.md)

### Slow music generation
- Use smaller MusicGen model: `facebook/musicgen-small`
- Reduce duration to 15-30 seconds
- Switch to Suno API for faster generation
- Ensure GPU is being used (not CPU)

## 📊 Performance & Limits

- **Queue Size**: 100 songs (configurable)
- **Playlist Size**: 500 songs (configurable)
- **Rate Limit**: 10 YouTube requests per 60 seconds
- **Timeout**: 45s for extraction, 30s for search
- **Memory**: Automatic cleanup of inactive guild queues every hour
- **Music Synthesis**: 30-120 seconds per generation
- **Cache Size**: 1GB default (configurable)

## 🎯 Use Cases

### For DJs and Music Enthusiasts
- Create mood-based playlists automatically
- Discover similar songs intelligently
- Analyze song characteristics
- Generate original background music

### For Study/Work Sessions
- Auto-DJ mode for continuous music
- Mood transitions for focus/break cycles
- Generate custom ambient/lofi tracks
- Natural language control without interruption

### For Parties and Events
- Complex action chaining for event flow
- Synthesize custom intro/outro music
- Smart shuffling for optimal energy
- Personalized recommendations

### For Content Creators
- Generate royalty-free background music
- Create unique soundtracks
- Test music concepts quickly
- Analyze song structures

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📝 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Built with [discord.py](https://github.com/Rapptz/discord.py)
- Audio extraction via [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- FFmpeg for audio processing
- LLM integration with Ollama, OpenAI, Anthropic, Google
- Music synthesis via [Suno AI](https://suno.ai/) and [MusicGen](https://github.com/facebookresearch/audiocraft)

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions
- Read documentation in `docs/` folder

## 📚 Documentation

- [LLM Integration Guide](docs/LLM_INTEGRATION.md) - Setup LLM for AI features
- [Music Synthesis Guide](docs/MUSIC_SYNTHESIS.md) - Setup and use AI music generation

---

**⚠️ IMPORTANT SECURITY NOTES:**
- Never commit your `config.json` file
- Keep your bot token secret
- Protect API keys (LLM, Suno)
- Use environment variables in production
- Regularly update dependencies
- Monitor logs for security events

**🎵 Made with ❤️ for the Discord community**

---

**Latest Update**: November 21, 2025 - Added AI Music Synthesis capabilities
