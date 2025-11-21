"""
NLP Handler - Natural Language Processing for Discord commands
Parses natural language queries and converts them to bot actions
"""
import logging
import json
import discord
from typing import Optional, Dict, Any
from core.container import get_container
from utils.llm_parser import parse_llm_response

logger = logging.getLogger(__name__)


class NLPHandler:
    """
    Handles natural language processing for bot commands
    Supports both simple and complex command parsing
    """
    
    def __init__(self, bot):
        """
        Initialize NLP handler
        
        Args:
            bot: Discord bot instance
        """
        self.bot = bot
        self.container = get_container()
    
    async def handle_natural_language(self, message: discord.Message) -> None:
        """
        Handle natural language commands with !/ prefix
        Supports complex action chaining and advanced AI features
        
        Args:
            message: Discord message with natural language command
        """
        # Extract the natural language query
        query = message.content[2:].strip()  # Remove !/ prefix
        
        if not query:
            await message.reply(
                "❌ Please provide a command after `!/`\n\nExample: `!/play something upbeat`"
            )
            return
        
        # Check LLM availability
        llm_service = self.container.get('llm_service')
        if not llm_service or not await llm_service.is_available():
            await message.reply(
                "❌ Natural language commands require an LLM to be loaded.\n"
                "Use regular commands instead: `!play`, `!queue`, `!skip`, etc."
            )
            return
        
        thinking_msg = None
        try:
            # Show thinking indicator
            thinking_msg = await message.reply("🤔 Analyzing your request...")
            
            # Check if this is a complex command
            is_complex = self._is_complex_command(query)
            
            if is_complex:
                await self._handle_complex_command(message, query, thinking_msg)
            else:
                await self._handle_simple_command(message, query, thinking_msg)
        
        except Exception as e:
            logger.error(f"Error handling natural language command: {e}", exc_info=True)
            if thinking_msg:
                try:
                    await thinking_msg.edit(content=f"❌ Error processing your request: {str(e)}")
                except:
                    pass
    
    def _is_complex_command(self, query: str) -> bool:
        """
        Determine if a command is complex (requires action chaining)
        
        Args:
            query: Natural language query
            
        Returns:
            True if command is complex
        """
        complex_keywords = [
            'then', 'after', 'and then', 'followed by', 'next',
            'create', 'generate', 'auto-dj', 'auto dj', 'similar',
            'like', 'mood', 'transition', 'shuffle', 'synthesize',
            'compose', 'make music', 'original'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in complex_keywords)
    
    async def _handle_complex_command(
        self,
        message: discord.Message,
        query: str,
        thinking_msg: discord.Message
    ) -> None:
        """
        Handle complex commands with action chaining
        
        Args:
            message: Original Discord message
            query: Natural language query
            thinking_msg: Status message to update
        """
        advanced_ai_service = self.container.get('advanced_ai_service')
        
        if not advanced_ai_service:
            await thinking_msg.edit(
                content="❌ Advanced AI features not available. Try simpler commands."
            )
            return
        
        # Parse complex intent with action chaining
        await thinking_msg.edit(content="🧠 Parsing complex command...")
        actions = await advanced_ai_service.parse_complex_intent(query, message.guild.id)
        
        if not actions:
            await thinking_msg.edit(
                content="❌ Could not understand your request. Try using simpler language."
            )
            return
        
        # Show what we understood
        action_summary = "\n".join([f"• {action.description}" for action in actions[:3]])
        if len(actions) > 3:
            action_summary += f"\n• ... and {len(actions) - 3} more actions"
        
        await thinking_msg.edit(
            content=f"✅ Understood! Planning:\n{action_summary}\n\n⚙️ Executing..."
        )
        
        # Execute complex action chain
        from core.action_executor import ActionExecutor
        executor = ActionExecutor(self.bot)
        await executor.execute_complex_actions(message, actions, thinking_msg)
    
    async def _handle_simple_command(
        self,
        message: discord.Message,
        query: str,
        thinking_msg: discord.Message
    ) -> None:
        """
        Handle simple commands (single action)
        
        Args:
            message: Original Discord message
            query: Natural language query
            thinking_msg: Status message to update
        """
        # Parse simple intent
        intent = await self.parse_simple_intent(query)
        
        if not intent:
            await thinking_msg.edit(
                content="❌ Could not understand your request. Try using regular commands."
            )
            return
        
        # Update thinking message with what we understood
        await thinking_msg.edit(
            content=f"🎵 {intent.get('thinking_message', 'Processing...')}"
        )
        
        # Execute the interpreted command
        await self.execute_simple_command(message, intent, thinking_msg)
    
    async def parse_simple_intent(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Parse natural language query to determine user intent (simple commands)
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary with intent information or None if parsing fails
        """
        llm_service = self.container.get('llm_service')
        if not llm_service:
            return None
        
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
            response = await llm_service._call_llm(prompt)
            intent = parse_llm_response(response)
            return intent
        except Exception as e:
            logger.error(f"Error parsing natural language intent: {e}")
            return None
    
    async def execute_simple_command(
        self,
        message: discord.Message,
        intent: Dict[str, Any],
        thinking_msg: discord.Message
    ) -> None:
        """
        Execute the interpreted command based on parsed intent (simple commands)
        
        Args:
            message: Original Discord message
            intent: Parsed intent dictionary
            thinking_msg: Status message to update
        """
        command = intent.get('command', '').lower()
        parameters = intent.get('parameters', {})
        
        # Get cogs
        music_cog = self.bot.get_cog('Music')
        queue_cog = self.bot.get_cog('QueueManager')
        playlist_cog = self.bot.get_cog('Playlist')
        ai_cog = self.bot.get_cog('AI Music')
        
        # Get services
        synthesis_service = self.container.get('synthesis_service')
        advanced_ai_service = self.container.get('advanced_ai_service')
        
        try:
            if command == 'play':
                await self._execute_play(message, parameters, music_cog, thinking_msg)
            
            elif command == 'synthesize':
                await self._execute_synthesize(
                    message, parameters, music_cog, synthesis_service,
                    advanced_ai_service, thinking_msg
                )
            
            elif command == 'skip':
                await self._execute_skip(message, music_cog, thinking_msg)
            
            elif command == 'pause':
                await self._execute_pause(message, music_cog, thinking_msg)
            
            elif command == 'resume':
                await self._execute_resume(message, music_cog, thinking_msg)
            
            elif command == 'stop':
                await self._execute_stop(message, music_cog, thinking_msg)
            
            elif command == 'queue':
                await self._execute_queue(message, queue_cog, thinking_msg)
            
            elif command == 'loop':
                await self._execute_loop(message, music_cog, thinking_msg)
            
            elif command == 'volume':
                await self._execute_volume(message, parameters, music_cog, thinking_msg)
            
            elif command == 'suggest':
                await self._execute_suggest(message, parameters, ai_cog, thinking_msg)
            
            elif command == 'search':
                await self._execute_search(message, parameters, music_cog, thinking_msg)
            
            elif command == 'playlist':
                await self._execute_playlist(message, parameters, playlist_cog, thinking_msg)
            
            else:
                await thinking_msg.edit(content=f"❌ Unknown command: {command}")
        
        except Exception as e:
            logger.error(f"Error executing natural language command: {e}", exc_info=True)
            try:
                await thinking_msg.edit(content=f"❌ Error executing command: {str(e)}")
            except:
                await message.reply(f"❌ Error executing command: {str(e)}")
    
    # Individual command executors
    
    async def _execute_play(
        self,
        message: discord.Message,
        parameters: Dict[str, Any],
        music_cog,
        thinking_msg: discord.Message
    ) -> None:
        """Execute play command"""
        query = parameters.get('query', '')
        if not query:
            await thinking_msg.edit(content="❌ Please specify what you want to play")
            return
        
        if music_cog:
            await thinking_msg.delete()
            await music_cog.play(message, query=query)
        else:
            await thinking_msg.edit(content="❌ Music system not available")
    
    async def _execute_synthesize(
        self,
        message: discord.Message,
        parameters: Dict[str, Any],
        music_cog,
        synthesis_service,
        advanced_ai_service,
        thinking_msg: discord.Message
    ) -> None:
        """Execute synthesize command"""
        if not synthesis_service or not await synthesis_service.is_available():
            await thinking_msg.edit(
                content="❌ Music synthesis not available. Check config.json to enable it."
            )
            return
        
        prompt = parameters.get('prompt', '')
        if not prompt:
            await thinking_msg.edit(content="❌ Please specify what kind of music to synthesize")
            return
        
        # Validate duration
        duration = parameters.get('duration', 30)
        if not isinstance(duration, (int, float)) or not 10 <= duration <= 300:
            duration = 30  # Default to 30 seconds
        
        await thinking_msg.edit(
            content=f"🎼 Synthesizing: **{prompt}**\n⏳ This may take 30-120 seconds..."
        )
        
        # Synthesize music
        file_path = await advanced_ai_service.synthesize_music(
            prompt=prompt,
            guild_id=message.guild.id,
            style=parameters.get('style'),
            mood=parameters.get('mood'),
            duration=int(duration),
            use_history=True
        )
        
        if file_path:
            await thinking_msg.edit(content=f"✅ Music synthesized!\n🎵 Playing: **{prompt}**")
            if music_cog:
                await music_cog.play(message, query=file_path)
        else:
            await thinking_msg.edit(content="❌ Music synthesis failed")
    
    async def _execute_skip(
        self,
        message: discord.Message,
        music_cog,
        thinking_msg: discord.Message
    ) -> None:
        """Execute skip command"""
        if music_cog:
            await thinking_msg.delete()
            await music_cog.skip(message)
        else:
            await thinking_msg.edit(content="❌ Music system not available")
    
    async def _execute_pause(
        self,
        message: discord.Message,
        music_cog,
        thinking_msg: discord.Message
    ) -> None:
        """Execute pause command"""
        if music_cog:
            await thinking_msg.delete()
            await music_cog.pause(message)
        else:
            await thinking_msg.edit(content="❌ Music system not available")
    
    async def _execute_resume(
        self,
        message: discord.Message,
        music_cog,
        thinking_msg: discord.Message
    ) -> None:
        """Execute resume command"""
        if music_cog:
            await thinking_msg.delete()
            await music_cog.resume(message)
        else:
            await thinking_msg.edit(content="❌ Music system not available")
    
    async def _execute_stop(
        self,
        message: discord.Message,
        music_cog,
        thinking_msg: discord.Message
    ) -> None:
        """Execute stop command"""
        if music_cog:
            await thinking_msg.delete()
            await music_cog.stop(message)
        else:
            await thinking_msg.edit(content="❌ Music system not available")
    
    async def _execute_queue(
        self,
        message: discord.Message,
        queue_cog,
        thinking_msg: discord.Message
    ) -> None:
        """Execute queue command"""
        if queue_cog:
            await thinking_msg.delete()
            await queue_cog.show_queue(message)
        else:
            await thinking_msg.edit(content="❌ Queue system not available")
    
    async def _execute_loop(
        self,
        message: discord.Message,
        music_cog,
        thinking_msg: discord.Message
    ) -> None:
        """Execute loop command"""
        if music_cog:
            await thinking_msg.delete()
            await music_cog.loop(message)
        else:
            await thinking_msg.edit(content="❌ Music system not available")
    
    async def _execute_volume(
        self,
        message: discord.Message,
        parameters: Dict[str, Any],
        music_cog,
        thinking_msg: discord.Message
    ) -> None:
        """Execute volume command"""
        level = parameters.get('level')
        
        # Validate volume level
        if level is not None:
            if not isinstance(level, (int, float)) or not 0 <= level <= 100:
                await thinking_msg.edit(content="❌ Volume must be between 0 and 100")
                return
            
            # Check voice connectivity
            if not message.guild.voice_client:
                await thinking_msg.edit(content="❌ Not connected to voice channel")
                return
            
            if music_cog:
                await thinking_msg.delete()
                await music_cog.volume(message, volume=int(level))
            else:
                await thinking_msg.edit(content="❌ Music system not available")
        else:
            await thinking_msg.edit(content="❌ Please specify a volume level (0-100)")
    
    async def _execute_suggest(
        self,
        message: discord.Message,
        parameters: Dict[str, Any],
        ai_cog,
        thinking_msg: discord.Message
    ) -> None:
        """Execute suggest command"""
        criteria = parameters.get('criteria')
        if ai_cog:
            await thinking_msg.delete()
            await ai_cog.suggest(message, criteria=criteria)
        else:
            await thinking_msg.edit(content="❌ AI system not available")
    
    async def _execute_search(
        self,
        message: discord.Message,
        parameters: Dict[str, Any],
        music_cog,
        thinking_msg: discord.Message
    ) -> None:
        """Execute search command"""
        query = parameters.get('query', '')
        if query and music_cog:
            await thinking_msg.delete()
            await music_cog.search(message, query=query)
        else:
            await thinking_msg.edit(content="❌ Please specify what to search for")
    
    async def _execute_playlist(
        self,
        message: discord.Message,
        parameters: Dict[str, Any],
        playlist_cog,
        thinking_msg: discord.Message
    ) -> None:
        """Execute playlist command"""
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
