"""
Discord Music Bot - Main Entry Point
A feature-rich music bot with security and playlist management
"""
import discord
from discord.ext import commands
import asyncio
import logging
import sys
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
    
    # Set bot status
    activity = discord.Game(name=config.playing)
    await bot.change_presence(activity=activity)
    
    logger.info('Bot is ready!')


@bot.event
async def on_message(message):
    """Process messages for commands"""
    # Ignore messages from bots
    if message.author.bot:
        return
    
    # Log mentions for debugging
    if bot.user.mentioned_in(message):
        logger.debug(f'Bot mentioned by {message.author} in {message.guild}: {message.content}')
    
    # Process commands
    await bot.process_commands(message)


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
        value='✅ YouTube Streaming\n✅ Local File Playback\n✅ Playlist Management\n✅ Queue System',
        inline=False
    )
    
    embed.add_field(
        name='Usage',
        value=f'`{config.command_prefix}play <song>` or `@{bot.user.name} play <song>`',
        inline=False
    )
    
    embed.set_footer(text=f'Made with discord.py')
    
    await ctx.send(embed=embed)


async def load_cogs():
    """Load all cogs"""
    cogs = ['cogs.music', 'cogs.playlist', 'cogs.queue_manager']
    
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
