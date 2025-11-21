"""
Discord Music Bot - Main Entry Point
Modular monolith architecture for maintainability
"""
import discord
from discord.ext import commands
import asyncio

from core.config import config
from core.bot_setup import create_bot
from cogs.music import Music
from cogs.queue_manager import QueueManager
from cogs.playlist import Playlist
from utils.logger import setup_logger

# Setup logging
logger = setup_logger()

async def main():
    """Main entry point for the bot"""
    # Create bot instance
    bot = create_bot()
    
    # Register event handlers
    @bot.event
    async def on_ready():
        logger.info(f'Logged in as {bot.user.name} ({bot.user.id})')
        logger.info(f'Mention the bot with commands: @{bot.user.name} help')
        if config.get('playing'):
            await bot.change_presence(activity=discord.Game(name=config['playing']))
    
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
    async def on_command_error(ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            await ctx.send(f"❌ Unknown command. Use `@{bot.user.name} help` for available commands")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: `{error.param.name}`")
        elif isinstance(error, commands.BadArgument):
            await ctx.send(f"❌ Invalid argument provided")
        else:
            logger.error(f"Command error: {error}", exc_info=error)
            await ctx.send("❌ An error occurred while executing the command")
    
    # Load cogs
    async with bot:
        await bot.add_cog(Music(bot))
        await bot.add_cog(QueueManager(bot))
        await bot.add_cog(Playlist(bot))
        
        logger.info("All cogs loaded successfully")
        
        # Start the bot
        await bot.start(config['token'])

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=e)