"""
Help Command Cog
Provides comprehensive help system for all bot commands

FIX MEDIUM #2: Implement comprehensive help command system
"""
import discord
from discord.ext import commands
from typing import Optional, List, Dict
import logging

logger = logging.getLogger('discord_bot')


class HelpCog(commands.Cog, name="Help"):
    """Help and documentation commands"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Command categories with descriptions
        self.categories = {
            "Music": "🎵 Music playback and queue management",
            "Playlist": "📝 Playlist creation and management",
            "AI Music": "🤖 AI-powered music features",
            "Queue": "📋 Advanced queue management",
            "Utility": "🔧 Bot information and utilities",
            "Help": "❓ Help and documentation"
        }
        
        # Detailed command information
        self.command_details = {
            # Music commands
            "play": {
                "category": "Music",
                "usage": "!play <song name or URL>",
                "aliases": ["p"],
                "description": "Play a song from YouTube or local file",
                "examples": [
                    "!play never gonna give you up",
                    "!play https://youtube.com/watch?v=...",
                    "!play mysong.mp3"
                ]
            },
            "pause": {
                "category": "Music",
                "usage": "!pause",
                "description": "Pause the currently playing song",
                "examples": ["!pause"]
            },
            "resume": {
                "category": "Music",
                "usage": "!resume",
                "description": "Resume the paused song",
                "examples": ["!resume"]
            },
            "skip": {
                "category": "Music",
                "usage": "!skip",
                "aliases": ["s"],
                "description": "Skip the current song",
                "examples": ["!skip"]
            },
            "stop": {
                "category": "Music",
                "usage": "!stop",
                "description": "Stop playback and clear the queue",
                "examples": ["!stop"]
            },
            "volume": {
                "category": "Music",
                "usage": "!volume <0-100>",
                "aliases": ["vol", "v"],
                "description": "Set the playback volume",
                "examples": ["!volume 50", "!vol 75"]
            },
            "nowplaying": {
                "category": "Music",
                "usage": "!nowplaying",
                "aliases": ["np", "current"],
                "description": "Show the currently playing song",
                "examples": ["!nowplaying", "!np"]
            },
            "loop": {
                "category": "Music",
                "usage": "!loop",
                "description": "Toggle loop mode for current song",
                "examples": ["!loop"]
            },
            "join": {
                "category": "Music",
                "usage": "!join",
                "description": "Make the bot join your voice channel",
                "examples": ["!join"]
            },
            "leave": {
                "category": "Music",
                "usage": "!leave",
                "aliases": ["disconnect", "dc"],
                "description": "Make the bot leave the voice channel",
                "examples": ["!leave", "!dc"]
            },
            
            # Queue commands
            "queue": {
                "category": "Queue",
                "usage": "!queue [page]",
                "aliases": ["q"],
                "description": "Show the current music queue",
                "examples": ["!queue", "!queue 2", "!q"]
            },
            "clear": {
                "category": "Queue",
                "usage": "!clear",
                "description": "Clear all songs from the queue",
                "examples": ["!clear"]
            },
            "shuffle": {
                "category": "Queue",
                "usage": "!shuffle",
                "description": "Shuffle the queue",
                "examples": ["!shuffle"]
            },
            "remove": {
                "category": "Queue",
                "usage": "!remove <position>",
                "description": "Remove a song from the queue",
                "examples": ["!remove 3"]
            },
            "move": {
                "category": "Queue",
                "usage": "!move <from> <to>",
                "description": "Move a song in the queue",
                "examples": ["!move 5 2"]
            },
            
            # Playlist commands
            "playlist": {
                "category": "Playlist",
                "usage": "!playlist <action> [name]",
                "aliases": ["pl"],
                "description": "Manage playlists (create, load, save, list, delete)",
                "examples": [
                    "!playlist create MyPlaylist",
                    "!playlist load MyPlaylist",
                    "!playlist save MyPlaylist",
                    "!playlist list",
                    "!playlist delete MyPlaylist"
                ]
            },
            
            # AI Music commands
            "aiplay": {
                "category": "AI Music",
                "usage": "!aiplay <description>",
                "description": "Generate and play AI music based on description",
                "examples": [
                    "!aiplay calm piano music",
                    "!aiplay upbeat electronic dance"
                ]
            },
            "mood": {
                "category": "AI Music",
                "usage": "!mood <mood>",
                "description": "Create a playlist based on mood",
                "examples": ["!mood happy", "!mood relaxing"]
            },
            "similar": {
                "category": "AI Music",
                "usage": "!similar",
                "description": "Find similar songs to current track",
                "examples": ["!similar"]
            },
            "autodj": {
                "category": "AI Music",
                "usage": "!autodj",
                "description": "Enable AI auto-DJ mode",
                "examples": ["!autodj"]
            },
            
            # Utility commands
            "ping": {
                "category": "Utility",
                "usage": "!ping",
                "description": "Check bot latency",
                "examples": ["!ping"]
            },
            "info": {
                "category": "Utility",
                "usage": "!info",
                "description": "Show bot information and features",
                "examples": ["!info"]
            },
            "health": {
                "category": "Utility",
                "usage": "!health",
                "description": "Check service health status",
                "examples": ["!health"]
            },
            
            # Help commands
            "help": {
                "category": "Help",
                "usage": "!help [command]",
                "aliases": ["h", "?"],
                "description": "Show this help message or get help for a specific command",
                "examples": ["!help", "!help play", "!h queue"]
            }
        }
    
    @commands.command(name='help', aliases=['h', '?'])
    async def help_command(self, ctx: commands.Context, *, command_name: Optional[str] = None):
        """
        Show help information
        
        Usage:
            !help - Show all commands
            !help <command> - Show detailed help for a command
        """
        if command_name:
            # Show detailed help for specific command
            await self._show_command_help(ctx, command_name.lower())
        else:
            # Show general help with all commands
            await self._show_general_help(ctx)
    
    async def _show_general_help(self, ctx: commands.Context):
        """Show general help with all commands organized by category"""
        embed = discord.Embed(
            title="🎵 Discord Music Bot - Help",
            description=(
                f"Use `{ctx.prefix}help <command>` for detailed information about a command.\n"
                f"You can also mention me: `@{self.bot.user.name} <command>`\n"
                f"Natural language: `!/ <request>` (when LLM is enabled)"
            ),
            color=discord.Color.blue()
        )
        
        # Add commands by category
        for category_name, category_desc in self.categories.items():
            commands_in_category = []
            
            for cmd_name, cmd_info in self.command_details.items():
                if cmd_info.get("category") == category_name:
                    # Add command with aliases
                    aliases = cmd_info.get("aliases", [])
                    if aliases:
                        cmd_display = f"`{cmd_name}` ({', '.join(aliases)})"
                    else:
                        cmd_display = f"`{cmd_name}`"
                    commands_in_category.append(cmd_display)
            
            if commands_in_category:
                embed.add_field(
                    name=category_desc,
                    value=", ".join(commands_in_category),
                    inline=False
                )
        
        # Add footer with additional info
        embed.set_footer(
            text=f"Prefix: {ctx.prefix} | Total Commands: {len(self.command_details)}"
        )
        
        # Add bot features
        features = []
        
        # Check for AI features
        synthesis_service = self.bot.service_manager.get_service('synthesis_service')
        advanced_ai_service = self.bot.service_manager.get_service('advanced_ai_service')
        dashboard_bridge = self.bot.service_manager.get_service('dashboard_bridge')
        
        if synthesis_service and await synthesis_service.is_available():
            features.append("✅ AI Music Generation")
        if advanced_ai_service:
            features.append("✅ Advanced AI Features")
        if dashboard_bridge:
            features.append("✅ Web Dashboard")
        
        if features:
            embed.add_field(
                name="🌟 Special Features",
                value="\n".join(features),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    async def _show_command_help(self, ctx: commands.Context, command_name: str):
        """Show detailed help for a specific command"""
        # Find command (check aliases too)
        cmd_info = None
        actual_name = command_name
        
        # First check if it's a direct command name
        if command_name in self.command_details:
            cmd_info = self.command_details[command_name]
        else:
            # Check aliases
            for name, info in self.command_details.items():
                if command_name in info.get("aliases", []):
                    cmd_info = info
                    actual_name = name
                    break
        
        if not cmd_info:
            await ctx.send(f"❌ Command `{command_name}` not found. Use `{ctx.prefix}help` to see all commands.")
            return
        
        # Create detailed embed
        embed = discord.Embed(
            title=f"Help: {actual_name}",
            description=cmd_info.get("description", "No description available"),
            color=discord.Color.green()
        )
        
        # Add usage
        embed.add_field(
            name="Usage",
            value=f"`{cmd_info.get('usage', f'{ctx.prefix}{actual_name}')}`",
            inline=False
        )
        
        # Add aliases if any
        aliases = cmd_info.get("aliases", [])
        if aliases:
            embed.add_field(
                name="Aliases",
                value=", ".join(f"`{alias}`" for alias in aliases),
                inline=False
            )
        
        # Add examples
        examples = cmd_info.get("examples", [])
        if examples:
            embed.add_field(
                name="Examples",
                value="\n".join(f"• `{ex}`" for ex in examples),
                inline=False
            )
        
        # Add category
        category = cmd_info.get("category", "Unknown")
        embed.set_footer(text=f"Category: {category}")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='commands')
    async def list_commands(self, ctx: commands.Context):
        """List all available commands"""
        embed = discord.Embed(
            title="📋 All Commands",
            description=f"Use `{ctx.prefix}help <command>` for details",
            color=discord.Color.blue()
        )
        
        # List all commands alphabetically
        all_commands = sorted(self.command_details.keys())
        
        # Split into chunks for better display
        chunk_size = 15
        for i in range(0, len(all_commands), chunk_size):
            chunk = all_commands[i:i+chunk_size]
            embed.add_field(
                name=f"Commands {i+1}-{min(i+chunk_size, len(all_commands))}",
                value=", ".join(f"`{cmd}`" for cmd in chunk),
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='categories')
    async def list_categories(self, ctx: commands.Context):
        """List all command categories"""
        embed = discord.Embed(
            title="📚 Command Categories",
            description="Commands are organized into these categories",
            color=discord.Color.blue()
        )
        
        for category_name, category_desc in self.categories.items():
            # Count commands in category
            count = sum(1 for cmd in self.command_details.values() 
                       if cmd.get("category") == category_name)
            
            embed.add_field(
                name=category_desc,
                value=f"{count} commands - Use `{ctx.prefix}help` to see them",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command(name='usage')
    async def show_usage(self, ctx: commands.Context):
        """Show bot usage tips and tricks"""
        embed = discord.Embed(
            title="💡 Usage Tips & Tricks",
            description="Get the most out of Discord Music Bot",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="🎵 Playing Music",
            value=(
                "• Search by name: `!play never gonna give you up`\n"
                "• Use YouTube URL: `!play https://youtube.com/...`\n"
                "• Play local files: `!play mysong.mp3`\n"
                "• Queue multiple songs: Just use `!play` multiple times"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📋 Queue Management",
            value=(
                "• View queue: `!queue` or `!q`\n"
                "• Skip songs: `!skip` or `!s`\n"
                "• Shuffle: `!shuffle`\n"
                "• Loop current song: `!loop`\n"
                "• Clear queue: `!clear`"
            ),
            inline=False
        )
        
        embed.add_field(
            name="📝 Playlists",
            value=(
                "• Create: `!playlist create MyPlaylist`\n"
                "• Save current queue: `!playlist save MyPlaylist`\n"
                "• Load playlist: `!playlist load MyPlaylist`\n"
                "• List all: `!playlist list`"
            ),
            inline=False
        )
        
        # Check for AI features
        synthesis_service = self.bot.service_manager.get_service('synthesis_service')
        advanced_ai_service = self.bot.service_manager.get_service('advanced_ai_service')
        
        if synthesis_service and await synthesis_service.is_available():
            embed.add_field(
                name="🤖 AI Music Generation",
                value=(
                    "• Generate music: `!aiplay calm piano music`\n"
                    "• Describe what you want and the AI creates it!\n"
                    "• Works with any musical description"
                ),
                inline=False
            )
        
        if advanced_ai_service:
            embed.add_field(
                name="🎭 AI Features",
                value=(
                    "• Mood playlists: `!mood happy`\n"
                    "• Find similar: `!similar`\n"
                    "• Auto-DJ: `!autodj`\n"
                    "• Natural language: `!/ play something relaxing`"
                ),
                inline=False
            )
        
        embed.add_field(
            name="🔧 Pro Tips",
            value=(
                "• Use `@bot` instead of prefix: `@MusicBot play ...`\n"
                "• Bot auto-disconnects when alone in voice\n"
                "• Volume persists for local files\n"
                "• Queue size limited to prevent spam"
            ),
            inline=False
        )
        
        embed.set_footer(text=f"Need more help? Use {ctx.prefix}help <command>")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='about')
    async def about_bot(self, ctx: commands.Context):
        """Show information about the bot"""
        embed = discord.Embed(
            title="🎵 About Discord Music Bot",
            description="A feature-rich music bot with AI capabilities",
            color=discord.Color.purple()
        )
        
        embed.add_field(
            name="Version",
            value="1.0.0",
            inline=True
        )
        
        embed.add_field(
            name="Servers",
            value=str(len(self.bot.guilds)),
            inline=True
        )
        
        embed.add_field(
            name="Users",
            value=str(len(self.bot.users)),
            inline=True
        )
        
        # Features
        features = [
            "✅ YouTube Streaming",
            "✅ Local File Playback",
            "✅ Playlist Management",
            "✅ Queue System",
            "✅ Natural Language Commands"
        ]
        
        # Check optional features
        synthesis_service = self.bot.service_manager.get_service('synthesis_service')
        advanced_ai_service = self.bot.service_manager.get_service('advanced_ai_service')
        dashboard_bridge = self.bot.service_manager.get_service('dashboard_bridge')
        
        if synthesis_service and await synthesis_service.is_available():
            features.append("✅ AI Music Generation")
        if advanced_ai_service:
            features.append("✅ Advanced AI Features")
        if dashboard_bridge:
            features.append("✅ Web Dashboard")
        
        embed.add_field(
            name="Features",
            value="\n".join(features),
            inline=False
        )
        
        embed.add_field(
            name="Links",
            value=(
                f"[Dashboard](http://localhost:8000) • "
                f"[API Docs](http://localhost:8000/docs) • "
                f"[GitHub](https://github.com/ModerateUser/Python_Discord_MusicBot)"
            ),
            inline=False
        )
        
        embed.set_footer(text="Made with discord.py")
        
        await ctx.send(embed=embed)


async def setup(bot):
    """Load the Help cog"""
    await bot.add_cog(HelpCog(bot))
    logger.info("✅ Help cog loaded")
