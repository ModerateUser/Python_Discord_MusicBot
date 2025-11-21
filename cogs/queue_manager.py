"""
Queue management commands cog - FIXED VERSION
FIX #19: Corrected queue empty check to use proper boolean evaluation
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
        """
        Show the current queue
        
        FIX #19: Use proper boolean check instead of non-existent is_empty()
        """
        music_cog = self.get_music_cog()
        if not music_cog:
            await ctx.send('❌ Music system not available')
            return
        
        queue = music_cog.get_queue(ctx.guild.id)
        
        # FIX #19: MusicQueue implements __bool__() which returns True if:
        # - Queue has songs (len(self.songs) > 0), OR
        # - Currently playing (self.current is not None)
        # So we check: not queue.current AND len(queue) == 0 for truly empty
        if not queue.current and len(queue) == 0:
            await ctx.send('📭 Queue is empty')
            return
        
        embed = create_queue_embed(queue)
        await ctx.send(embed=embed)
    
    @commands.command(name='help')
    async def help_command(self, ctx):
        """Show all available commands"""
        embed = create_help_embed(self.bot.user.name)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """Setup function for cog loading"""
    await bot.add_cog(QueueManager(bot))
