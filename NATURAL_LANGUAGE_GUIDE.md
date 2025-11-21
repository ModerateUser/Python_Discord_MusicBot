# 🤖 Natural Language Commands - Quick Reference Guide

**Version:** 1.0  
**Date:** November 21, 2025  
**Status:** ✅ Ready to Use

---

## 🚀 Quick Start

### Enable Natural Language Commands

1. **Configure LLM in `config.json`:**
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

2. **Start your LLM service** (if using Ollama):
   ```bash
   ollama serve
   ```

3. **Start the bot:**
   ```bash
   python bot.py
   ```

4. **Use natural language commands:**
   ```
   !/play something upbeat
   !/what's in the queue?
   !/set volume to 50
   ```

---

## 📋 Command Reference

### 🎵 Music Playback

#### Play Music
```
!/play [song/artist/genre]
!/play something upbeat
!/play jazz music
!/play never gonna give you up
!/I want to listen to rock
```

#### Skip Song
```
!/skip
!/skip this
!/next song
!/skip to the next one
```

#### Pause/Resume
```
!/pause
!/pause the music
!/resume
!/play again
!/unpause
```

#### Stop Playback
```
!/stop
!/stop playing
!/turn off the music
```

---

### 📝 Queue Management

#### View Queue
```
!/queue
!/what's in the queue?
!/show queue
!/what's playing?
!/what's next?
```

#### Loop/Repeat
```
!/loop
!/repeat this song
!/enable loop
!/loop mode
```

---

### 🔊 Volume Control

#### Set Volume
```
!/volume 50
!/set volume to 50
!/turn it up to 80
!/volume 30%
!/make it louder
!/make it quieter
```

---

### 🎷 Recommendations

#### Get Suggestions
```
!/suggest
!/suggest jazz
!/suggest some chill music
!/recommend songs
!/what should I listen to?
!/suggest upbeat music
```

---

### 🔍 Search

#### Search for Songs
```
!/search rock songs
!/find jazz music
!/look for classical
!/search for [artist name]
```

---

### 📚 Playlist Management

#### List Playlists
```
!/show my playlists
!/list playlists
!/what playlists do I have?
```

#### Play Playlist
```
!/play my favorite songs
!/play [playlist name]
!/play my workout playlist
```

#### Show Playlist
```
!/show my favorite songs
!/what's in [playlist name]?
```

---

## 💡 Example Conversations

### Scenario 1: Relaxation Session
```
User: !/I want to listen to something relaxing
Bot: 🤔 Processing your request...
Bot: 🎵 Searching for relaxing music
Bot: ▶️ Now playing: Ambient Relaxation Mix

User: !/what's playing?
Bot: 🤔 Processing your request...
Bot: 📝 Showing queue
Bot: [Queue embed]

User: !/suggest more like this
Bot: 🤔 Processing your request...
Bot: 🎷 Suggesting relaxing songs
Bot: [5 suggestions]

User: !/play the first one
Bot: ▶️ Now playing: [Song]
```

### Scenario 2: Workout Session
```
User: !/play something energetic for my workout
Bot: 🤔 Processing your request...
Bot: 🎵 Searching for energetic music
Bot: ▶️ Now playing: High Energy Workout Mix

User: !/turn it up to 80
Bot: 🤔 Processing your request...
Bot: 🔊 Setting volume to 80%
Bot: ✅ Volume set to 80%

User: !/skip this one
Bot: 🤔 Processing your request...
Bot: ⏭️ Skipping song
Bot: ▶️ Now playing: [Next Song]

User: !/pause
Bot: ⏸️ Pausing playback

User: !/resume
Bot: ▶️ Resuming playback
```

### Scenario 3: Playlist Discovery
```
User: !/show me my playlists
Bot: 🤔 Processing your request...
Bot: 📚 Available Playlists
Bot: [All playlists]

User: !/play my favorite songs
Bot: 🤔 Processing your request...
Bot: 🎵 Playing playlist: Favorite Songs
Bot: ▶️ Now playing: [First Song]

User: !/what's in this playlist?
Bot: 📝 Showing playlist
Bot: [Playlist contents]
```

---

## ⚙️ Configuration Guide

### Ollama (Local, Free)

**Installation:**
```bash
# Download from https://ollama.ai
# Or use package manager:
brew install ollama  # macOS
# or
sudo apt install ollama  # Linux
```

**Start Ollama:**
```bash
ollama serve
```

**Pull a model:**
```bash
ollama pull llama3
ollama pull mistral
ollama pull neural-chat
```

**Configuration:**
```json
{
  "llm": {
    "enabled": true,
    "provider": "ollama",
    "model": "llama3",
    "base_url": "http://localhost:11434",
    "timeout": 30,
    "max_tokens": 500
  }
}
```

---

### OpenAI (Cloud, Paid)

**Get API Key:**
1. Go to https://platform.openai.com/api-keys
2. Create new secret key
3. Copy the key

**Configuration:**
```json
{
  "llm": {
    "enabled": true,
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "api_key": "sk-...",
    "timeout": 30,
    "max_tokens": 500
  }
}
```

**Recommended Models:**
- `gpt-3.5-turbo` - Fast, cheap
- `gpt-4` - More capable, expensive
- `gpt-4-turbo` - Best balance

---

### Claude (Cloud, Paid)

**Get API Key:**
1. Go to https://console.anthropic.com/
2. Create API key
3. Copy the key

**Configuration:**
```json
{
  "llm": {
    "enabled": true,
    "provider": "claude",
    "model": "claude-3-sonnet-20240229",
    "api_key": "sk-ant-...",
    "timeout": 30,
    "max_tokens": 500
  }
}
```

**Recommended Models:**
- `claude-3-haiku-20240307` - Fast, cheap
- `claude-3-sonnet-20240229` - Balanced
- `claude-3-opus-20240229` - Most capable

---

### Gemini (Cloud, Paid)

**Get API Key:**
1. Go to https://makersuite.google.com/app/apikey
2. Create API key
3. Copy the key

**Configuration:**
```json
{
  "llm": {
    "enabled": true,
    "provider": "gemini",
    "model": "gemini-pro",
    "api_key": "AIza...",
    "timeout": 30,
    "max_tokens": 500
  }
}
```

**Recommended Models:**
- `gemini-pro` - General purpose
- `gemini-pro-vision` - With image support

---

## 🧪 Testing Checklist

- [ ] LLM is configured and running
- [ ] Bot starts without errors
- [ ] `!/play jazz` works
- [ ] `!/queue` shows queue
- [ ] `!/skip` skips song
- [ ] `!/pause` pauses playback
- [ ] `!/resume` resumes playback
- [ ] `!/volume 50` sets volume
- [ ] `!/suggest` shows suggestions
- [ ] `!/stop` stops playback

---

## 🐛 Troubleshooting

### "Natural language commands require an LLM to be loaded"

**Solution:**
1. Check `config.json` has `"llm": {"enabled": true}`
2. Verify LLM service is running
3. Check LLM configuration is correct
4. Check logs for connection errors

### "Could not understand your request"

**Solution:**
1. Try rephrasing your request
2. Use simpler language
3. Check LLM model is appropriate
4. Try a different LLM provider

### LLM Response is Slow

**Solution:**
1. Increase `timeout` in config (default: 30s)
2. Use a faster model (e.g., gpt-3.5-turbo instead of gpt-4)
3. Check network connection
4. Check LLM service is not overloaded

### Command Not Recognized

**Solution:**
1. Check command is in supported list
2. Try different phrasing
3. Use regular commands as fallback
4. Check bot logs for errors

---

## 📊 Supported Intents

| Intent | Examples | Status |
|--------|----------|--------|
| play | "play jazz", "play something upbeat" | ✅ |
| skip | "skip", "next song" | ✅ |
| pause | "pause", "pause the music" | ✅ |
| resume | "resume", "play again" | ✅ |
| stop | "stop", "stop playing" | ✅ |
| queue | "what's in the queue?", "show queue" | ✅ |
| loop | "loop this", "repeat" | ✅ |
| volume | "set volume to 50", "volume 75%" | ✅ |
| suggest | "suggest jazz", "recommend songs" | ✅ |
| search | "search for rock", "find jazz" | ✅ |
| playlist | "show playlists", "play my playlist" | ✅ |

---

## 🔐 Security Notes

- ✅ All commands validated before execution
- ✅ No arbitrary code execution
- ✅ Rate limiting still applies
- ✅ LLM API keys stored securely in config
- ✅ Input sanitization on all parameters
- ✅ Error messages don't leak sensitive info

---

## 📞 Getting Help

1. **Check logs:** `tail -f bot.log`
2. **Verify configuration:** Check `config.json`
3. **Test LLM:** Try LLM directly (e.g., `ollama run llama3`)
4. **Use regular commands:** Fall back to `!play`, `!queue`, etc.
5. **Check GitHub issues:** Report bugs or ask questions

---

## 🎯 Tips & Tricks

### Natural Language Tips
- Be conversational - the bot understands natural language
- Specify mood/genre for better results
- Ask questions - "what's in the queue?" works
- Use contractions - "what's", "don't", etc.

### Performance Tips
- Use Ollama locally for faster responses
- Use gpt-3.5-turbo for balance of speed/cost
- Increase timeout if LLM is slow
- Monitor LLM service health

### Customization Tips
- Modify intent parsing prompt in `bot.py`
- Add new commands by extending `execute_natural_language_command()`
- Adjust thinking messages for your preference
- Create custom LLM prompts for specific use cases

---

## 📚 Related Documentation

- [BUG_FIXES_SUMMARY.md](BUG_FIXES_SUMMARY.md) - All bug fixes
- [README.md](README.md) - Main documentation
- [bot.py](bot.py) - Bot source code
- [services/llm_service.py](services/llm_service.py) - LLM service

---

## 🎉 Enjoy!

Your Discord Music Bot now supports natural language commands! Have fun exploring the possibilities.

**Questions?** Check the troubleshooting section or review the examples above.

**Happy listening!** 🎵🤖
