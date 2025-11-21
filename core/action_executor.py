"""
Action Executor - Executes complex action chains from natural language commands
Handles temporal triggers, action validation, and execution
"""
import asyncio
import logging
import discord
from typing import List, Optional
from core.container import get_container

logger = logging.getLogger(__name__)


class ActionExecutor:
    """
    Executes action chains from natural language commands
    Supports immediate and delayed actions with temporal triggers
    """
    
    def __init__(self, bot):
        """
        Initialize action executor
        
        Args:
            bot: Discord bot instance
        """
        self.bot = bot
        self.container = get_container()
    
    async def execute_complex_actions(
        self,
        message: discord.Message,
        actions: list,
        status_msg: discord.Message
    ) -> None:
        """
        Execute a chain of complex actions
        
        Args:
            message: Original Discord message
            actions: List of Action objects to execute
            status_msg: Status message to update
        """
        from services.ai_music_service import TriggerType
        
        guild_id = message.guild.id
        advanced_ai_service = self.container.get('advanced_ai_service')
        
        if not advanced_ai_service:
            await status_msg.edit(content="❌ Advanced AI service not available")
            return
        
        queue = advanced_ai_service.get_queue(guild_id)
        
        # Separate immediate and delayed actions
        immediate_actions = [a for a in actions if a.trigger == TriggerType.IMMEDIATE]
        delayed_actions = [a for a in actions if a.trigger != TriggerType.IMMEDIATE]
        
        # Queue delayed actions
        for action in delayed_actions:
            queue.add_action(action)
        
        # Execute immediate actions
        for i, action in enumerate(immediate_actions):
            try:
                await status_msg.edit(
                    content=f"⚙️ Executing: {action.description} ({i+1}/{len(immediate_actions)})"
                )
                await self.execute_single_action(message, action, status_msg)
                await asyncio.sleep(0.5)  # Brief pause between actions
            except Exception as e:
                logger.error(f"Error executing action {action.action_type}: {e}")
                await message.channel.send(
                    f"⚠️ Error with action: {action.description}\n{str(e)}"
                )
        
        # Final status
        if delayed_actions:
            delayed_summary = "\n".join([f"• {a.description}" for a in delayed_actions[:3]])
            if len(delayed_actions) > 3:
                delayed_summary += f"\n• ... and {len(delayed_actions) - 3} more actions"
            await status_msg.edit(
                content=f"✅ Immediate actions complete!\n\n⏰ Scheduled:\n{delayed_summary}"
            )
        else:
            await status_msg.edit(content="✅ All actions completed!")
    
    async def execute_single_action(
        self,
        message: discord.Message,
        action,
        status_msg: discord.Message
    ) -> None:
        """
        Execute a single action from the action chain
        
        Args:
            message: Original Discord message
            action: Action object to execute
            status_msg: Status message for updates
        """
        from services.ai_music_service import ActionType
        
        # Get cogs
        music_cog = self.bot.get_cog('Music')
        queue_cog = self.bot.get_cog('QueueManager')
        playlist_cog = self.bot.get_cog('Playlist')
        
        # Get services
        advanced_ai_service = self.container.get('advanced_ai_service')
        synthesis_service = self.container.get('synthesis_service')
        
        # Validate parameters
        if not self._validate_action_parameters(action):
            await message.channel.send(f"❌ Invalid parameters for action: {action.description}")
            return
        
        # Execute based on action type
        if action.action_type == ActionType.PLAY:
            await self._execute_play(message, action, music_cog)
        
        elif action.action_type == ActionType.SKIP:
            await self._execute_skip(message, music_cog)
        
        elif action.action_type == ActionType.PAUSE:
            await self._execute_pause(message, music_cog)
        
        elif action.action_type == ActionType.RESUME:
            await self._execute_resume(message, music_cog)
        
        elif action.action_type == ActionType.STOP:
            await self._execute_stop(message, music_cog)
        
        elif action.action_type == ActionType.VOLUME:
            await self._execute_volume(message, action, music_cog)
        
        elif action.action_type == ActionType.LOOP:
            await self._execute_loop(message, music_cog)
        
        elif action.action_type == ActionType.SYNTHESIZE_MUSIC:
            await self._execute_synthesize(message, action, music_cog, synthesis_service, advanced_ai_service)
        
        elif action.action_type == ActionType.GENERATE_PLAYLIST:
            await self._execute_generate_playlist(message, action, music_cog, advanced_ai_service)
        
        elif action.action_type == ActionType.ANALYZE_SONG:
            await self._execute_analyze_song(message, action, advanced_ai_service)
        
        elif action.action_type == ActionType.FIND_SIMILAR:
            await self._execute_find_similar(message, action, music_cog, advanced_ai_service)
        
        elif action.action_type == ActionType.AUTO_DJ:
            await self._execute_auto_dj(message, action, music_cog, advanced_ai_service)
        
        elif action.action_type == ActionType.FETCH_LYRICS:
            await self._execute_fetch_lyrics(message, action, advanced_ai_service)
        
        elif action.action_type == ActionType.MOOD_TRANSITION:
            await self._execute_mood_transition(message, action, music_cog, advanced_ai_service)
        
        elif action.action_type == ActionType.SMART_SHUFFLE:
            await self._execute_smart_shuffle(message)
    
    def _validate_action_parameters(self, action) -> bool:
        """
        Validate action parameters
        
        Args:
            action: Action object to validate
            
        Returns:
            True if parameters are valid
        """
        from services.ai_music_service import ActionType
        
        params = action.parameters
        
        if action.action_type == ActionType.VOLUME:
            level = params.get('level')
            if level is not None:
                if not isinstance(level, (int, float)) or not 0 <= level <= 100:
                    return False
        
        elif action.action_type == ActionType.SYNTHESIZE_MUSIC:
            duration = params.get('duration', 30)
            if not isinstance(duration, (int, float)) or not 10 <= duration <= 300:
                return False
        
        elif action.action_type == ActionType.GENERATE_PLAYLIST:
            count = params.get('count', 10)
            if not isinstance(count, int) or not 1 <= count <= 50:
                return False
        
        elif action.action_type == ActionType.FIND_SIMILAR:
            count = params.get('count', 5)
            if not isinstance(count, int) or not 1 <= count <= 20:
                return False
        
        elif action.action_type == ActionType.MOOD_TRANSITION:
            duration = params.get('duration_songs', 10)
            if not isinstance(duration, int) or not 3 <= duration <= 30:
                return False
        
        return True
    
    # Individual action executors
    
    async def _execute_play(self, message: discord.Message, action, music_cog) -> None:
        """Execute play action"""
        query = action.parameters.get('query', '')
        if query and music_cog:
            await music_cog.play(message, query=query)
    
    async def _execute_skip(self, message: discord.Message, music_cog) -> None:
        """Execute skip action"""
        if music_cog:
            await music_cog.skip(message)
    
    async def _execute_pause(self, message: discord.Message, music_cog) -> None:
        """Execute pause action"""
        if music_cog:
            await music_cog.pause(message)
    
    async def _execute_resume(self, message: discord.Message, music_cog) -> None:
        """Execute resume action"""
        if music_cog:
            await music_cog.resume(message)
    
    async def _execute_stop(self, message: discord.Message, music_cog) -> None:
        """Execute stop action"""
        if music_cog:
            await music_cog.stop(message)
    
    async def _execute_volume(self, message: discord.Message, action, music_cog) -> None:
        """Execute volume action"""
        level = action.parameters.get('level')
        if level is not None and music_cog:
            await music_cog.volume(message, volume=int(level))
    
    async def _execute_loop(self, message: discord.Message, music_cog) -> None:
        """Execute loop action"""
        if music_cog:
            await music_cog.loop(message)
    
    async def _execute_synthesize(
        self,
        message: discord.Message,
        action,
        music_cog,
        synthesis_service,
        advanced_ai_service
    ) -> None:
        """Execute music synthesis action"""
        if not synthesis_service or not await synthesis_service.is_available():
            await message.channel.send(
                "❌ Music synthesis not available. Check config.json to enable it."
            )
            return
        
        prompt = action.parameters.get('prompt', '')
        style = action.parameters.get('style')
        mood = action.parameters.get('mood')
        duration = action.parameters.get('duration', 30)
        use_history = action.parameters.get('use_history', True)
        
        if not prompt:
            await message.channel.send("❌ No prompt provided for music synthesis")
            return
        
        # Show synthesis progress
        synth_msg = await message.channel.send(
            f"🎼 Synthesizing music: **{prompt}**\n⏳ This may take 30-120 seconds..."
        )
        
        try:
            # Synthesize music
            file_path = await advanced_ai_service.synthesize_music(
                prompt=prompt,
                guild_id=message.guild.id,
                style=style,
                mood=mood,
                duration=int(duration),
                use_history=use_history
            )
            
            if file_path:
                await synth_msg.edit(
                    content=f"✅ Music synthesized successfully!\n🎵 Playing: **{prompt}**"
                )
                
                # Play the synthesized music
                if music_cog:
                    await music_cog.play(message, query=file_path)
                else:
                    await message.channel.send("❌ Music cog not available to play synthesized audio")
            else:
                await synth_msg.edit(content="❌ Music synthesis failed. Check logs for details.")
        
        except Exception as e:
            logger.error(f"Error in music synthesis action: {e}", exc_info=True)
            await synth_msg.edit(content=f"❌ Synthesis error: {str(e)}")
    
    async def _execute_generate_playlist(
        self,
        message: discord.Message,
        action,
        music_cog,
        advanced_ai_service
    ) -> None:
        """Execute generate playlist action"""
        mood = action.parameters.get('mood', 'varied')
        genre = action.parameters.get('genre')
        count = action.parameters.get('count', 10)
        
        songs = await advanced_ai_service.generate_mood_playlist(mood, genre, count)
        
        if songs:
            await message.channel.send(
                f"🎵 Generated {len(songs)}-song playlist for mood: **{mood}**"
            )
            # Add songs to queue
            for song in songs:
                if music_cog:
                    await music_cog.play(message, query=song)
        else:
            await message.channel.send("❌ Could not generate playlist")
    
    async def _execute_analyze_song(
        self,
        message: discord.Message,
        action,
        advanced_ai_service
    ) -> None:
        """Execute analyze song action"""
        song_title = action.parameters.get('song', 'Unknown')
        analysis = await advanced_ai_service.analyze_song(song_title)
        
        embed = discord.Embed(
            title=f"🎵 Song Analysis: {song_title}",
            color=discord.Color.blue()
        )
        if analysis.mood:
            embed.add_field(name="Mood", value=analysis.mood, inline=True)
        if analysis.tempo:
            embed.add_field(name="Tempo", value=f"{analysis.tempo} BPM", inline=True)
        if analysis.energy:
            embed.add_field(name="Energy", value=f"{analysis.energy:.1%}", inline=True)
        if analysis.genre:
            embed.add_field(name="Genre", value=analysis.genre, inline=True)
        if analysis.tags:
            embed.add_field(name="Tags", value=", ".join(analysis.tags), inline=False)
        
        await message.channel.send(embed=embed)
    
    async def _execute_find_similar(
        self,
        message: discord.Message,
        action,
        music_cog,
        advanced_ai_service
    ) -> None:
        """Execute find similar songs action"""
        reference = action.parameters.get('reference_song', '')
        count = action.parameters.get('count', 5)
        
        similar_songs = await advanced_ai_service.find_similar_songs(reference, count=count)
        
        if similar_songs:
            await message.channel.send(
                f"🎵 Found {len(similar_songs)} songs similar to **{reference}**:"
            )
            for i, song in enumerate(similar_songs, 1):
                await message.channel.send(f"{i}. {song}")
                if music_cog:
                    await music_cog.play(message, query=song)
        else:
            await message.channel.send("❌ Could not find similar songs")
    
    async def _execute_auto_dj(
        self,
        message: discord.Message,
        action,
        music_cog,
        advanced_ai_service
    ) -> None:
        """Execute Auto-DJ action"""
        mood = action.parameters.get('mood', 'varied')
        await message.channel.send(f"🎧 Auto-DJ mode activated! Mood: **{mood}**")
        
        # Start Auto-DJ loop (simplified - would need proper implementation)
        for _ in range(5):  # Queue 5 songs
            next_song = await advanced_ai_service.get_auto_dj_next_song(
                message.guild.id,
                mood
            )
            if next_song and music_cog:
                await music_cog.play(message, query=next_song)
    
    async def _execute_fetch_lyrics(
        self,
        message: discord.Message,
        action,
        advanced_ai_service
    ) -> None:
        """Execute fetch lyrics action"""
        song = action.parameters.get('song', '')
        artist = action.parameters.get('artist')
        
        lyrics = await advanced_ai_service.fetch_lyrics(song, artist)
        
        if lyrics:
            # Split lyrics if too long
            if len(lyrics) > 2000:
                lyrics = lyrics[:1997] + "..."
            
            embed = discord.Embed(
                title=f"📝 Lyrics: {song}",
                description=lyrics,
                color=discord.Color.green()
            )
            await message.channel.send(embed=embed)
        else:
            await message.channel.send("❌ Lyrics not available")
    
    async def _execute_mood_transition(
        self,
        message: discord.Message,
        action,
        music_cog,
        advanced_ai_service
    ) -> None:
        """Execute mood transition action"""
        from_mood = action.parameters.get('from_mood', 'calm')
        to_mood = action.parameters.get('to_mood', 'energetic')
        duration = action.parameters.get('duration_songs', 10)
        
        songs = await advanced_ai_service.create_mood_transition_playlist(
            from_mood,
            to_mood,
            duration
        )
        
        if songs:
            await message.channel.send(
                f"🎵 Created mood transition: **{from_mood}** → **{to_mood}** ({len(songs)} songs)"
            )
            for song in songs:
                if music_cog:
                    await music_cog.play(message, query=song)
        else:
            await message.channel.send("❌ Could not create mood transition")
    
    async def _execute_smart_shuffle(self, message: discord.Message) -> None:
        """Execute smart shuffle action"""
        await message.channel.send("🔀 Smart shuffling queue...")
        # Placeholder for actual implementation
