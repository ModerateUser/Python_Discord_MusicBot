"""
Bot Core - Main bot initialization and event handling
Simplified and modular bot entry point using dependency injection
"""
import discord
from discord.ext import commands
import asyncio
import logging
import sys
from pathlib import Path

from core.config import config
from core.service_manager import ServiceManager
from core.nlp_handler import NLPHandler
from utils.logger import setup_logger

# Setup logging
logger = setup_logger()


class MusicBot(commands.Bot):
    """
    Enhanced Discord Music Bot with dependency injection
    Supports natural language commands, AI features, and music synthesis
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the music bot"""
        super().__init__(*args, **kwargs)
        
        # Initialize managers
        self.service_manager = ServiceManager(self)
        self.nlp_handler = NLPHandler(self)
        
        # Set bot attributes from config
        self.llm_config = config.llm_config
    
    async def setup_hook(self):
        """Called when the bot is setting up"""
        logger.info("Setting up bot...")
        
        # Load cogs
        await self.load_cogs()
        
        # Initialize services
        await self.service_manager.initialize_all()
    
    async def load_cogs(self):
        """Load all cogs"""
        cogs = ['cogs.music', 'cogs.playlist', 'cogs.queue_manager', 'cogs.ai_music']
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f'✅ Loaded cog: {cog}')
            except Exception as e:
                logger.error(f'❌ Failed to load cog {cog}: {e}', exc_info=True)
    
    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'Logged in as {self.user.name} (ID: {self.user.id})')
        logger.info(f'Connected to {len(self.guilds)} guilds')
        logger.info(f'Command prefix: {config.command_prefix} or @{self.user.name}')
        logger.info(f'Natural language prefix: !/ (when LLM is loaded)')
        
        # Set bot status
        activity = discord.Game(name=config.playing)
        await self.change_presence(activity=activity)
        
        # Health check
        health = await self.service_manager.health_check()
        logger.info(f"Service health: {health}")
        
        logger.info('🎵 Bot is ready!')
    
    async def on_message(self, message: discord.Message):
        """Process messages for commands and natural language"""
        # Ignore messages from bots
        if message.author.bot:
            return
        
        # Log mentions for debugging
        if self.user.mentioned_in(message):
            logger.debug(f'Bot mentioned by {message.author} in {message.guild}: {message.content}')
        
        # Check for natural language prefix (!/)
        if message.content.startswith('!/'):
            await self.nlp_handler.handle_natural_language(message)
            return
        
        # Process regular commands
        await self.process_commands(message)
    
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ):
        """Auto-disconnect if bot is alone in voice channel"""
        if member.id == self.user.id:
            return
        
        voice_client = discord.utils.get(self.voice_clients, guild=member.guild)
        if voice_client and len(voice_client.channel.members) == 1:
            logger.info(f'Auto-disconnecting from {voice_client.channel.name} (alone in channel)')
            await voice_client.disconnect()
    
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(
                f'❌ Command not found. Use `{config.command_prefix}help` or '
                f'`@{self.user.name} help` for available commands.'
            )
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
    
    async def close(self):
        """Cleanup when bot is shutting down"""
        logger.info("Shutting down bot...")
        await self.service_manager.shutdown_all()
        await super().close()


def get_prefix(bot, message):
    """
    Dynamic prefix function that allows both custom prefix and bot mentions
    This allows users to use either !command or @bot command
    """
    return commands.when_mentioned_or(config.command_prefix)(bot, message)


def create_bot() -> MusicBot:
    """
    Create and configure the bot instance
    
    Returns:
        Configured MusicBot instance
    """
    # Discord intents
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    intents.guilds = True
    intents.members = True  # For mention detection
    
    # Create bot instance
    bot = MusicBot(
        command_prefix=get_prefix,
        intents=intents,
        help_command=None  # We'll create a custom help command
    )
    
    # Register basic commands
    register_basic_commands(bot)
    
    return bot


def register_basic_commands(bot: MusicBot):
    """Register basic bot commands"""
    
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
        
        # Check service availability
        synthesis_service = bot.service_manager.get_service('synthesis_service')
        advanced_ai_service = bot.service_manager.get_service('advanced_ai_service')
        
        ai_status = "✅ Enabled" if advanced_ai_service else "⚠️ Unavailable"
        synthesis_status = "✅ Enabled" if (
            synthesis_service and await synthesis_service.is_available()
        ) else "⚠️ Disabled"
        
        embed.add_field(
            name='Features',
            value=(
                f'✅ YouTube Streaming\n'
                f'✅ Local File Playback\n'
                f'✅ Playlist Management\n'
                f'✅ Queue System\n'
                f'✅ Natural Language Commands\n'
                f'{ai_status} Advanced AI Features\n'
                f'{synthesis_status} AI Music Synthesis'
            ),
            inline=False
        )
        
        embed.add_field(
            name='Usage',
            value=(
                f'`{config.command_prefix}play <song>` or `@{bot.user.name} play <song>`\n'
                f'`!/ <natural language>` (with LLM)'
            ),
            inline=False
        )
        
        if advanced_ai_service:
            embed.add_field(
                name='AI Features',
                value=(
                    '🎵 Mood playlists\n'
                    '🎧 Auto-DJ mode\n'
                    '🎼 Song analysis\n'
                    '🔍 Similar songs\n'
                    '📝 Lyrics\n'
                    '🎭 Mood transitions'
                ),
                inline=True
            )
        
        if synthesis_service and await synthesis_service.is_available():
            embed.add_field(
                name='Music Synthesis',
                value=(
                    f'🎼 AI Music Generation\n'
                    f'🎹 Backend: {synthesis_service.backend.value}\n'
                    f'🎨 Personalized Creation\n'
                    f'⚡ Context-Aware'
                ),
                inline=True
            )
        
        embed.set_footer(text=f'Made with discord.py')
        
        await ctx.send(embed=embed)
    
    @bot.command(name='health')
    async def health(ctx: commands.Context):
        """Check service health"""
        health_status = await bot.service_manager.health_check()
        
        embed = discord.Embed(
            title='🏥 Service Health Check',
            color=discord.Color.green()
        )
        
        for service, status in health_status.items():
            status_emoji = "✅" if status else "❌"
            embed.add_field(
                name=service.replace('_', ' ').title(),
                value=f"{status_emoji} {'Healthy' if status else 'Unavailable'}",
                inline=True
            )
        
        await ctx.send(embed=embed)


async def main():
    """Main entry point"""
    bot = create_bot()
    
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
