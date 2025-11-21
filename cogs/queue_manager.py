"""
Queue management commands cog
"""
import discord
from discord.ext import commands

from utils.embeds import create_queue_embed, create_help_embed

class QueueManager(commands.Cog):
    """Queue management commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def get_music_cog(self):
        """Get the Music cog to access queues"""
        return self.bot.get_cog('Music')
    
    @commands.command(name='queue', aliases=['q'])
    async def show_queue(self, ctx):
        """Show the current queue"""
        music_cog = self.get_music_cog()
        if not music_cog:
            await ctx.send('❌ Music system not available')
            return
        
        queue = music_cog.get_queue(ctx.guild.id)
        
        if queue.is_empty():
            await ctx.send('📭 Queue is empty')
            return
        
        embed = create_queue_embed(queue)
        await ctx.send(embed=embed)
    
    @commands.command(name='help')
    async def help_command(self, ctx):
        """Show all available commands"""
        embed = create_help_embed(self.bot.user.name)
        await ctx.send(embed=embed)
