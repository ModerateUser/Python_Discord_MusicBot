# AI Music Synthesis Guide

## Overview

The Discord Music Bot now includes **AI Music Synthesis** capabilities, allowing you to generate original music on-demand using artificial intelligence. This feature integrates seamlessly with the bot's existing AI features and can create personalized music based on your listening history.

## Features

- 🎼 **Generate Original Music**: Create unique tracks from text descriptions
- 🎨 **Personalized Creation**: Uses your listening history for better results
- 🎹 **Multiple Backends**: Support for Suno API, MusicGen (local), and MIDI fallback
- ⚡ **Context-Aware**: Understands mood, style, tempo, and genre preferences
- 🔄 **Smart Caching**: Reuses previously generated music to save time
- 🎵 **Seamless Integration**: Works with natural language commands and action chaining

## Supported Backends

### 1. Suno API (Recommended for Production)
**Best for**: High-quality music generation with vocals

- ✅ Professional quality output
- ✅ Fast generation (30-60 seconds)
- ✅ Supports vocals and lyrics
- ✅ Multiple genres and styles
- ❌ Requires API key and subscription ($10/500 songs)
- ❌ Internet connection required

### 2. MusicGen Local (Recommended for Privacy)
**Best for**: Local generation without external dependencies

- ✅ Completely offline
- ✅ No API costs
- ✅ Privacy-focused
- ✅ Open-source (Meta)
- ❌ Requires GPU (8GB+ VRAM recommended)
- ❌ Slower generation (60-120 seconds)
- ❌ Lower quality than Suno
- ❌ Large model files (~2GB)

### 3. MIDI Fallback (Not Yet Implemented)
**Best for**: Simple procedural music

- ✅ Lightweight
- ✅ Fast generation
- ❌ Basic quality
- ❌ Limited styles
- ⚠️ Coming in future update

## Setup

### Prerequisites

1. **LLM Service** (required for prompt enhancement)
   - Configure an LLM provider in `config.json`
   - See [LLM_INTEGRATION.md](LLM_INTEGRATION.md) for setup

2. **Discord Bot** (obviously)
   - Bot must be running and connected

### Option A: Suno API Setup

1. **Get API Key**
   ```
   Visit: https://suno.ai/
   Sign up for an account
   Subscribe to API access ($10/500 songs)
   Copy your API key
   ```

2. **Configure Bot**
   ```json
   {
     "music_synthesis": {
       "enabled": true,
       "backend": "suno_api",
       "suno_api_key": "your-api-key-here",
       "suno_api_url": "https://api.suno.ai/v1",
       "cache_dir": "generated_music",
       "max_cache_size_mb": 1000,
       "default_duration": 30,
       "default_quality": "medium"
     }
   }
   ```

3. **Restart Bot**
   ```bash
   python bot.py
   ```

### Option B: MusicGen Local Setup

1. **Install Dependencies**
   ```bash
   # Uncomment these lines in requirements.txt:
   audiocraft>=1.3.0
   torch>=2.0.0
   torchaudio>=2.0.0
   
   # Install
   pip install -r requirements.txt
   ```

2. **Configure Bot**
   ```json
   {
     "music_synthesis": {
       "enabled": true,
       "backend": "musicgen_local",
       "musicgen_model": "facebook/musicgen-small",
       "cache_dir": "generated_music",
       "max_cache_size_mb": 1000,
       "default_duration": 30,
       "default_quality": "medium"
     }
   }
   ```

3. **First Run** (downloads model)
   ```bash
   python bot.py
   # Wait for model download (~2GB)
   # This only happens once
   ```

### Hardware Requirements

**Suno API**:
- Any system with internet connection
- Minimal CPU/RAM requirements

**MusicGen Local**:
- **Recommended**: GPU with 8GB+ VRAM (NVIDIA)
- **Minimum**: CPU with 16GB+ RAM (slower)
- **Storage**: 5GB free space (models + cache)
- **OS**: Linux, Windows, macOS

## Usage

### Natural Language Commands

The easiest way to use music synthesis is through natural language:

```
!/ synthesize upbeat electronic music
!/ create chill lofi beats for studying
!/ generate energetic rock music
!/ make original jazz music based on what I've been listening to
!/ compose calm ambient music for 60 seconds
```

### Complex Action Chaining

Combine synthesis with other actions:

```
!/ synthesize upbeat music then play it on loop
!/ create chill music and set volume to 30
!/ generate energetic music after 3 songs
!/ make original music similar to what's playing
```

### Programmatic Usage

For developers integrating the service:

```python
from services.music_synthesis_service import (
    MusicGenerationRequest,
    GenerationQuality,
    create_music_synthesis_service
)

# Initialize service
synthesis_service = create_music_synthesis_service(config, llm_service)

# Create request
request = MusicGenerationRequest(
    prompt="upbeat electronic music",
    style="electronic",
    mood="energetic",
    tempo=128,
    duration=30,
    quality=GenerationQuality.HIGH,
    guild_id=message.guild.id
)

# Generate music
result = await synthesis_service.generate_music(
    request,
    listening_history=user_history
)

if result:
    print(f"Generated: {result.file_path}")
    print(f"Title: {result.title}")
    print(f"Time: {result.generation_time:.2f}s")
```

## Configuration Reference

### Complete Configuration

```json
{
  "music_synthesis": {
    "enabled": true,
    "backend": "suno_api",
    "cache_dir": "generated_music",
    "max_cache_size_mb": 1000,
    "default_duration": 30,
    "default_quality": "medium",
    "suno_api_key": "your-key-here",
    "suno_api_url": "https://api.suno.ai/v1",
    "musicgen_model": "facebook/musicgen-small"
  }
}
```

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `false` | Enable/disable music synthesis |
| `backend` | string | `"disabled"` | Backend to use: `suno_api`, `musicgen_local`, `midi_fallback`, `disabled` |
| `cache_dir` | string | `"generated_music"` | Directory for cached generated music |
| `max_cache_size_mb` | integer | `1000` | Maximum cache size in MB (auto-cleanup) |
| `default_duration` | integer | `30` | Default generation duration in seconds |
| `default_quality` | string | `"medium"` | Default quality: `low`, `medium`, `high`, `ultra` |
| `suno_api_key` | string | `null` | Suno API key (required for Suno backend) |
| `suno_api_url` | string | `"https://api.suno.ai/v1"` | Suno API endpoint |
| `musicgen_model` | string | `"facebook/musicgen-small"` | MusicGen model: `small`, `medium`, `large` |

### MusicGen Model Options

| Model | Size | Quality | Speed | VRAM |
|-------|------|---------|-------|------|
| `facebook/musicgen-small` | 300MB | Good | Fast | 4GB |
| `facebook/musicgen-medium` | 1.5GB | Better | Medium | 8GB |
| `facebook/musicgen-large` | 3.3GB | Best | Slow | 16GB |

## Examples

### Basic Synthesis

```
!/ synthesize happy pop music
```
Generates a 30-second happy pop track.

### With Style and Mood

```
!/ create energetic rock music with aggressive mood
```
Generates rock music with specific characteristics.

### Custom Duration

```
!/ generate calm ambient music for 60 seconds
```
Creates a 1-minute ambient track.

### Based on Listening History

```
!/ make original music based on what I've been listening to
```
Uses your recent listening history to personalize the generation.

### Complex Workflow

```
!/ synthesize upbeat electronic music, then find similar songs and queue them
```
Generates music, then finds and queues similar tracks.

### Mood Transition

```
!/ create a playlist transitioning from calm to energetic, include synthesized music
```
Generates music as part of a mood transition playlist.

## Advanced Features

### Prompt Enhancement

The bot uses LLM to enhance your prompts automatically:

**Your input**: "chill music"

**Enhanced prompt**: "Relaxed lo-fi hip hop with soft piano, gentle beats, warm bass, and ambient atmosphere at 85 BPM"

### Listening History Integration

When you use synthesis, the bot analyzes your recent listening history to:
- Match your preferred genres
- Adapt to your mood patterns
- Incorporate similar artists' styles
- Maintain consistent energy levels

### Smart Caching

Generated music is cached to avoid regenerating identical requests:
- Cache key based on prompt, style, mood, tempo, duration
- Automatic cleanup when cache exceeds size limit
- Oldest files removed first
- Instant playback for cached results

### Quality Levels

| Quality | Description | Generation Time | File Size |
|---------|-------------|-----------------|-----------|
| `low` | Fast, lower fidelity | 20-40s | ~2MB |
| `medium` | Balanced (default) | 30-60s | ~4MB |
| `high` | Best quality | 60-120s | ~8MB |
| `ultra` | Maximum (if supported) | 120-180s | ~12MB |

## Troubleshooting

### "Music synthesis not available"

**Cause**: Synthesis is disabled or not configured

**Solution**:
1. Check `config.json` - ensure `enabled: true`
2. Verify backend is set correctly
3. For Suno: Check API key is valid
4. For MusicGen: Ensure dependencies installed
5. Restart bot after configuration changes

### "Synthesis failed" or timeout

**Cause**: Backend error or network issue

**Solution**:
1. Check bot logs for detailed error
2. For Suno: Verify API key and internet connection
3. For MusicGen: Check GPU/RAM availability
4. Try reducing duration or quality
5. Check cache directory permissions

### Slow generation with MusicGen

**Cause**: Running on CPU or insufficient VRAM

**Solution**:
1. Use smaller model: `facebook/musicgen-small`
2. Reduce duration to 15-20 seconds
3. Close other GPU-intensive applications
4. Consider using Suno API instead
5. Upgrade to GPU with more VRAM

### "audiocraft not installed"

**Cause**: MusicGen dependencies missing

**Solution**:
```bash
pip install audiocraft torch torchaudio
```

### Cache filling up quickly

**Cause**: Many unique generations

**Solution**:
1. Increase `max_cache_size_mb` in config
2. Manually clean cache directory
3. Use more specific prompts (better cache hits)
4. Reduce default duration

### Poor quality output

**Cause**: Low quality setting or model limitations

**Solution**:
1. Increase quality: `"default_quality": "high"`
2. Use larger MusicGen model
3. Switch to Suno API for better quality
4. Provide more detailed prompts
5. Specify style and mood explicitly

## Performance Optimization

### For Suno API

1. **Batch Requests**: Generate multiple tracks in sequence
2. **Cache Aggressively**: Increase cache size
3. **Optimize Prompts**: More specific = better cache hits
4. **Monitor Usage**: Track API quota

### For MusicGen Local

1. **Use GPU**: 10-20x faster than CPU
2. **Smaller Model**: Start with `musicgen-small`
3. **Shorter Duration**: 15-30 seconds optimal
4. **Batch Size**: Generate one at a time
5. **Model Caching**: Keep model loaded in memory

### General Tips

1. **Enable Caching**: Set reasonable `max_cache_size_mb`
2. **Prompt Enhancement**: Enable LLM for better prompts
3. **Listening History**: Provides better context
4. **Quality vs Speed**: Use `medium` for balance
5. **Monitor Resources**: Check CPU/RAM/GPU usage

## API Reference

### MusicGenerationRequest

```python
@dataclass
class MusicGenerationRequest:
    prompt: str                          # Description of music
    style: Optional[str] = None          # Music style (rock, jazz, etc.)
    mood: Optional[str] = None           # Mood (happy, sad, energetic)
    tempo: Optional[int] = None          # BPM
    duration: int = 30                   # Seconds
    quality: GenerationQuality = MEDIUM  # Quality level
    reference_songs: Optional[List[str]] # Reference tracks
    user_id: Optional[int] = None        # Discord user ID
    guild_id: Optional[int] = None       # Discord guild ID
```

### GeneratedMusic

```python
@dataclass
class GeneratedMusic:
    file_path: str              # Path to audio file
    title: str                  # Generated title
    prompt: str                 # Original prompt
    style: str                  # Music style
    mood: str                   # Music mood
    duration: int               # Duration in seconds
    backend: SynthesisBackend   # Backend used
    generation_time: float      # Time taken (seconds)
    metadata: Dict[str, Any]    # Additional metadata
```

### MusicSynthesisService Methods

```python
# Check availability
available = await synthesis_service.is_available()

# Generate music
result = await synthesis_service.generate_music(request, listening_history)

# Get statistics
stats = synthesis_service.get_stats()
# Returns: total_generations, successful_generations, 
#          avg_generation_time, cache_hits, etc.
```

## Best Practices

### Prompt Writing

**Good Prompts**:
- ✅ "Upbeat electronic dance music with synth leads and driving bass"
- ✅ "Calm acoustic guitar with soft vocals, folk style"
- ✅ "Energetic rock with electric guitars and powerful drums"

**Poor Prompts**:
- ❌ "music"
- ❌ "something good"
- ❌ "idk just make something"

### Style and Mood

**Styles**: rock, pop, jazz, electronic, classical, hip-hop, folk, metal, ambient, etc.

**Moods**: happy, sad, energetic, calm, aggressive, melancholic, uplifting, dark, etc.

### Duration Guidelines

- **15-30s**: Quick generations, good for testing
- **30-60s**: Standard tracks, balanced
- **60-120s**: Full songs, longer wait
- **120s+**: Extended pieces, significant time

### Resource Management

1. Monitor cache size regularly
2. Clean up old generations periodically
3. Use appropriate quality for use case
4. Consider backend costs (Suno API)
5. Balance quality vs generation time

## Integration Examples

### With Auto-DJ

```
!/ enable auto-dj with synthesized music mixed in
```

### With Mood Transitions

```
!/ transition from calm to energetic using synthesized tracks
```

### With Playlists

```
!/ create a workout playlist with 5 synthesized energetic tracks
```

### With Analysis

```
!/ synthesize music similar to what's playing, then analyze it
```

## Limitations

### Current Limitations

1. **No Lyrics Control**: Cannot specify exact lyrics (Suno only)
2. **Style Mixing**: Limited control over style combinations
3. **Exact Tempo**: Tempo is approximate, not exact
4. **Long Generations**: Can take 30-120 seconds
5. **Quality Variance**: Output quality varies by prompt

### Future Improvements

- [ ] MIDI fallback implementation
- [ ] Lyrics specification support
- [ ] Real-time generation progress
- [ ] Multiple backend fallback chain
- [ ] Advanced style mixing
- [ ] Tempo and key control
- [ ] Stem separation
- [ ] Remix capabilities

## FAQ

**Q: How much does it cost?**
A: Suno API costs $10/500 songs. MusicGen is free but requires hardware.

**Q: Can I use this commercially?**
A: Check your backend's license. Suno has specific terms. MusicGen is open-source.

**Q: How long does generation take?**
A: 30-120 seconds depending on backend, quality, and duration.

**Q: Can I generate music with vocals?**
A: Yes with Suno API. MusicGen is instrumental only.

**Q: Is my listening history private?**
A: Yes, it's only used locally for prompt enhancement. Never sent externally.

**Q: Can I use both backends?**
A: Not simultaneously, but you can switch in config.json.

**Q: What audio format is generated?**
A: Suno: MP3/MP4, MusicGen: WAV

**Q: Can I download generated music?**
A: Yes, files are in the `generated_music` directory.

## Support

For issues, questions, or feature requests:

1. Check this documentation
2. Review bot logs for errors
3. Check [GitHub Issues](https://github.com/ModerateUser/Python_Discord_MusicBot/issues)
4. Join our Discord server (if available)

## Credits

- **Suno AI**: https://suno.ai/
- **MusicGen (Meta)**: https://github.com/facebookresearch/audiocraft
- **Discord.py**: https://github.com/Rapptz/discord.py

---

**Last Updated**: November 21, 2025
**Version**: 1.0.0
