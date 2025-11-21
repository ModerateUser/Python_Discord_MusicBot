# Security Policy

## 🔒 Security Best Practices

This document outlines security best practices for deploying and using this Discord Music Bot.

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |

## Configuration Security

### ⚠️ NEVER Commit Sensitive Data

**CRITICAL:** Never commit the following files to Git:
- `config.json` - Contains your bot token
- `.env` - Contains environment variables
- `logs/` - May contain sensitive runtime data
- `playlists.json` - May contain private playlist data

These files are already in `.gitignore`, but always verify before committing.

### 🔑 Bot Token Protection

Your Discord bot token is like a password. If exposed:
1. **Immediately regenerate** your token at [Discord Developer Portal](https://discord.com/developers/applications)
2. Update your `config.json` or environment variables
3. Review your bot's recent activity for unauthorized use

**Best Practices:**
- Use environment variables instead of config files in production
- Never share your token in screenshots, logs, or error messages
- Rotate tokens periodically
- Use different tokens for development and production

### 🌍 Environment Variables (Recommended)

Instead of `config.json`, use environment variables:

```bash
export DISCORD_BOT_TOKEN="your_token_here"
export DISCORD_OWNER_ID="your_user_id"
export DISCORD_PLAYING="!help for commands"
export DISCORD_PREFIX="!"
```

Or create a `.env` file (already gitignored):
```env
DISCORD_BOT_TOKEN=your_token_here
DISCORD_OWNER_ID=123456789012345678
```

The bot will automatically use environment variables if available.

## File Access Security

### 🛡️ Local File Restrictions

The bot includes security features to prevent unauthorized file access:

1. **File Extension Whitelist**: Only allowed audio formats can be played
   - Default: `.mp3`, `.wav`, `.flac`, `.ogg`, `.m4a`, `.aac`, `.opus`
   - Configure in `config.json`: `allowed_file_extensions`

2. **Music Directory Restriction**: Optionally restrict file access to a specific directory
   ```json
   {
     "music_directory": "/path/to/safe/music/folder"
   }
   ```
   - Files outside this directory will be rejected
   - Prevents path traversal attacks (`../../../etc/passwd`)

3. **Path Validation**: All file paths are validated to prevent:
   - Directory traversal attempts
   - Access to system files
   - Symbolic link exploitation

### 📁 Recommended File Structure

```
/home/user/musicbot/
├── bot.py
├── config.json          # Restricted permissions (chmod 600)
├── music/               # Dedicated music directory
│   ├── song1.mp3
│   └── song2.flac
└── logs/                # Restricted permissions (chmod 700)
```

Set proper file permissions:
```bash
chmod 600 config.json    # Owner read/write only
chmod 700 logs/          # Owner access only
```

## Rate Limiting

The bot includes built-in rate limiting to prevent abuse:

- **YouTube API**: 10 requests per 60 seconds
- **Queue Size**: Configurable max (default: 100 songs)
- **Playlist Size**: Configurable max (default: 500 songs)

Configure in `config.json`:
```json
{
  "max_queue_size": 100,
  "max_playlist_size": 500
}
```

## Owner-Only Commands

Some commands are restricted to the bot owner (specified by `owner_id`):
- `!playlist delete` - Delete playlists

**Security Note:** The `owner_id` must be your Discord user ID (17-19 digit number), not your username.

To find your Discord user ID:
1. Enable Developer Mode in Discord (Settings → Advanced → Developer Mode)
2. Right-click your username and select "Copy ID"

## Input Validation

The bot validates all user inputs:

- **Playlist Names**: Alphanumeric, spaces, hyphens, underscores only (max 50 chars)
- **Search Queries**: Max 100 characters
- **URLs**: Max 500 characters
- **Volume**: 0-100 range
- **File Paths**: Validated against whitelist and directory restrictions

## Logging and Monitoring

The bot logs security events to help you monitor for suspicious activity:

- Blocked file access attempts
- Unauthorized command attempts
- Rate limit violations
- Configuration errors

**Review logs regularly** in the `logs/` directory.

**Log Security:**
- Logs may contain sensitive information
- Never commit logs to Git (already in `.gitignore`)
- Restrict log file permissions: `chmod 600 logs/*.log`
- Rotate logs periodically to prevent disk space issues

## Network Security

### 🌐 Firewall Recommendations

If running on a server:
- Only allow outbound connections (bot connects to Discord)
- No inbound ports need to be open
- Consider using a firewall (ufw, iptables, etc.)

### 🔒 HTTPS/TLS

- Discord API uses HTTPS by default
- YouTube downloads use HTTPS
- No additional TLS configuration needed

## Dependency Security

### 📦 Keep Dependencies Updated

Regularly update dependencies to patch security vulnerabilities:

```bash
pip install --upgrade -r requirements.txt
```

Check for known vulnerabilities:
```bash
pip install safety
safety check
```

### 🔍 Dependency Versions

Current dependencies with minimum versions:
- `discord.py[voice]>=2.3.0` - Discord API wrapper
- `yt-dlp>=2023.3.4` - YouTube downloader
- `PyNaCl>=1.5.0` - Voice encryption
- `python-dotenv>=1.0.0` - Environment variables

## Reporting Security Vulnerabilities

If you discover a security vulnerability:

1. **DO NOT** open a public GitHub issue
2. Email the maintainer directly (see repository owner)
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We will respond within 48 hours and work on a fix.

## Security Checklist

Before deploying your bot:

- [ ] Bot token is in `config.json` or environment variables (NOT in code)
- [ ] `config.json` has restricted permissions (chmod 600)
- [ ] `.gitignore` is properly configured
- [ ] `owner_id` is set to your Discord user ID
- [ ] `music_directory` is configured (if using local files)
- [ ] `allowed_file_extensions` is configured appropriately
- [ ] Dependencies are up to date
- [ ] Logs directory has restricted permissions
- [ ] Bot has minimal Discord permissions (only what it needs)
- [ ] Environment variables are used in production
- [ ] Regular backups of playlists (if important)

## Discord Bot Permissions

The bot requires these Discord permissions:
- **Read Messages/View Channels** - See commands
- **Send Messages** - Respond to commands
- **Connect** - Join voice channels
- **Speak** - Play audio
- **Use Voice Activity** - Transmit audio

**Security Tip:** Only grant necessary permissions. Avoid "Administrator" permission.

## Additional Resources

- [Discord Developer Documentation](https://discord.com/developers/docs)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

---

**Last Updated:** November 21, 2025  
**Version:** 1.0.0
