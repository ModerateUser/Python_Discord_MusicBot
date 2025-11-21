# 🚀 New Features Guide - AI & Web Dashboard

## Overview

Your Discord Music Bot now includes two powerful new features:
1. **🤖 AI-Powered Music Intelligence** - Natural language music search and recommendations
2. **🖥️ Web Dashboard** - Real-time monitoring and control panel

---

## 🤖 AI-Powered Music Features

### What is it?

The bot now understands natural language! Instead of typing exact song names, you can describe what you want to hear, and the AI will find the perfect music for you.

### Supported LLM Providers

Choose from multiple AI providers:

| Provider | Type | Cost | Privacy | Setup Difficulty |
|----------|------|------|---------|------------------|
| **Ollama** | Local | Free | 100% Private | Easy |
| **OpenAI** | Cloud | Paid | Shared | Very Easy |
| **Claude** | Cloud | Paid | Shared | Very Easy |
| **Gemini** | Cloud | Free/Paid | Shared | Very Easy |

### Quick Start with Ollama (Recommended)

**Why Ollama?**
- ✅ Completely free
- ✅ 100% private (runs on your machine)
- ✅ No API keys needed
- ✅ Works offline

**Installation:**

1. **Install Ollama**
   ```bash
   # Windows/Mac/Linux
   curl -fsSL https://ollama.com/install.sh | sh
   
   # Or download from: https://ollama.com/download
   ```

2. **Download a model**
   ```bash
   ollama pull llama3
   ```

3. **Enable in config.json**
   ```json
   {
     "llm": {
       "enabled": true,
       "provider": "ollama",
       "model": "llama3",
       "base_url": "http://localhost:11434"
     }
   }
   ```

4. **Restart the bot**
   ```bash
   python bot.py
   ```

### Using Cloud Providers

#### OpenAI (GPT-4/GPT-3.5)

```json
{
  "llm": {
    "enabled": true,
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "api_key": "sk-your-api-key-here"
  }
}
```

Get API key: https://platform.openai.com/api-keys

#### Anthropic Claude

```json
{
  "llm": {
    "enabled": true,
    "provider": "claude",
    "model": "claude-3-sonnet-20240229",
    "api_key": "sk-ant-your-api-key-here"
  }
}
```

Get API key: https://console.anthropic.com/

#### Google Gemini

```json
{
  "llm": {
    "enabled": true,
    "provider": "gemini",
    "model": "gemini-pro",
    "api_key": "your-api-key-here"
  }
}
```

Get API key: https://makersuite.google.com/app/apikey

### AI Commands

#### `!aiplay <natural language query>`
Play music using natural language descriptions.

**Examples:**
```
!aiplay something upbeat and energetic
!aiplay calm piano music for studying
!aiplay happy songs from the 80s
!aiplay sad acoustic guitar
!aiplay workout music with heavy bass
```

**Aliases:** `!ap`, `!smartplay`

#### `!suggest [criteria]`
Get AI-powered song recommendations.

**Examples:**
```
!suggest energetic workout music
!suggest calm jazz for relaxing
!suggest happy pop songs
!suggest (random suggestions)
```

**Aliases:** `!recommend`

#### `!songinfo <song title>`
Get detailed information about a song.

**Examples:**
```
!songinfo Bohemian Rhapsody
!songinfo Stairway to Heaven
```

**Aliases:** `!info`

#### `!aistatus`
Check if AI service is online and working.

**Aliases:** `!llmstatus`

### How It Works

1. **Natural Language Processing**: AI understands your mood/genre preferences
2. **Smart Query Generation**: Converts your description into optimal YouTube search terms
3. **Intelligent Recommendations**: Suggests songs based on context and criteria

### Troubleshooting AI Features

**"AI Not Available" error:**
- Check if Ollama is running: `ollama list`
- Verify config.json has `"enabled": true`
- Check API key if using cloud provider
- Run `!aistatus` to see detailed status

**Slow responses:**
- Local models (Ollama) depend on your hardware
- Cloud providers are usually faster
- Increase timeout in config if needed

**Poor recommendations:**
- Try different models (llama3, mistral, etc.)
- Be more specific in your queries
- Cloud models (GPT-4, Claude) are more accurate

---

## 🖥️ Web Dashboard

### What is it?

A beautiful web interface to monitor and control your bot in real-time!

### Features

- 📊 **Real-time Status Monitoring**
  - Bot online/offline status
  - Connected servers count
  - Active music queues
  - Uptime tracking

- 🎵 **Queue Management**
  - View current queue for each server
  - See what's playing now
  - Monitor playback status

- 🤖 **AI Service Status**
  - Check if AI is online
  - View current provider and model
  - Quick status refresh

- ⚙️ **Configuration Editor**
  - Edit bot settings via web interface
  - No need to manually edit JSON files
  - Validation and error checking

- 📝 **Log Viewer**
  - Real-time log streaming
  - Filter by log level
  - Search through logs

- 🔄 **Bot Control**
  - Restart bot from dashboard
  - View connected servers
  - Quick actions panel

### Starting the Dashboard

**Option 1: Standalone Mode**
```bash
cd web_dashboard
python app.py
```

**Option 2: With Bot (Coming Soon)**
The dashboard will auto-start with the bot if enabled in config.

### Accessing the Dashboard

1. **Start the dashboard**
2. **Open your browser**
3. **Navigate to:** http://localhost:8000

### Dashboard Pages

#### Main Dashboard (`/`)
- Overview of bot status
- Server statistics
- AI service status
- Quick actions

#### Configuration (`/config`)
- Edit all bot settings
- LLM provider configuration
- Save and reload settings

#### Logs (`/logs`)
- Real-time log viewer
- Filter and search
- Download logs

### API Endpoints

The dashboard provides a REST API:

```
GET  /api/status          - Bot status
GET  /api/guilds          - Connected servers
GET  /api/queue/{id}      - Queue for specific server
GET  /api/config          - Current configuration
POST /api/config          - Update configuration
GET  /api/llm/status      - AI service status
GET  /api/logs            - Recent log entries
WS   /ws                  - WebSocket for real-time updates
```

### Security Considerations

**⚠️ IMPORTANT:**
- Dashboard has NO authentication by default
- Only run on trusted networks
- Use firewall rules to restrict access
- Consider adding authentication for production

**Recommended Setup:**
```json
{
  "web_dashboard": {
    "enabled": true,
    "host": "127.0.0.1",  // localhost only
    "port": 8000
  }
}
```

For remote access, use SSH tunneling:
```bash
ssh -L 8000:localhost:8000 user@your-server
```

---

## 🎯 Complete Configuration Example

```json
{
  "token": "YOUR_BOT_TOKEN_HERE",
  "owner_id": 123456789012345678,
  "playing": "!help | AI-Powered Music",
  "command_prefix": "!",
  "max_queue_size": 100,
  "max_playlist_size": 500,
  "allowed_file_extensions": [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus"],
  "music_directory": null,
  
  "llm": {
    "enabled": true,
    "provider": "ollama",
    "model": "llama3",
    "api_key": null,
    "base_url": "http://localhost:11434",
    "timeout": 30,
    "max_tokens": 500
  },
  
  "web_dashboard": {
    "enabled": true,
    "host": "0.0.0.0",
    "port": 8000
  }
}
```

---

## 📊 Comparison: AI Providers

### Ollama (Local)
**Pros:**
- ✅ Free forever
- ✅ Complete privacy
- ✅ No internet required
- ✅ No rate limits
- ✅ Multiple models available

**Cons:**
- ❌ Requires decent hardware (8GB+ RAM)
- ❌ Slower than cloud APIs
- ❌ Initial setup required

**Best for:** Privacy-conscious users, unlimited usage

### OpenAI (Cloud)
**Pros:**
- ✅ Very fast responses
- ✅ Excellent accuracy
- ✅ No local resources needed
- ✅ Easy setup

**Cons:**
- ❌ Costs money per request
- ❌ Requires internet
- ❌ Data sent to OpenAI
- ❌ Rate limits apply

**Best for:** Best quality, don't mind cost

### Claude (Cloud)
**Pros:**
- ✅ Very accurate
- ✅ Good at understanding context
- ✅ Fast responses
- ✅ Easy setup

**Cons:**
- ❌ Costs money
- ❌ Requires internet
- ❌ Data sent to Anthropic
- ❌ Rate limits

**Best for:** High quality, alternative to OpenAI

### Gemini (Cloud)
**Pros:**
- ✅ Free tier available
- ✅ Fast responses
- ✅ Good accuracy
- ✅ Easy setup

**Cons:**
- ❌ Requires internet
- ❌ Data sent to Google
- ❌ Rate limits on free tier

**Best for:** Free cloud option

---

## 🚀 Quick Start Guide

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup AI (Optional but Recommended)

**For Ollama (Free & Private):**
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Download model
ollama pull llama3

# Verify it's running
ollama list
```

**For Cloud Providers:**
- Get API key from provider
- Add to config.json

### 3. Update Configuration
```bash
cp config.example.json config.json
# Edit config.json with your settings
```

### 4. Start the Bot
```bash
python bot.py
```

### 5. Start the Dashboard (Optional)
```bash
cd web_dashboard
python app.py
```

### 6. Test AI Features
```
!aistatus
!aiplay something energetic
!suggest workout music
```

---

## 💡 Tips & Best Practices

### AI Usage Tips

1. **Be Descriptive**: "upbeat electronic dance music" works better than "music"
2. **Include Mood**: "sad piano ballad" or "happy summer vibes"
3. **Specify Genre**: "90s rock" or "modern jazz"
4. **Use Context**: "music for studying" or "party playlist"

### Dashboard Tips

1. **Bookmark It**: Add http://localhost:8000 to bookmarks
2. **Mobile Friendly**: Works great on phones/tablets
3. **Real-time Updates**: Leave it open to monitor bot
4. **Check Logs**: First place to look when troubleshooting

### Performance Tips

1. **Local AI**: Requires 8GB+ RAM for good performance
2. **Cloud AI**: Fast but costs money per request
3. **Dashboard**: Minimal overhead, safe to run 24/7
4. **WebSocket**: Keeps connection alive for real-time updates

---

## 🐛 Troubleshooting

### AI Issues

**Problem:** "AI Not Available"
```bash
# Check Ollama is running
ollama list

# Restart Ollama
ollama serve

# Check config
cat config.json | grep -A 5 "llm"
```

**Problem:** Slow AI responses
- Use cloud provider (OpenAI/Claude)
- Upgrade hardware for local models
- Increase timeout in config

**Problem:** Poor recommendations
- Try different model (mistral, mixtral)
- Use cloud provider for better accuracy
- Be more specific in queries

### Dashboard Issues

**Problem:** Can't access dashboard
```bash
# Check if running
curl http://localhost:8000/health

# Check firewall
sudo ufw allow 8000

# Check logs
tail -f logs/bot.log
```

**Problem:** WebSocket disconnects
- Normal behavior, auto-reconnects
- Check browser console for errors
- Verify network stability

---

## 📚 Additional Resources

- **Ollama Models**: https://ollama.com/library
- **OpenAI Pricing**: https://openai.com/pricing
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Discord.py Docs**: https://discordpy.readthedocs.io/

---

## 🎉 What's Next?

Future features planned:
- 🔐 Dashboard authentication
- 📱 Mobile app
- 🎨 Custom themes
- 📊 Analytics and statistics
- 🔔 Webhook notifications
- 🎵 Advanced playlist AI
- 🗣️ Voice command support

---

**Enjoy your AI-powered music bot! 🎵🤖**
