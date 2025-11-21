# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-11-21

### 🔒 CRITICAL SECURITY FIXES

#### Configuration & Token Security
- **FIXED:** Added `config.example.json` to prevent accidental token commits
- **FIXED:** Owner ID type confusion vulnerability (now properly validated as integer)
- **FIXED:** Added environment variable support for sensitive configuration
  - `DISCORD_BOT_TOKEN` - Bot token
  - `DISCORD_OWNER_ID` - Owner user ID
  - `DISCORD_PLAYING` - Bot status message
  - `DISCORD_PREFIX` - Command prefix
- **FIXED:** Token validation to prevent common configuration mistakes
- **FIXED:** Discord snowflake ID validation for owner_id

#### File Access Security
- **FIXED:** Path traversal vulnerability in local file playback
- **FIXED:** Added file extension whitelist validation
- **FIXED:** Added optional `music_directory` restriction to prevent arbitrary file access
- **FIXED:** Path validation to prevent directory traversal attacks (`../../../etc/passwd`)
- **FIXED:** File existence and readability validation

#### Input Validation & Sanitization
- **FIXED:** Playlist name validation (prevents JSON injection)
- **FIXED:** Added regex pattern for safe playlist names (alphanumeric, spaces, hyphens, underscores)
- **FIXED:** Search query length validation (max 100 characters)
- **FIXED:** URL length validation (max 500 characters)
- **FIXED:** Volume range validation (0-100)

#### Git Security
- **FIXED:** Enhanced `.gitignore` to prevent committing sensitive data
  - Added `logs/` directory
  - Added `.env` files
  - Added `*.key` and `*.pem` files
  - Added cache and temp directories
  - Better organization with security sections
- **REMOVED:** Duplicate `gitignore.txt` file

### 🐛 CRITICAL BUG FIXES

#### Race Conditions & Concurrency
- **FIXED:** Race condition in `_play_next()` using `asyncio.Lock`
  - Prevents crashes when multiple songs finish simultaneously
  - Thread-safe queue access
- **FIXED:** Concurrent access issues for shared resources

#### Memory Management
- **FIXED:** Memory leak - queues never cleaned up for inactive guilds
  - Added periodic cleanup task (runs hourly)
  - Automatically removes queues for guilds bot is no longer in
- **FIXED:** Resource leaks - proper cleanup of audio sources

#### Playback Issues
- **FIXED:** Volume not persisting between songs
  - Added `volume` field to `MusicQueue` model
  - Volume now maintained across playback session
- **FIXED:** Loop mode unnecessarily re-fetching YouTube URLs
  - Optimized to reuse existing source when possible
  - Prevents rate limiting issues
- **FIXED:** Unhandled exceptions in playback causing bot crashes
- **FIXED:** Potential crash when channel is deleted during playback

#### Data Integrity
- **FIXED:** Playlist data corruption on write errors
  - Implemented atomic file operations (write to temp, then rename)
  - Automatic backup before overwriting
  - Rollback on save failures
- **FIXED:** Corrupted playlist file recovery
  - Automatic backup of corrupted files
  - Fresh file creation on parse errors

#### Error Handling
- **FIXED:** Unhandled yt-dlp exceptions causing crashes
- **FIXED:** Timeout protection for YouTube extraction (45s) and search (30s)
- **FIXED:** Graceful handling of Discord API errors
- **FIXED:** Better error messages for configuration issues

### ⚡ IMPROVEMENTS

#### Rate Limiting & Performance
- **ADDED:** Rate limiting for YouTube API (10 requests per 60 seconds)
- **ADDED:** Queue size limit enforcement (configurable, default: 100)
- **ADDED:** Playlist size limit enforcement (configurable, default: 500)
- **ADDED:** FFmpeg reconnection options for stream stability

#### Logging & Monitoring
- **ADDED:** Comprehensive logging throughout codebase
- **ADDED:** Security event logging (blocked access attempts, unauthorized commands)
- **ADDED:** Audit trail for playlist operations
- **ADDED:** Better error logging with stack traces

#### Code Quality
- **ADDED:** Type hints for better code safety
- **ADDED:** Comprehensive docstrings
- **ADDED:** Input validation for all user inputs
- **ADDED:** Better error messages for users
- **IMPROVED:** Code organization and structure

#### Configuration
- **ADDED:** Security limits in configuration:
  - `max_queue_size` - Maximum songs in queue
  - `max_playlist_size` - Maximum songs in playlist
  - `allowed_file_extensions` - Whitelist of audio formats
  - `music_directory` - Optional directory restriction
- **ADDED:** Configuration validation with helpful error messages
- **ADDED:** UTF-8 encoding support for international characters

#### Dependencies
- **ADDED:** `PyNaCl>=1.5.0` (was missing but required for voice)
- **ADDED:** `python-dotenv>=1.0.0` for environment variable support
- **UPDATED:** Version constraints for security

### 📚 DOCUMENTATION

- **ADDED:** `SECURITY.md` - Comprehensive security best practices guide
  - Token protection guidelines
  - File access security
  - Rate limiting information
  - Input validation details
  - Logging and monitoring guidance
  - Deployment security checklist
  - Vulnerability reporting process
- **ADDED:** `CHANGELOG.md` - This file
- **IMPROVED:** Code comments and docstrings

### 🔧 TECHNICAL CHANGES

#### Core Configuration (`core/config.py`)
- Environment variable override support
- Comprehensive validation with security checks
- Type-safe owner comparison method (`is_owner()`)
- File access validation method (`is_file_allowed()`)
- Absolute path resolution for security

#### Music Cog (`cogs/music.py`)
- Thread-safe playback with locks
- Periodic queue cleanup task
- Volume persistence
- Better error handling
- Security logging

#### Playlist Cog (`cogs/playlist.py`)
- Playlist name validation
- Type-safe owner checks
- Queue size validation before loading
- Failed song counter for user feedback
- Setup function for proper cog loading

#### Playlist Service (`services/playlist_service.py`)
- Atomic file operations
- Automatic backups
- Rollback on failures
- Data structure validation
- UTF-8 encoding support

#### Audio Service (`services/audio_service.py`)
- Rate limiting implementation
- Timeout protection
- Better error handling
- File validation for local sources
- Metadata extraction improvements

#### Song Model (`models/song.py`)
- Added `volume` field to `MusicQueue`
- Better type hints

### 🔄 MIGRATION NOTES

#### For Existing Users

1. **Create `config.json` from template:**
   ```bash
   cp config.example.json config.json
   # Edit config.json with your settings
   ```

2. **Update dependencies:**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

3. **Review security settings:**
   - Set `music_directory` if using local files
   - Adjust `max_queue_size` and `max_playlist_size` if needed
   - Review `allowed_file_extensions`

4. **Optional: Use environment variables (recommended for production):**
   ```bash
   export DISCORD_BOT_TOKEN="your_token"
   export DISCORD_OWNER_ID="your_user_id"
   ```

5. **Verify `.gitignore` is working:**
   ```bash
   git status  # config.json should NOT appear
   ```

### ⚠️ BREAKING CHANGES

- **Owner ID must now be an integer** (not string)
  - Old: `"owner_id": "123456789"`
  - New: `"owner_id": 123456789`
- **Configuration validation is now strict**
  - Invalid configurations will prevent bot startup
  - Better error messages guide you to fix issues

### 🎯 WHAT'S FIXED

This release addresses **ALL** of the following critical issues:

1. ✅ Logs directory tracked in Git
2. ✅ `__pycache__` directories tracked in Git
3. ✅ No config.example.json
4. ✅ Path traversal vulnerability
5. ✅ No input sanitization
6. ✅ Owner ID type confusion
7. ✅ Race condition in _play_next()
8. ✅ Memory leak (queues never cleaned)
9. ✅ Unhandled exceptions
10. ✅ Loop mode bug
11. ✅ Volume not persisted
12. ✅ Duplicate gitignore.txt
13. ✅ Missing PyNaCl dependency
14. ✅ No environment variable support
15. ✅ Playlist name validation
16. ✅ No rate limiting
17. ✅ Data corruption on write errors

### 📊 STATISTICS

- **Files Changed:** 11
- **Security Fixes:** 15+
- **Bug Fixes:** 17+
- **Lines Added:** ~2,500
- **Lines Removed:** ~500
- **New Features:** 10+

---

## [1.0.0] - Initial Release

### Added
- Basic music playback functionality
- YouTube streaming support
- Local file playback
- Queue management
- Playlist system
- Basic commands (play, pause, skip, etc.)

---

**For full commit history, see:** https://github.com/ModerateUser/Python_Discord_MusicBot/commits/security-bugfix-comprehensive
