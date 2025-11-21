"""
AI-Enhanced Music Commands
Natural language music search and recommendations powered by LLM
"""
import discord
from discord.ext import commands
import logging
from typing import Optional

from services.llm_service import create_llm_service
from services.audio_service import audio_service
from utils.embeds import create_error_embed, create_success_embed

logger = logging.getLogger('discord_bot')


class AIMusicCog(commands.Cog, name="AI Music"):
    """AI-powered music commands using LLM"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
        # Initialize LLM service from bot config
        llm_config = getattr(bot, 'llm_config', None)
        self.llm = create_llm_service(llm_config)
        
        logger.info("AI Music cog loaded")
    
    @commands.command(name='aiplay', aliases=['ap', 'smartplay'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def ai_play(self, ctx: commands.Context, *, query: str):
        """
        Play music using natural language
        
        Examples:
            !aiplay something upbeat and energetic
            !aiplay calm piano music for studying
            !aiplay happy songs from the 80s
        """
        if not await self.llm.is_available():
            embed = create_error_embed(
                "AI Not Available",
                "AI features are disabled. Use `!play` for regular search."
            )
            await ctx.send(embed=embed)
            return
        
        # Show thinking message
        thinking_msg = await ctx.send("🤔 Understanding your request...")
        
        try:
            # Parse natural language query
            parsed = await self.llm.parse_music_query(query)
            
            if parsed.get('fallback'):
                await thinking_msg.edit(content="⚠️ AI unavailable, using direct search...")
            else:
                mood_info = f" (Mood: {parsed['mood']})" if parsed['mood'] else ""
                genre_info = f" (Genre: {parsed['genre']})" if parsed['genre'] else ""
                await thinking_msg.edit(
                    content=f"🎵 Searching for: **{parsed['search_query']}**{mood_info}{genre_info}"
                )
            
            # Use the music cog's play command with enhanced query
            music_cog = self.bot.get_cog('Music')
            if music_cog:
                # Call the regular play command with enhanced query
                await music_cog.play(ctx, query=parsed['search_query'])
                await thinking_msg.delete()
            else:
                embed = create_error_embed(
                    "Music Cog Not Found",
                    "The music playback system is not loaded."
                )
                await thinking_msg.edit(content=None, embed=embed)
                
        except Exception as e:
            logger.error(f"Error in AI play command: {e}", exc_info=True)
            embed = create_error_embed(
                "AI Error",
                f"Failed to process your request: {str(e)}"
            )
            await thinking_msg.edit(content=None, embed=embed)
    
    @commands.command(name='suggest', aliases=['recommend'])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def suggest(self, ctx: commands.Context, *, criteria: Optional[str] = None):
        """
        Get AI-powered song suggestions
        
        Examples:
            !suggest energetic workout music
            !suggest calm jazz
            !suggest happy pop songs
            !suggest (random suggestions)
        """
        if not await self.llm.is_available():
            embed = create_error_embed(
                "AI Not Available",
                "AI features are disabled. Enable LLM in configuration."
            )
            await ctx.send(embed=embed)
            return
        
        thinking_msg = await ctx.send("🤔 Generating suggestions...")
        
        try:
            # Parse criteria if provided
            mood = None
            genre = None
            
            if criteria:
                parsed = await self.llm.parse_music_query(criteria)
                mood = parsed.get('mood')
                genre = parsed.get('genre')
            
            # Generate suggestions
            suggestions = await self.llm.generate_playlist_suggestions(
                mood=mood,
                genre=genre,
                count=5
            )
            
            if not suggestions:
                embed = create_error_embed(
                    "No Suggestions",
                    "Failed to generate suggestions. Try again later."
                )
                await thinking_msg.edit(content=None, embed=embed)
                return
            
            # Create embed with suggestions
            criteria_text = criteria or "popular music"
            embed = discord.Embed(
                title="🎵 AI Music Suggestions",
                description=f"Based on: **{criteria_text}**",
                color=discord.Color.purple()
            )
            
            for i, song in enumerate(suggestions, 1):
                embed.add_field(
                    name=f"{i}. {song}",
                    value=f"Use `!play {song}` to play",
                    inline=False
                )
            
            embed.set_footer(text="Powered by AI • Use !aiplay for smart search")
            
            await thinking_msg.edit(content=None, embed=embed)
            
        except Exception as e:
            logger.error(f"Error in suggest command: {e}", exc_info=True)
            embed = create_error_embed(
                "Suggestion Error",
                f"Failed to generate suggestions: {str(e)}"
            )
            await thinking_msg.edit(content=None, embed=embed)
    
    @commands.command(name='songinfo', aliases=['info'])
    @commands.cooldown(1, 3, commands.BucketType.user)
    async def song_info(self, ctx: commands.Context, *, song_title: str):
        """
        Get AI-powered information about a song
        
        Example:
            !songinfo Bohemian Rhapsody
        """
        if not await self.llm.is_available():
            embed = create_error_embed(
                "AI Not Available",
                "AI features are disabled."
            )
            await ctx.send(embed=embed)
            return
        
        thinking_msg = await ctx.send("🔍 Looking up song information...")
        
        try:
            info = await self.llm.get_song_info(song_title)
            
            if not info:
                embed = create_error_embed(
                    "Not Found",
                    f"Could not find information about: {song_title}"
                )
                await thinking_msg.edit(content=None, embed=embed)
                return
            
            embed = discord.Embed(
                title=f"🎵 {song_title}",
                description=info.get('description', 'No description available'),
                color=discord.Color.blue()
            )
            
            if info.get('artist'):
                embed.add_field(name="Artist", value=info['artist'], inline=True)
            if info.get('genre'):
                embed.add_field(name="Genre", value=info['genre'], inline=True)
            if info.get('year'):
                embed.add_field(name="Year", value=info['year'], inline=True)
            
            embed.set_footer(text="Powered by AI")
            
            await thinking_msg.edit(content=None, embed=embed)
            
        except Exception as e:
            logger.error(f"Error in song info command: {e}", exc_info=True)
            embed = create_error_embed(
                "Info Error",
                f"Failed to get song information: {str(e)}"
            )
            await thinking_msg.edit(content=None, embed=embed)
    
    @commands.command(name='aistatus', aliases=['llmstatus'])
    async def ai_status(self, ctx: commands.Context):
        """Check AI service status"""
        is_available = await self.llm.is_available()
        
        embed = discord.Embed(
            title="🤖 AI Service Status",
            color=discord.Color.green() if is_available else discord.Color.red()
        )
        
        embed.add_field(
            name="Status",
            value="✅ Online" if is_available else "❌ Offline",
            inline=True
        )
        
        embed.add_field(
            name="Provider",
            value=self.llm.provider.value,
            inline=True
        )
        
        embed.add_field(
            name="Model",
            value=self.llm.model,
            inline=True
        )
        
        if is_available:
            embed.add_field(
                name="Available Commands",
                value=(
                    "`!aiplay <query>` - Smart music search\n"
                    "`!suggest [criteria]` - Get recommendations\n"
                    "`!songinfo <song>` - Song information"
                ),
                inline=False
            )
        else:
            embed.add_field(
                name="Note",
                value="AI features are disabled. Check configuration.",
                inline=False
            )
        
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    """Setup function for cog loading"""
    await bot.add_cog(AIMusicCog(bot))
