# 🏗️ Modular Monolith Architecture

## Directory Structure

```
discord-music-bot/
│
├── bot.py                      # Main entry point
│
├── core/                       # Core configuration and setup
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   └── bot_setup.py           # Bot initialization
│
├── models/                     # Data models
│   ├── __init__.py
│   └── song.py                # Song and MusicQueue classes
│
├── services/                   # Business logic layer
│   ├── __init__.py
│   ├── audio_service.py       # Audio streaming and playback
│   └── playlist_service.py    # Playlist management
│
├── cogs/                       # Discord command modules
│   ├── __init__.py
│   ├── music.py               # Music playback commands
│   ├── queue_manager.py       # Queue management commands
│   └── playlist.py            # Playlist commands
│
├── utils/                      # Utility functions
│   ├── __init__.py
│   ├── embeds.py              # Discord embed creators
│   └── logger.py              # Logging configuration
│
├── logs/                       # Auto-generated log files
│   └── bot.log
│
├── config.json                 # Bot configuration
├── playlists.json             # Playlist storage
├── requirements.txt           # Dependencies
├── pyproject.toml             # Project metadata
├── launch.bat / launch.sh     # Launcher scripts
├── update.bat / update.sh     # Update scripts
├── .gitignore
└── README.md
```

## 📦 Module Responsibilities

### **Core Layer** (`core/`)
- **config.py**: Load and validate configuration
- **bot_setup.py**: Create and configure bot instance

### **Models Layer** (`models/`)
- **song.py**: Data structures for Song and MusicQueue
- Pure data classes with minimal logic
- No external dependencies

### **Services Layer** (`services/`)
- **audio_service.py**: YouTube streaming, local file handling
- **playlist_service.py**: Playlist CRUD operations
- Business logic and external API interactions
- Stateless service classes

### **Cogs Layer** (`cogs/`)
- **music.py**: Playback commands (play, pause, skip, etc.)
- **queue_manager.py**: Queue display and help commands
- **playlist.py**: Playlist management commands
- Each cog is a self-contained feature module

### **Utils Layer** (`utils/`)
- **embeds.py**: Discord embed creation helpers
- **logger.py**: Logging configuration
- Reusable utility functions

## 🎯 Architecture Benefits

### ✅ **Separation of Concerns**
- Each module has a single, well-defined responsibility
- Easy to understand what each file does
- Clear boundaries between layers

### ✅ **Maintainability**
- Changes to one module don't cascade to others
- Easy to locate and fix bugs
- Add new features without touching existing code

### ✅ **Testability**
- Services can be tested independently
- Mock dependencies easily
- Clear input/output contracts

### ✅ **Reusability**
- Services are reusable across cogs
- Utility functions centralized
- No code duplication

### ✅ **Scalability**
- Add new cogs without modifying core
- Extend services without breaking existing features
- Modular growth path

## 🔄 Data Flow

```
User Command
    ↓
Discord Gateway
    ↓
Bot (bot.py) ← Event Handlers
    ↓
Cog (commands) ← Parse & Validate
    ↓
Service Layer ← Business Logic
    ↓
Models (data) ← Data Structures
    ↓
Service Layer ← Process Results
    ↓
Cog ← Format Response
    ↓
Discord (send message)
```

## 🔧 Extending the Bot

### Adding a New Command
1. Choose appropriate cog or create new one
2. Add command method with `@commands.command()`
3. Use existing services for business logic
4. Create embed in utils/embeds.py if needed

### Adding a New Service
1. Create new file in `services/`
2. Implement as a class with clear methods
3. Create singleton instance at bottom of file
4. Import and use in cogs

### Adding a New Cog
1. Create new file in `cogs/`
2. Inherit from `commands.Cog`
3. Register in `bot.py` with `await bot.add_cog()`

## 📝 Code Organization Principles

### **DRY (Don't Repeat Yourself)**
- Common embed creation in `utils/embeds.py`
- Audio operations in `audio_service.py`
- No duplicate business logic

### **Single Responsibility**
- Each class/module does ONE thing well
- Easy to name and describe
- Focused and cohesive

### **Dependency Injection**
- Services passed to cogs via constructor
- Easy to swap implementations
- Better for testing

### **Loose Coupling**
- Modules interact through well-defined interfaces
- Changes don't ripple through codebase
- Independent module evolution

## 🛠️ Development Workflow

### Making Changes
1. Identify which layer needs modification
2. Make changes in appropriate module
3. Update only affected modules
4. Test the specific feature
5. No need to understand entire codebase

### Debugging
1. Check logs in `logs/bot.log`
2. Logs show layer, file, and line number
3. Follow data flow through layers
4. Isolate issue to specific module

### Adding Features
1. Design feature at architecture level
2. Identify which layers are involved
3. Implement bottom-up (models → services → cogs)
4. Register cog in main bot.py
5. Test in isolation

## 📚 Best Practices

### ✅ Do:
- Keep services stateless where possible
- Use type hints for better IDE support
- Log important operations
- Validate inputs at cog layer
- Keep models simple (just data)

### ❌ Don't:
- Put business logic in cogs
- Access Discord API from services
- Create circular dependencies
- Mix concerns between layers
- Hardcode configuration values

## 🎓 Learning Path

1. **Start with models/** - Understand data structures
2. **Then services/** - See how business logic works
3. **Then cogs/** - Learn command handling
4. **Finally bot.py** - See how it all connects

Each layer builds on the previous one!