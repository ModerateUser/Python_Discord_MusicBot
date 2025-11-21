"""
Discord Music Bot - Main Entry Point
A feature-rich music bot with security, playlist management, and advanced AI features
Includes AI music synthesis capabilities
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

# Global references
advanced_ai_service = None
synthesis_service = None

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
    
    # Initialize services
    await initialize_services()
    
    # Set bot status
    activity = discord.Game(name=config.playing)
    await bot.change_presence(activity=activity)
    
    logger.info('Bot is ready!')


async def initialize_services():
    """Initialize all AI services"""
    global advanced_ai_service, synthesis_service
    
    # Initialize music synthesis service
    try:
        from services.music_synthesis_service import create_music_synthesis_service
        
        ai_cog = bot.get_cog('AI Music')
        llm_service = ai_cog.llm if ai_cog else None
        
        synthesis_service = create_music_synthesis_service(config.config, llm_service)
        
        if await synthesis_service.is_available():
            logger.info(f'✅ Music Synthesis Service initialized (Backend: {synthesis_service.backend.value})')
        else:
            logger.info('⚠️ Music synthesis disabled (check config.json)')
    except Exception as e:
        logger.warning(f'⚠️ Music synthesis unavailable: {e}')
        synthesis_service = None
    
    # Initialize advanced AI service
    await initialize_advanced_ai_service()


async def initialize_advanced_ai_service():
    """Initialize the advanced AI music service"""
    global advanced_ai_service
    
    ai_cog = bot.get_cog('AI Music')
    if ai_cog and await ai_cog.llm.is_available():
        from services.ai_music_service import create_advanced_ai_service
        advanced_ai_service = create_advanced_ai_service(ai_cog.llm, synthesis_service)
        logger.info('✅ Advanced AI Music Service initialized')
    else:
        logger.info('⚠️ Advanced AI features unavailable (LLM not loaded)')


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
    Supports complex action chaining and advanced AI features including music synthesis
    """
    # Extract the natural language query
    query = message.content[2:].strip()  # Remove !/ prefix
    
    if not query:
        await message.reply("❌ Please provide a command after `!/`\n\nExample: `!/play something upbeat`")
        return
    
    # Get AI cog and check LLM availability
    ai_cog = bot.get_cog('AI Music')
    if not ai_cog or not await ai_cog.llm.is_available():
        await message.reply(
            "❌ Natural language commands require an LLM to be loaded.\n"
            "Use regular commands instead: `!play`, `!queue`, `!skip`, etc."
        )
        return
    
    # Ensure advanced AI service is initialized
    if not advanced_ai_service:
        await initialize_advanced_ai_service()
    
    # Show thinking indicator
    thinking_msg = await message.reply("🤔 Analyzing your request...")
    
    try:
        # Check if this is a complex command (contains "then", "after", "and then", etc.)
        is_complex = any(keyword in query.lower() for keyword in [
            'then', 'after', 'and then', 'followed by', 'next', 'create', 'generate',
            'auto-dj', 'auto dj', 'similar', 'like', 'mood', 'transition', 'shuffle',
            'synthesize', 'compose', 'make music', 'original'
        ])
        
        if is_complex and advanced_ai_service:
            # Parse complex intent with action chaining
            await thinking_msg.edit(content="🧠 Parsing complex command...")
            actions = await advanced_ai_service.parse_complex_intent(query, message.guild.id)
            
            if not actions:
                await thinking_msg.edit(content="❌ Could not understand your request. Try using simpler language.")
                return
            
            # Show what we understood
            action_summary = "\n".join([f"• {action.description}" for action in actions[:3]])
            if len(actions) > 3:
                action_summary += f"\n• ... and {len(actions) - 3} more actions"
            
            await thinking_msg.edit(content=f"✅ Understood! Planning:\n{action_summary}\n\n⚙️ Executing...")
            
            # Execute complex action chain
            await execute_complex_actions(message, actions, thinking_msg)
        else:
            # Simple command - use original parsing
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


async def execute_complex_actions(
    message: discord.Message,
    actions: list,
    status_msg: discord.Message
):
    """
    Execute a chain of complex actions
    
    Args:
        message: Original Discord message
        actions: List of Action objects to execute
        status_msg: Status message to update
    """
    from services.ai_music_service import ActionType, TriggerType
    
    guild_id = message.guild.id
    queue = advanced_ai_service.get_queue(guild_id)
    
    # Separate immediate and delayed actions
    immediate_actions = [a for a in actions if a.trigger == TriggerType.IMMEDIATE]
    delayed_actions = [a for a in actions if a.trigger != TriggerType.IMMEDIATE]
    
    # Queue delayed actions
    for action in delayed_actions:
        queue.add_action(action)
    
    # Execute immediate actions
    for i, action in enumerate(immediate_actions):
        try:
            await status_msg.edit(content=f"⚙️ Executing: {action.description} ({i+1}/{len(immediate_actions)})")
            await execute_single_action(message, action, status_msg)
            await asyncio.sleep(0.5)  # Brief pause between actions
        except Exception as e:
            logger.error(f"Error executing action {action.action_type}: {e}")
            await message.channel.send(f"⚠️ Error with action: {action.description}\n{str(e)}")
    
    # Final status
    if delayed_actions:
        delayed_summary = "\n".join([f"• {a.description}" for a in delayed_actions[:3]])
        await status_msg.edit(content=f"✅ Immediate actions complete!\n\n⏰ Scheduled:\n{delayed_summary}")
    else:
        await status_msg.edit(content="✅ All actions completed!")


async def execute_single_action(
    message: discord.Message,
    action,
    status_msg: discord.Message
):
    """Execute a single action from the action chain"""
    from services.ai_music_service import ActionType
    
    music_cog = bot.get_cog('Music')
    queue_cog = bot.get_cog('QueueManager')
    playlist_cog = bot.get_cog('Playlist')
    ai_cog = bot.get_cog('AI Music')
    
    if action.action_type == ActionType.PLAY:
        query = action.parameters.get('query', '')
        if query and music_cog:
            await music_cog.play(message, query=query)
    
    elif action.action_type == ActionType.SKIP:
        if music_cog:
            await music_cog.skip(message)
    
    elif action.action_type == ActionType.PAUSE:
        if music_cog:
            await music_cog.pause(message)
    
    elif action.action_type == ActionType.RESUME:
        if music_cog:
            await music_cog.resume(message)
    
    elif action.action_type == ActionType.STOP:
        if music_cog:
            await music_cog.stop(message)
    
    elif action.action_type == ActionType.VOLUME:
        level = action.parameters.get('level')
        if level is not None and music_cog:
            await music_cog.volume(message, volume=level)
    
    elif action.action_type == ActionType.LOOP:
        if music_cog:
            await music_cog.loop(message)
    
    elif action.action_type == ActionType.SYNTHESIZE_MUSIC:
        # NEW: AI Music Synthesis
        if not synthesis_service or not await synthesis_service.is_available():
            await message.channel.send("❌ Music synthesis not available. Check config.json to enable it.")
            return
        
        prompt = action.parameters.get('prompt', '')
        style = action.parameters.get('style')
        mood = action.parameters.get('mood')
        duration = action.parameters.get('duration', 30)
        use_history = action.parameters.get('use_history', True)
        
        if not prompt:
            await message.channel.send("❌ No prompt provided for music synthesis")
            return
        
        # Show synthesis progress
        synth_msg = await message.channel.send(f"🎼 Synthesizing music: **{prompt}**\n⏳ This may take 30-120 seconds...")
        
        try:
            # Synthesize music
            file_path = await advanced_ai_service.synthesize_music(
                prompt=prompt,
                guild_id=message.guild.id,
                style=style,
                mood=mood,
                duration=duration,
                use_history=use_history
            )
            
            if file_path:
                await synth_msg.edit(content=f"✅ Music synthesized successfully!\n🎵 Playing: **{prompt}**")
                
                # Play the synthesized music
                if music_cog:
                    # Use local file playback
                    await music_cog.play(message, query=file_path)
                else:
                    await message.channel.send("❌ Music cog not available to play synthesized audio")
            else:
                await synth_msg.edit(content="❌ Music synthesis failed. Check logs for details.")
        
        except Exception as e:
            logger.error(f"Error in music synthesis action: {e}", exc_info=True)
            await synth_msg.edit(content=f"❌ Synthesis error: {str(e)}")
    
    elif action.action_type == ActionType.GENERATE_PLAYLIST:
        # Generate AI playlist
        mood = action.parameters.get('mood', 'varied')
        genre = action.parameters.get('genre')
        count = action.parameters.get('count', 10)
        
        songs = await advanced_ai_service.generate_mood_playlist(mood, genre, count)
        
        if songs:
            await message.channel.send(f"🎵 Generated {len(songs)}-song playlist for mood: **{mood}**")
            # Add songs to queue
            for song in songs:
                if music_cog:
                    await music_cog.play(message, query=song)
        else:
            await message.channel.send("❌ Could not generate playlist")
    
    elif action.action_type == ActionType.ANALYZE_SONG:
        # Analyze current song
        if music_cog and hasattr(music_cog, 'current_song'):
            song_title = action.parameters.get('song') or getattr(music_cog, 'current_song', 'Unknown')
            analysis = await advanced_ai_service.analyze_song(song_title)
            
            embed = discord.Embed(title=f"🎵 Song Analysis: {song_title}", color=discord.Color.blue())
            if analysis.mood:
                embed.add_field(name="Mood", value=analysis.mood, inline=True)
            if analysis.tempo:
                embed.add_field(name="Tempo", value=f"{analysis.tempo} BPM", inline=True)
            if analysis.energy:
                embed.add_field(name="Energy", value=f"{analysis.energy:.1%}", inline=True)
            if analysis.genre:
                embed.add_field(name="Genre", value=analysis.genre, inline=True)
            if analysis.tags:
                embed.add_field(name="Tags", value=", ".join(analysis.tags), inline=False)
            
            await message.channel.send(embed=embed)
    
    elif action.action_type == ActionType.FIND_SIMILAR:
        # Find similar songs
        reference = action.parameters.get('reference_song', '')
        count = action.parameters.get('count', 5)
        
        similar_songs = await advanced_ai_service.find_similar_songs(reference, count=count)
        
        if similar_songs:
            await message.channel.send(f"🎵 Found {len(similar_songs)} songs similar to **{reference}**:")
            for i, song in enumerate(similar_songs, 1):
                await message.channel.send(f"{i}. {song}")
                if music_cog:
                    await music_cog.play(message, query=song)
        else:
            await message.channel.send("❌ Could not find similar songs")
    
    elif action.action_type == ActionType.AUTO_DJ:
        # Enable Auto-DJ mode
        mood = action.parameters.get('mood', 'varied')
        await message.channel.send(f"🎧 Auto-DJ mode activated! Mood: **{mood}**")
        
        # Start Auto-DJ loop (simplified - would need proper implementation)
        for _ in range(5):  # Queue 5 songs
            next_song = await advanced_ai_service.get_auto_dj_next_song(message.guild.id, mood)
            if next_song and music_cog:
                await music_cog.play(message, query=next_song)
    
    elif action.action_type == ActionType.FETCH_LYRICS:
        # Fetch lyrics
        song = action.parameters.get('song', '')
        artist = action.parameters.get('artist')
        
        lyrics = await advanced_ai_service.fetch_lyrics(song, artist)
        
        if lyrics:
            # Split lyrics if too long
            if len(lyrics) > 2000:
                lyrics = lyrics[:1997] + "..."
            
            embed = discord.Embed(
                title=f"📝 Lyrics: {song}",
                description=lyrics,
                color=discord.Color.green()
            )
            await message.channel.send(embed=embed)
        else:
            await message.channel.send("❌ Lyrics not available")
    
    elif action.action_type == ActionType.MOOD_TRANSITION:
        # Create mood transition playlist
        from_mood = action.parameters.get('from_mood', 'calm')
        to_mood = action.parameters.get('to_mood', 'energetic')
        duration = action.parameters.get('duration_songs', 10)
        
        songs = await advanced_ai_service.create_mood_transition_playlist(from_mood, to_mood, duration)
        
        if songs:
            await message.channel.send(f"🎵 Created mood transition: **{from_mood}** → **{to_mood}** ({len(songs)} songs)")
            for song in songs:
                if music_cog:
                    await music_cog.play(message, query=song)
        else:
            await message.channel.send("❌ Could not create mood transition")
    
    elif action.action_type == ActionType.SMART_SHUFFLE:
        # Smart shuffle current queue
        await message.channel.send("🔀 Smart shuffling queue...")
        # Would need to get current queue and reorder
        # This is a placeholder for the actual implementation


async def parse_natural_language_intent(query: str, ai_cog) -> dict:
    """
    Parse natural language query to determine user intent (simple commands)
    
    Returns:
        Dictionary with intent information or None if parsing fails
    """
    prompt = f"""Analyze this Discord music bot command and determine the user's intent.

User input: "{query}"

Determine:
1. command: The main command (play, skip, queue, pause, resume, stop, loop, volume, playlist, search, suggest, synthesize)
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
- "synthesize chill music" → {{"command": "synthesize", "parameters": {{"prompt": "chill music", "mood": "relaxed"}}, "thinking_message": "🎼 Synthesizing chill music"}}
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
    Execute the interpreted command based on parsed intent (simple commands)
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
        
        elif command == 'synthesize':
            # Synthesize music
            if not synthesis_service or not await synthesis_service.is_available():
                await thinking_msg.edit(content="❌ Music synthesis not available. Check config.json to enable it.")
                return
            
            prompt = parameters.get('prompt', '')
            if not prompt:
                await thinking_msg.edit(content="❌ Please specify what kind of music to synthesize")
                return
            
            await thinking_msg.edit(content=f"🎼 Synthesizing: **{prompt}**\n⏳ This may take 30-120 seconds...")
            
            # Synthesize music
            file_path = await advanced_ai_service.synthesize_music(
                prompt=prompt,
                guild_id=message.guild.id,
                style=parameters.get('style'),
                mood=parameters.get('mood'),
                duration=parameters.get('duration', 30),
                use_history=True
            )
            
            if file_path:
                await thinking_msg.edit(content=f"✅ Music synthesized!\n🎵 Playing: **{prompt}**")
                if music_cog:
                    await music_cog.play(message, query=file_path)
            else:
                await thinking_msg.edit(content="❌ Music synthesis failed")
        
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
    
    ai_status = "✅ Enabled" if advanced_ai_service else "⚠️ Unavailable"
    synthesis_status = "✅ Enabled" if (synthesis_service and await synthesis_service.is_available()) else "⚠️ Disabled"
    
    embed.add_field(
        name='Features',
        value=f'✅ YouTube Streaming\n✅ Local File Playback\n✅ Playlist Management\n✅ Queue System\n✅ Natural Language Commands\n{ai_status} Advanced AI Features\n{synthesis_status} AI Music Synthesis',
        inline=False
    )
    
    embed.add_field(
        name='Usage',
        value=f'`{config.command_prefix}play <song>` or `@{bot.user.name} play <song>`\n`!/ <natural language>` (with LLM)',
        inline=False
    )
    
    if advanced_ai_service:
        embed.add_field(
            name='AI Features',
            value='🎵 Mood playlists\n🎧 Auto-DJ mode\n🎼 Song analysis\n🔍 Similar songs\n📝 Lyrics\n🎭 Mood transitions',
            inline=True
        )
    
    if synthesis_service and await synthesis_service.is_available():
        embed.add_field(
            name='Music Synthesis',
            value=f'🎼 AI Music Generation\n🎹 Backend: {synthesis_service.backend.value}\n🎨 Personalized Creation\n⚡ Context-Aware',
            inline=True
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
