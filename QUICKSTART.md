# Discord Music Bot - Quick Start Guide

## 🚀 Get Started in 3 Steps

### Step 1: Install Requirements

**Install Python 3.8+** from https://python.org

**Install FFmpeg:**
- **Windows:** Download from https://ffmpeg.org/download.html and add to PATH
- **Linux:** `sudo apt install ffmpeg`
- **macOS:** `brew install ffmpeg`

**Install Python dependencies:**
```bash
pip install -r requirements.txt
```

### Step 2: Configure the Bot

**Create `config.json`:**
```json
{
    "token": "YOUR_BOT_TOKEN_HERE",
    "owner_id": 123456789012345678,
    "command_prefix": "!",
    "playing": "!help for commands"
}
```

**Get your bot token:**
1. Go to https://discord.com/developers/applications
2. Create a new application
3. Go to "Bot" section
4. Click "Reset Token" and copy it
5. Paste it in `config.json`

**Get your Discord user ID:**
1. Enable Developer Mode in Discord (Settings → Advanced → Developer Mode)
2. Right-click your username
3. Click "Copy ID"
4. Paste it in `config.json` as `owner_id`

### Step 3: Run the Bot

**Option A: Use the launcher (Recommended)**
```bash
launch.bat
```
Then choose:
- `1` for Bot Only (basic music)
- `2` for Bot + Dashboard (with web interface)
- `3` for Dashboard Only

**Option B: Run directly**
```bash
# Bot only
python bot.py

# Bot with dashboard
python bot_with_dashboard.py
```

---

## 🎵 Basic Commands

Once the bot is running and invited to your server:

```
!play <song>        - Play a song from YouTube
!pause              - Pause playback
!resume             - Resume playback
!skip               - Skip current song
!stop               - Stop and clear queue
!queue              - Show current queue
!volume <0-100>     - Set volume
!help               - Show all commands
```

---

## 🔧 Troubleshooting

### Bot won't start?

**Run the diagnostic script:**
```bash
python test_bot.py
```

This will tell you exactly what's wrong.

### Common Issues:

**"FFmpeg not found"**
- Install FFmpeg and make sure it's in your PATH
- Restart your terminal after installing

**"Invalid token"**
- Check your `config.json` has the correct bot token
- Make sure there are no extra spaces or quotes

**"Module not found"**
- Run `pip install -r requirements.txt`
- Make sure you're using Python 3.8 or higher

**"Bot connects but won't play music"**
- Make sure FFmpeg is installed
- Check bot has permission to join voice channels
- Try `!ping` to verify bot is responding

### Still having issues?

1. Run `python test_bot.py` and check the output
2. Check the `logs/` folder for error messages
3. Make sure your bot has these permissions:
   - Read Messages
   - Send Messages
   - Connect (voice)
   - Speak (voice)

---

## 📊 Web Dashboard (Optional)

If you started with option 2 (Bot + Dashboard):

**Access the dashboard:**
- Open http://localhost:8000 in your browser
- View bot status, queues, and controls
- API docs at http://localhost:8000/docs

---

## 🎯 Next Steps

Once the bot is working:

1. **Invite to your server:**
   - Go to https://discord.com/developers/applications
   - Select your application
   - Go to OAuth2 → URL Generator
   - Select scopes: `bot`, `applications.commands`
   - Select permissions: `Send Messages`, `Connect`, `Speak`
   - Copy the generated URL and open it

2. **Try advanced features:**
   - Playlists: `!playlist create <name>`
   - Search: `!search <query>`
   - Loop: `!loop`
   - Natural language: `!/ play something upbeat` (requires LLM)

3. **Customize:**
   - Edit `config.json` to change prefix, status, etc.
   - Check `config.example.json` for all options

---

## 📝 Configuration Options

See `config.example.json` for all available options including:
- LLM integration (Ollama, OpenAI)
- Music synthesis (Suno, MusicGen)
- Web dashboard settings
- Security settings

---

## ✅ Verification Checklist

Before asking for help, verify:

- [ ] Python 3.8+ installed (`python --version`)
- [ ] FFmpeg installed (`ffmpeg -version`)
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] `config.json` exists with valid token and owner_id
- [ ] Bot invited to your Discord server
- [ ] Bot has voice channel permissions
- [ ] Diagnostic script passes (`python test_bot.py`)

---

**Need more help?** Check `CRITICAL_FIXES_NEEDED.md` for detailed troubleshooting.
