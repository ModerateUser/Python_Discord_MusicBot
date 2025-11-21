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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('discord_bot')

# Discord intents
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True

# Create bot instance
bot = commands.Bot(
    command_prefix=config.command_prefix,
    intents=intents,
    help_command=None  # We'll create a custom help command
)


@bot.event
async def on_ready():
    """Called when the bot is ready"""
    logger.info(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    logger.info(f'Connected to {len(bot.guilds)} guilds')
    
    # Set bot status
    activity = discord.Game(name=config.playing)
    await bot.change_presence(activity=activity)
    
    logger.info('Bot is ready!')


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.CommandError):
    """Global error handler"""
    if isinstance(error, commands.CommandNotFound):
        await ctx.send(f'❌ Command not found. Use `{config.command_prefix}help` for available commands.')
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


@bot.command(name='help')
async def help_command(ctx: commands.Context, command: str = None):
    """Show help information"""
    embed = discord.Embed(
        title='🎵 Music Bot Help',
        description='A feature-rich Discord music bot',
        color=discord.Color.blue()
    )
    
    if command:
        # Show help for specific command
        cmd = bot.get_command(command)
        if cmd:
            embed.add_field(
                name=f'{config.command_prefix}{cmd.name}',
                value=cmd.help or 'No description available',
                inline=False
            )
        else:
            await ctx.send(f'❌ Command `{command}` not found.')
            return
    else:
        # Show all commands
        embed.add_field(
            name='🎵 Music Commands',
            value=(
                f'`{config.command_prefix}play <song/url>` - Play a song\n'
                f'`{config.command_prefix}pause` - Pause playback\n'
                f'`{config.command_prefix}resume` - Resume playback\n'
                f'`{config.command_prefix}skip` - Skip current song\n'
                f'`{config.command_prefix}stop` - Stop and clear queue\n'
                f'`{config.command_prefix}queue` - Show queue\n'
                f'`{config.command_prefix}nowplaying` - Show current song\n'
                f'`{config.command_prefix}volume <0-100>` - Set volume\n'
                f'`{config.command_prefix}loop` - Toggle loop mode\n'
                f'`{config.command_prefix}search <query>` - Search YouTube'
            ),
            inline=False
        )
        
        embed.add_field(
            name='📚 Playlist Commands',
            value=(
                f'`{config.command_prefix}playlist create <name>` - Create playlist\n'
                f'`{config.command_prefix}playlist add <name> <song>` - Add to playlist\n'
                f'`{config.command_prefix}playlist play <name>` - Play playlist\n'
                f'`{config.command_prefix}playlist list` - List playlists\n'
                f'`{config.command_prefix}playlist show <name>` - Show playlist songs\n'
                f'`{config.command_prefix}playlist delete <name>` - Delete playlist (owner)'
            ),
            inline=False
        )
        
        embed.add_field(
            name='🔊 Voice Commands',
            value=(
                f'`{config.command_prefix}join` - Join your voice channel\n'
                f'`{config.command_prefix}leave` - Leave voice channel'
            ),
            inline=False
        )
        
        embed.set_footer(text=f'Use {config.command_prefix}help <command> for more info on a command')
    
    await ctx.send(embed=embed)


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
    embed.add_field(name='Prefix', value=config.command_prefix, inline=True)
    
    embed.add_field(
        name='Features',
        value='✅ YouTube Streaming\n✅ Local File Playback\n✅ Playlist Management\n✅ Queue System',
        inline=False
    )
    
    embed.set_footer(text=f'Made with discord.py')
    
    await ctx.send(embed=embed)


async def load_cogs():
    """Load all cogs"""
    cogs = ['cogs.music', 'cogs.playlist']
    
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
