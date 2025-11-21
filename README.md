# 🎵 Python Discord Music Bot

A feature-rich Discord music bot with comprehensive security, playlist management, and robust error handling.

## ✨ Features

- 🎶 **Music Playback**: Stream from YouTube or play local files
- 📚 **Playlist Management**: Create, manage, and play custom playlists
- 🔊 **Audio Controls**: Volume, pause, resume, skip, loop
- 🔍 **YouTube Search**: Search and play songs directly
- 🔒 **Security Hardened**: Rate limiting, input validation, path traversal protection
- 🛡️ **Production Ready**: Comprehensive error handling and logging

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- FFmpeg installed and in PATH
- Discord Bot Token ([Get one here](https://discord.com/developers/applications))

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/ModerateUser/Python_Discord_MusicBot.git
cd Python_Discord_MusicBot
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure the bot**
```bash
cp config.example.json config.json
# Edit config.json with your bot token and owner ID
```

4. **Run the bot**
```bash
python bot.py
```

## ⚙️ Configuration

### Option 1: config.json (Recommended for development)

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

### Option 2: Environment Variables (Recommended for production)

```bash
export DISCORD_BOT_TOKEN="your_token_here"
export DISCORD_OWNER_ID="123456789012345678"
export DISCORD_PLAYING="!help for commands"
export DISCORD_PREFIX="!"
```

## 🎮 Commands

### Music Commands
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

## 🐛 Bug Fixes Included

### Critical Fixes
- ✅ Fixed race condition in `_play_next()` using asyncio.Lock
- ✅ Fixed memory leak with periodic queue cleanup
- ✅ Fixed volume not persisting between songs
- ✅ Fixed loop mode unnecessarily re-fetching URLs
- ✅ Fixed unhandled exceptions causing crashes
- ✅ Fixed data corruption with atomic file operations

## 📁 Project Structure

```
Python_Discord_MusicBot/
├── bot.py                      # Main bot entry point
├── config.json                 # Configuration (gitignored)
├── config.example.json         # Configuration template
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore rules
│
├── core/
│   ├── __init__.py
│   └── config.py              # Configuration management
│
├── cogs/
│   ├── __init__.py
│   ├── music.py               # Music playback commands
│   └── playlist.py            # Playlist management
│
├── models/
│   ├── __init__.py
│   └── song.py                # Song and queue models
│
├── services/
│   ├── __init__.py
│   ├── audio_service.py       # YouTube/audio handling
│   └── playlist_service.py    # Playlist file operations
│
└── utils/
    ├── __init__.py
    └── embeds.py              # Discord embed formatting
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

### File playback fails
- Check file extension is in allowed_file_extensions
- Verify file exists and is readable
- If music_directory is set, ensure file is within it

## 📊 Performance & Limits

- **Queue Size**: 100 songs (configurable)
- **Playlist Size**: 500 songs (configurable)
- **Rate Limit**: 10 YouTube requests per 60 seconds
- **Timeout**: 45s for extraction, 30s for search
- **Memory**: Automatic cleanup of inactive guild queues every hour

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

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions

---

**⚠️ IMPORTANT SECURITY NOTES:**
- Never commit your `config.json` file
- Keep your bot token secret
- Use environment variables in production
- Regularly update dependencies
- Monitor logs for security events

**Made with ❤️ for the Discord community**
