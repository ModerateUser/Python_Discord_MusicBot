# Discord Music Bot

A Python-based Discord bot for playing audio from YouTube, local files, and more with queue management and playlist support.

## Features

- 🎵 Stream music from YouTube (URLs and search)
- 📁 Play local audio files
- 📝 Queue management system
- 📚 Create and manage playlists (supports both YouTube and local files)
- 🔁 Loop mode for repeating songs
- ⏯️ Playback controls (pause, resume, skip, stop)
- 🔊 Volume control
- 🔍 Search YouTube directly from Discord
- 🎮 Custom Discord status

## Prerequisites

- Python 3.8 or higher
- FFmpeg installed on your system
- A Discord Bot Token

## Installation

### 1. Install FFmpeg

**Windows:**
- Download from [ffmpeg.org](https://ffmpeg.org/download.html)
- Extract and add to your system PATH

**Linux:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `discord.py[voice]` - Discord API wrapper with voice support
- `yt-dlp` - YouTube and media downloader/streamer
- `PyNaCl` - Voice encryption library

### 3. Configure the Bot

1. Create a Discord application at [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a bot and copy the token
3. Enable these Privileged Gateway Intents:
   - Message Content Intent
   - Server Members Intent (optional)
4. Get your Discord User ID (enable Developer Mode in Discord, right-click your name, Copy ID)
5. Edit `config.json` with your details:

```json
{
    "token": "YOUR_BOT_TOKEN_HERE",
    "owner_id": "YOUR_DISCORD_USER_ID_HERE",
    "playing": "!help_music for commands"
}
```

### 4. Invite the Bot to Your Server

Use this URL (replace CLIENT_ID with your bot's client ID):
```
https://discord.com/api/oauth2/authorize?client_id=CLIENT_ID&permissions=36700160&scope=bot
```

Required permissions:
- Connect (voice)
- Speak (voice)
- Send Messages
- Embed Links
- Read Message History

## Usage

### Running the Bot

```bash
python bot.py
```

### Commands

#### Playback Commands
- `!join` - Bot joins your voice channel
- `!leave` - Bot leaves the voice channel
- `!play <url/search/path>` - Play from YouTube URL, search query, or local file
- `!search <query>` - Search YouTube and display top 5 results
- `!pause` - Pause the current song
- `!resume` - Resume playback
- `!skip` - Skip to the next song
- `!stop` - Stop playback and clear queue
- `!loop` - Toggle loop mode for current song
- `!volume <0-100>` - Adjust playback volume
- `!queue` - Display the current queue
- `!nowplaying` or `!np` - Show currently playing song

#### Playlist Commands
- `!playlist_create <n>` - Create a new playlist
- `!playlist_add <n> <url/path>` - Add a song to a playlist (YouTube or local)
- `!playlist_play <n>` - Play all songs from a playlist
- `!playlist_list` - List all available playlists
- `!playlist_show <n>` - Show songs in a specific playlist
- `!playlist_delete <n>` - Delete a playlist (owner only)

#### Help
- `!help_music` - Display all available commands

### Example Usage

**Playing from YouTube:**
```
!join
!play Never Gonna Give You Up
!play https://www.youtube.com/watch?v=dQw4w9WgXcQ
!search lofi hip hop
```

**Playing local files:**
```
!play C:/Music/song.mp3
!play /home/user/music/album/track.flac
```

**Managing playlists:**
```
!playlist_create chill
!playlist_add chill https://youtube.com/watch?v=...
!playlist_add chill C:/Music/relaxing.mp3
!playlist_play chill
```

**Queue management:**
```
!queue
!nowplaying
!skip
!loop
!volume 75
```

## Supported Audio Sources

### YouTube
- Direct URLs (youtube.com, youtu.be)
- Search queries
- Live streams
- Age-restricted content (if accessible)

### Local Files
Any audio format that FFmpeg can handle:
- MP3, WAV, FLAC, OGG, M4A, AAC
- WMA, OPUS, ALAC
- And many more

### Other Sources (via yt-dlp)
yt-dlp supports 1000+ sites including:
- SoundCloud
- Bandcamp
- Vimeo
- Twitch
- And many more

## Troubleshooting

**Bot doesn't play audio:**
- Ensure FFmpeg is installed and in your system PATH
- Run `ffmpeg -version` to verify installation
- Check that you're in a voice channel
- Verify the bot has "Connect" and "Speak" permissions

**Bot doesn't respond to commands:**
- Check that Message Content Intent is enabled in Discord Developer Portal
- Verify the bot has proper permissions in your server
- Make sure you're using the correct command prefix (`!`)

**YouTube playback issues:**
- yt-dlp may need updating: `pip install -U yt-dlp`
- Some videos may be geo-restricted
- Age-restricted videos may not work

**"Unable to extract data" errors:**
- Update yt-dlp: `pip install -U yt-dlp`
- Try using a direct URL instead of search
- Check if the video is available in your region

**High latency or stuttering:**
- Ensure stable internet connection
- Lower the volume with `!volume 50`
- Try playing local files instead of streaming

**Permission errors:**
- Ensure the bot has "Connect" and "Speak" permissions in voice channels
- Check that the voice channel isn't full or restricted

## Advanced Configuration

### Custom yt-dlp Options
Edit the `ytdl_format_options` in `bot.py` to customize download behavior:
```python
ytdl_format_options = {
    'format': 'bestaudio/best',
    'noplaylist': True,  # Set to False to allow playlists
    # Add more options as needed
}
```

### Auto-disconnect
The bot automatically disconnects when it's alone in a voice channel to save resources.

## Performance Tips

- Use local files for frequently played songs
- Keep the bot and your Discord client on a stable network
- Update dependencies regularly with `pip install -U -r requirements.txt`
- Close other bandwidth-intensive applications while streaming

## Privacy & Security

- Never share your bot token
- The `config.json` file is gitignored by default
- yt-dlp doesn't store login credentials by default
- All audio streaming is done directly through Discord's voice API

## License

MIT License - feel free to modify and distribute as needed.

## Credits

- Built with [discord.py](https://github.com/Rapptz/discord.py)
- Powered by [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- Uses FFmpeg for audio processing