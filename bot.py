"""
Discord Music Bot - Main Entry Point
A feature-rich music bot with security and playlist management
"""
import discord
from discord.ext import commands
import asyncio
import logging
import sys
import re
from pathlib import Path

from core.config import config
from utils.logger import setup_logger

# Setup logging
logger = setup_logger()

# Discord intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True  # For mention detection

def get_prefix(bot, message):
    """
    Dynamic prefix function that allows both custom prefix and bot mentions
    This allows users to use either !command or @bot command
    """
    # Allow both the configured prefix and bot mentions
    return commands.when_mentioned_or(config.command_prefix)(bot, message)

# Create bot instance with dynamic prefix
bot = commands.Bot(
    command_prefix=get_prefix,
    intents=intents,
    help_command=None  # We'll create a custom help command
)


@bot.event
async def on_ready():
    """Called when the bot is ready"""
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info(f'Connected to {len(bot.guilds)} guilds')
    logger.info(f'Command prefix: {config.command_prefix} or @{bot.user.name}')
    logger.info(f'Natural language prefix: !/ (when LLM is loaded)')
    
    # Set bot status
    activity = discord.Game(name=config.playing)
    await bot.change_presence(activity=activity)
    
    logger.info('Bot is ready!')


@bot.event
async def on_message(message):
    """Process messages for commands and natural language"""
    # Ignore messages from bots
    if message.author.bot:
        return
    
    # Log mentions for debugging
    if bot.user.mentioned_in(message):
        logger.debug(f'Bot mentioned by {message.author} in {message.guild}: {message.content}')
    
    # Check for natural language prefix (!/)
    if message.content.startswith('!/'):
        await handle_natural_language(message)
        return
    
    # Process regular commands
    await bot.process_commands(message)


async def handle_natural_language(message: discord.Message):
    """
    Handle natural language commands with !/ prefix
    Routes to LLM for interpretation when available
    """
    # Extract the natural language query
    query = message.content[2:].strip()  # Remove !/ prefix
    
    if not query:
        await message.reply("❌ Please provide a command after `!/`\n\nExample: `!/play something upbeat`")
        return
    
    # Get LLM service from AI Music cog
    ai_cog = bot.get_cog('AI Music')
    if not ai_cog or not await ai_cog.llm.is_available():
        await message.reply(
            "❌ Natural language commands require an LLM to be loaded.\n"
            "Use regular commands instead: `!play`, `!queue`, `!skip`, etc."
        )
        return
    
    # Show thinking indicator
    thinking_msg = await message.reply("🤔 Processing your request...")
    
    try:
        # Parse the natural language query to determine intent
        intent = await parse_natural_language_intent(query, ai_cog)
        
        if not intent:
            await thinking_msg.edit(content="❌ Could not understand your request. Try using regular commands.")
            return
        
        # Update thinking message with what we understood
        await thinking_msg.edit(content=f"🎵 {intent.get('thinking_message', 'Processing...')}")
        
        # Execute the interpreted command
        await execute_natural_language_command(message, intent, ai_cog, thinking_msg)
        
    except Exception as e:
        logger.error(f"Error handling natural language command: {e}", exc_info=True)
        await thinking_msg.edit(content=f"❌ Error processing your request: {str(e)}")


async def parse_natural_language_intent(query: str, ai_cog) -> dict:
    """
    Parse natural language query to determine user intent
    
    Returns:
        Dictionary with intent information or None if parsing fails
    """
    prompt = f"""Analyze this Discord music bot command and determine the user's intent.

User input: "{query}"

Determine:
1. command: The main command (play, skip, queue, pause, resume, stop, loop, volume, playlist, search, suggest)
2. parameters: Any parameters needed (song name, volume level, playlist name, etc.)
3. thinking_message: A brief message showing what you understood (max 100 chars)

Respond ONLY with valid JSON:
{{"command": "...", "parameters": {{}}, "thinking_message": "..."}}

Examples:
- "play something upbeat" → {{"command": "play", "parameters": {{"query": "upbeat music"}}, "thinking_message": "🎵 Searching for upbeat music"}}
- "what's in the queue" → {{"command": "queue", "parameters": {{}}, "thinking_message": "📝 Showing queue"}}
- "skip this" → {{"command": "skip", "parameters": {{}}, "thinking_message": "⏭️ Skipping song"}}
- "set volume to 50" → {{"command": "volume", "parameters": {{"level": 50}}, "thinking_message": "🔊 Setting volume to 50%"}}
- "suggest some jazz" → {{"command": "suggest", "parameters": {{"criteria": "jazz"}}, "thinking_message": "🎷 Suggesting jazz songs"}}
"""
    
    try:
        import json
        response = await ai_cog.llm._call_llm(prompt)
        intent = json.loads(response)
        return intent
    except Exception as e:
        logger.error(f"Error parsing natural language intent: {e}")
        return None


async def execute_natural_language_command(
    message: discord.Message,
    intent: dict,
    ai_cog,
    thinking_msg: discord.Message
):
    """
    Execute the interpreted command based on parsed intent
    """
    command = intent.get('command', '').lower()
    parameters = intent.get('parameters', {})
    
    music_cog = bot.get_cog('Music')
    queue_cog = bot.get_cog('QueueManager')
    playlist_cog = bot.get_cog('Playlist')
    
    try:
        if command == 'play':
            # Play a song
            query = parameters.get('query', '')
            if not query:
                await thinking_msg.edit(content="❌ Please specify what you want to play")
                return
            
            if music_cog:
                # Create a context-like object for the play command
                await thinking_msg.delete()
                await music_cog.play(message, query=query)
            else:
                await thinking_msg.edit(content="❌ Music system not available")
        
        elif command == 'skip':
            # Skip current song
            if music_cog:
                await thinking_msg.delete()
                await music_cog.skip(message)
            else:
                await thinking_msg.edit(content="❌ Music system not available")
        
        elif command == 'pause':
            # Pause playback
            if music_cog:
                await thinking_msg.delete()
                await music_cog.pause(message)
            else:
                await thinking_msg.edit(content="❌ Music system not available")
        
        elif command == 'resume':
            # Resume playback
            if music_cog:
                await thinking_msg.delete()
                await music_cog.resume(message)
            else:
                await thinking_msg.edit(content="❌ Music system not available")
        
        elif command == 'stop':
            # Stop playback
            if music_cog:
                await thinking_msg.delete()
                await music_cog.stop(message)
            else:
                await thinking_msg.edit(content="❌ Music system not available")
        
        elif command == 'queue':
            # Show queue
            if queue_cog:
                await thinking_msg.delete()
                await queue_cog.show_queue(message)
            else:
                await thinking_msg.edit(content="❌ Queue system not available")
        
        elif command == 'loop':
            # Toggle loop mode
            if music_cog:
                await thinking_msg.delete()
                await music_cog.loop(message)
            else:
                await thinking_msg.edit(content="❌ Music system not available")
        
        elif command == 'volume':
            # Set volume
            level = parameters.get('level')
            if level is not None:
                if music_cog:
                    await thinking_msg.delete()
                    await music_cog.volume(message, volume=level)
                else:
                    await thinking_msg.edit(content="❌ Music system not available")
            else:
                await thinking_msg.edit(content="❌ Please specify a volume level (0-100)")
        
        elif command == 'suggest':
            # Get suggestions
            criteria = parameters.get('criteria')
            if ai_cog:
                await thinking_msg.delete()
                await ai_cog.suggest(message, criteria=criteria)
            else:
                await thinking_msg.edit(content="❌ AI system not available")
        
        elif command == 'search':
            # Search for songs
            query = parameters.get('query', '')
            if query and music_cog:
                await thinking_msg.delete()
                await music_cog.search(message, query=query)
            else:
                await thinking_msg.edit(content="❌ Please specify what to search for")
        
        elif command == 'playlist':
            # Playlist commands
            action = parameters.get('action', 'list')
            name = parameters.get('name', '')
            
            if playlist_cog:
                await thinking_msg.delete()
                if action == 'list':
                    await playlist_cog.list_playlists(message)
                elif action == 'show' and name:
                    await playlist_cog.show_playlist(message, name=name)
                elif action == 'play' and name:
                    await playlist_cog.play_playlist(message, name=name)
                else:
                    await message.reply("❌ Invalid playlist command")
            else:
                await thinking_msg.edit(content="❌ Playlist system not available")
        
        else:
            await thinking_msg.edit(content=f"❌ Unknown command: {command}")
    
    except Exception as e:
        logger.error(f"Error executing natural language command: {e}", exc_info=True)
        try:
            await thinking_msg.edit(content=f"❌ Error executing command: {str(e)}")
        except:
            await message.reply(f"❌ Error executing command: {str(e)}")


@bot.event
async def on_voice_state_update(member, before, after):
    """Auto-disconnect if bot is alone in voice channel"""
    if member.id == bot.user.id:
        return
    
    voice_client = discord.utils.get(bot.voice_clients, guild=member.guild)
    if voice_client and len(voice_client.channel.members) == 1:
        logger.info(f'Auto-disconnecting from {voice_client.channel.name} (alone in channel)')
        await voice_client.disconnect()


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    """Global error handler"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f'❌ Command not found. Use `{config.command_prefix}help` or `@{bot.user.name} help` for available commands.')
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f'❌ Missing required argument: `{error.param.name}`')
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f'❌ Invalid argument provided.')
    elif isinstance(error, commands.CheckFailure):
        await ctx.send('❌ You do not have permission to use this command.')
    elif isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f'⏳ Command on cooldown. Try again in {error.retry_after:.1f}s')
    else:
        logger.error(f'Unhandled error in command {ctx.command}: {error}', exc_info=error)
        await ctx.send('❌ An error occurred while processing your command.')


@bot.command(name='ping')
async def ping(ctx: commands.Context):
    """Check bot latency"""
    latency = round(bot.latency * 1000)
    await ctx.send(f'🏓 Pong! Latency: {latency}ms')


@bot.command(name='info')
async def info(ctx: commands.Context):
    """Show bot information"""
    embed = discord.Embed(
        title='🎵 Music Bot Info',
        color=discord.Color.blue()
    )
    
    embed.add_field(name='Servers', value=len(bot.guilds), inline=True)
    embed.add_field(name='Users', value=len(bot.users), inline=True)
    embed.add_field(name='Prefix', value=f'{config.command_prefix} or @mention', inline=True)
    
    embed.add_field(
        name='Features',
        value='✅ YouTube Streaming\n✅ Local File Playback\n✅ Playlist Management\n✅ Queue System\n✅ Natural Language Commands',
        inline=False
    )
    
    embed.add_field(
        name='Usage',
        value=f'`{config.command_prefix}play <song>` or `@{bot.user.name} play <song>`\n`!/ <natural language>` (with LLM)',
        inline=False
    )
    
    embed.set_footer(text=f'Made with discord.py')
    
    await ctx.send(embed=embed)


async def load_cogs():
    """Load all cogs"""
    cogs = ['cogs.music', 'cogs.playlist', 'cogs.queue_manager', 'cogs.ai_music']
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f'Loaded cog: {cog}')
        except Exception as e:
            logger.error(f'Failed to load cog {cog}: {e}', exc_info=True)


async def main():
    """Main entry point"""
    async with bot:
        # Load cogs
        await load_cogs()
        
        # Start the bot
        try:
            logger.info('Starting bot...')
            await bot.start(config.token)
        except discord.LoginFailure:
            logger.error('Invalid bot token! Check your config.json')
            sys.exit(1)
        except Exception as e:
            logger.error(f'Failed to start bot: {e}', exc_info=True)
            sys.exit(1)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('Bot stopped by user')
    except Exception as e:
        logger.error(f'Fatal error: {e}', exc_info=True)
        sys.exit(1)
