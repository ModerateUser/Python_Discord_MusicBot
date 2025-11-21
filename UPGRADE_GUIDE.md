# Upgrade Guide - v1.0.0 to v1.1.0

This guide will help you upgrade from version 1.0.0 to 1.1.0, which includes critical security fixes and bug fixes.

## ⚠️ IMPORTANT: Breaking Changes

### 1. Owner ID Type Change

**Old format (v1.0.0):**
```json
{
  "owner_id": "123456789012345678"
}
```

**New format (v1.1.0):**
```json
{
  "owner_id": 123456789012345678
}
```

**Action Required:** Remove quotes around your owner_id in `config.json`

### 2. Strict Configuration Validation

The bot now validates all configuration fields. Invalid configurations will prevent startup with helpful error messages.

**Common issues:**
- Token too short (must be 50+ characters)
- Owner ID not a valid Discord snowflake (17-19 digits)
- Invalid file paths in `music_directory`

## 📋 Step-by-Step Upgrade Process

### Step 1: Backup Your Data

```bash
# Backup your current configuration and playlists
cp config.json config.json.backup
cp playlists.json playlists.json.backup 2>/dev/null || true
```

### Step 2: Pull Latest Changes

```bash
# If you cloned the repository
git fetch origin
git checkout security-bugfix-comprehensive
git pull origin security-bugfix-comprehensive

# Or download the latest release
```

### Step 3: Update Dependencies

```bash
# Update all dependencies
pip install --upgrade -r requirements.txt

# Verify installation
pip list | grep -E "discord.py|yt-dlp|PyNaCl|python-dotenv"
```

Expected output:
```
discord.py        2.3.0 (or higher)
yt-dlp            2023.3.4 (or higher)
PyNaCl            1.5.0 (or higher)
python-dotenv     1.0.0 (or higher)
```

### Step 4: Update Configuration

#### Option A: Update Existing config.json

1. **Fix owner_id type:**
   ```bash
   # Edit config.json
   nano config.json
   ```
   
   Change:
   ```json
   "owner_id": "123456789012345678"
   ```
   
   To:
   ```json
   "owner_id": 123456789012345678
   ```

2. **Add new optional fields:**
   ```json
   {
     "token": "your_token_here",
     "owner_id": 123456789012345678,
     "playing": "!help for commands",
     "command_prefix": "!",
     "max_queue_size": 100,
     "max_playlist_size": 500,
     "allowed_file_extensions": [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus"],
     "music_directory": null
   }
   ```

#### Option B: Use Environment Variables (Recommended)

Create a `.env` file:
```bash
cat > .env << EOF
DISCORD_BOT_TOKEN=your_token_here
DISCORD_OWNER_ID=123456789012345678
DISCORD_PLAYING=!help for commands
DISCORD_PREFIX=!
EOF

# Secure the file
chmod 600 .env
```

Then you can delete `config.json` (the bot will use environment variables).

### Step 5: Configure Security Settings

#### For Local File Playback

If you play local audio files, configure a dedicated music directory:

```json
{
  "music_directory": "/home/user/musicbot/music",
  "allowed_file_extensions": [".mp3", ".wav", ".flac", ".ogg"]
}
```

Create the directory:
```bash
mkdir -p /home/user/musicbot/music
chmod 755 /home/user/musicbot/music
```

#### Set Proper File Permissions

```bash
# Secure configuration file
chmod 600 config.json

# Secure logs directory
chmod 700 logs/

# Secure environment file (if using)
chmod 600 .env
```

### Step 6: Verify .gitignore

Ensure sensitive files won't be committed:

```bash
# Check git status
git status

# These should NOT appear:
# - config.json
# - .env
# - logs/
# - __pycache__/
```

If they appear, run:
```bash
# Remove from git tracking (keeps local files)
git rm --cached config.json
git rm --cached -r logs/
git rm --cached -r __pycache__/
```

### Step 7: Test the Bot

```bash
# Start the bot
python bot.py
```

**Expected startup messages:**
```
INFO - Loaded X playlists
INFO - Bot is ready!
INFO - Logged in as: YourBotName#1234
```

**If you see errors:**
- Check configuration format (owner_id as integer)
- Verify token is valid
- Check file permissions
- Review logs in `logs/` directory

### Step 8: Test Core Functionality

Run these tests in Discord:

1. **Basic Commands:**
   ```
   !join
   !play never gonna give you up
   !pause
   !resume
   !skip
   !leave
   ```

2. **Volume Persistence (NEW):**
   ```
   !play song1
   !volume 75
   !skip
   # Volume should remain at 75% for next song
   ```

3. **Playlist Commands:**
   ```
   !playlist create TestPlaylist
   !playlist add TestPlaylist https://youtube.com/...
   !playlist show TestPlaylist
   !playlist play TestPlaylist
   ```

4. **Security Features:**
   ```
   # Try to access a file outside music_directory
   !play /etc/passwd
   # Should be blocked with error message
   ```

## 🆕 New Features You Can Use

### 1. Environment Variables

Instead of `config.json`, use environment variables:

```bash
export DISCORD_BOT_TOKEN="your_token"
export DISCORD_OWNER_ID="123456789012345678"
python bot.py
```

### 2. Music Directory Restriction

Restrict file access to a specific directory:

```json
{
  "music_directory": "/path/to/music"
}
```

### 3. Configurable Limits

Adjust queue and playlist sizes:

```json
{
  "max_queue_size": 200,
  "max_playlist_size": 1000
}
```

### 4. Volume Persistence

Volume now persists between songs automatically!

### 5. Better Error Messages

The bot now provides helpful error messages for configuration issues.

## 🔍 Troubleshooting

### Issue: "owner_id must be an integer"

**Solution:** Remove quotes around owner_id in config.json
```json
"owner_id": 123456789012345678  ✅
"owner_id": "123456789012345678"  ❌
```

### Issue: "Bot token appears invalid"

**Solution:** 
1. Verify token at [Discord Developer Portal](https://discord.com/developers/applications)
2. Regenerate token if needed
3. Ensure no extra spaces or quotes

### Issue: "music_directory does not exist"

**Solution:**
```bash
# Create the directory
mkdir -p /path/to/music

# Or set to null in config.json
"music_directory": null
```

### Issue: "This file is not allowed"

**Solution:** Check file extension is in `allowed_file_extensions`:
```json
{
  "allowed_file_extensions": [".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus"]
}
```

### Issue: Bot crashes on playback

**Solution:**
1. Update dependencies: `pip install --upgrade -r requirements.txt`
2. Check FFmpeg is installed: `ffmpeg -version`
3. Review logs in `logs/` directory

### Issue: "Rate limit reached"

**Solution:** This is normal protection. Wait 60 seconds or adjust in code if needed.

## 📊 What's Fixed in This Version

✅ **Security Fixes:**
- Path traversal vulnerability
- Token exposure prevention
- Input validation
- File access restrictions
- Owner ID type confusion

✅ **Critical Bugs:**
- Race conditions in playback
- Memory leaks
- Volume not persisting
- Loop mode issues
- Data corruption
- Unhandled exceptions

✅ **Improvements:**
- Rate limiting
- Better error handling
- Comprehensive logging
- Environment variable support
- Atomic file operations

## 🔄 Rollback Instructions

If you need to rollback to v1.0.0:

```bash
# Restore backups
cp config.json.backup config.json
cp playlists.json.backup playlists.json

# Checkout old version
git checkout master  # or your previous branch

# Downgrade dependencies
pip install discord.py==2.3.0 yt-dlp==2023.3.4
```

**Note:** You'll lose the security fixes and bug fixes.

## 📚 Additional Resources

- [SECURITY.md](SECURITY.md) - Security best practices
- [CHANGELOG.md](CHANGELOG.md) - Complete list of changes
- [README.md](README.md) - General documentation

## ✅ Post-Upgrade Checklist

- [ ] Dependencies updated
- [ ] config.json updated (owner_id as integer)
- [ ] File permissions set (chmod 600 config.json)
- [ ] .gitignore working (config.json not tracked)
- [ ] Bot starts without errors
- [ ] Basic commands work
- [ ] Volume persists between songs
- [ ] Playlists load correctly
- [ ] Security features tested
- [ ] Logs directory created and secured

## 🎉 You're Done!

Your bot is now upgraded with critical security fixes and improvements. Enjoy the enhanced stability and security!

If you encounter any issues not covered in this guide, please:
1. Check the logs in `logs/` directory
2. Review [SECURITY.md](SECURITY.md) for security settings
3. Open an issue on GitHub with details

---

**Upgrade completed on:** November 21, 2025  
**Version:** 1.0.0 → 1.1.0
