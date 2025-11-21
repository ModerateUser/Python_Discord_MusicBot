"""
Bot initialization and setup
"""
import discord
from discord.ext import commands

def create_bot() -> commands.Bot:
    """Create and configure the bot instance"""
    intents = discord.Intents.default()
    intents.message_content = True
    intents.voice_states = True
    
    bot = commands.Bot(
        command_prefix=commands.when_mentioned,
        intents=intents,
        help_command=None
    )
    
    return bot
