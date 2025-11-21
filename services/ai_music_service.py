"""
Advanced AI Music Service
Handles complex action chaining and intelligent music features
Integrated with AI music synthesis
"""
import asyncio
import logging
import json
from typing import Optional, Dict, List, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger('discord_bot')


class ActionType(Enum):
    """Types of actions that can be performed"""
    PLAY = "play"
    SKIP = "skip"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    VOLUME = "volume"
    LOOP = "loop"
    CREATE_PLAYLIST = "create_playlist"
    ADD_TO_PLAYLIST = "add_to_playlist"
    GENERATE_PLAYLIST = "generate_playlist"
    ANALYZE_SONG = "analyze_song"
    FIND_SIMILAR = "find_similar"
    AUTO_DJ = "auto_dj"
    FETCH_LYRICS = "fetch_lyrics"
    MOOD_TRANSITION = "mood_transition"
    SMART_SHUFFLE = "smart_shuffle"
    SYNTHESIZE_MUSIC = "synthesize_music"  # NEW: AI music synthesis


class TriggerType(Enum):
    """Types of triggers for conditional actions"""
    IMMEDIATE = "immediate"
    AFTER_SONGS = "after_songs"
    AFTER_TIME = "after_time"
    ON_MOOD_CHANGE = "on_mood_change"
    ON_SONG_END = "on_song_end"


@dataclass
class Action:
    """Represents a single action to be performed"""
    action_type: ActionType
    parameters: Dict[str, Any] = field(default_factory=dict)
    trigger: TriggerType = TriggerType.IMMEDIATE
    trigger_value: Any = None
    description: str = ""


@dataclass
class MusicAnalysis:
    """Analysis results for a song"""
    tempo: Optional[int] = None  # BPM
    key: Optional[str] = None  # Musical key
    mood: Optional[str] = None  # happy, sad, energetic, calm, etc.
    energy: Optional[float] = None  # 0.0 to 1.0
    danceability: Optional[float] = None  # 0.0 to 1.0
    valence: Optional[float] = None  # 0.0 to 1.0 (positivity)
    genre: Optional[str] = None
    similar_artists: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


class AIActionQueue:
    """Manages a queue of AI-generated actions"""
    
    def __init__(self):
        self.actions: List[Action] = []
        self.current_song_count = 0
        self.start_time = datetime.now()
        self.listening_history: List[Dict[str, Any]] = []
        self.current_mood = None
        
    def add_action(self, action: Action):
        """Add an action to the queue"""
        self.actions.append(action)
        logger.info(f"Added action to queue: {action.action_type.value} - {action.description}")
    
    def get_ready_actions(self) -> List[Action]:
        """Get all actions that are ready to execute"""
        ready = []
        for action in self.actions[:]:
            if self._is_action_ready(action):
                ready.append(action)
                self.actions.remove(action)
        return ready
    
    def _is_action_ready(self, action: Action) -> bool:
        """Check if an action's trigger condition is met"""
        if action.trigger == TriggerType.IMMEDIATE:
            return True
        elif action.trigger == TriggerType.AFTER_SONGS:
            return self.current_song_count >= action.trigger_value
        elif action.trigger == TriggerType.AFTER_TIME:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            return elapsed >= action.trigger_value
        elif action.trigger == TriggerType.ON_MOOD_CHANGE:
            return self.current_mood != action.trigger_value
        return False
    
    def increment_song_count(self):
        """Increment the song counter"""
        self.current_song_count += 1
    
    def update_mood(self, mood: str):
        """Update the current mood"""
        self.current_mood = mood
    
    def add_to_history(self, song_info: Dict[str, Any]):
        """Add a song to listening history"""
        self.listening_history.append({
            **song_info,
            'timestamp': datetime.now().isoformat()
        })
        # Keep only last 100 songs
        if len(self.listening_history) > 100:
            self.listening_history = self.listening_history[-100:]


class AdvancedAIMusicService:
    """
    Advanced AI Music Service with complex action chaining and intelligent features
    Integrated with AI music synthesis capabilities
    """
    
    def __init__(self, llm_service, synthesis_service=None):
        """
        Initialize the advanced AI music service
        
        Args:
            llm_service: The LLM service instance for AI operations
            synthesis_service: Optional music synthesis service for AI generation
        """
        self.llm = llm_service
        self.synthesis = synthesis_service
        self.action_queues: Dict[int, AIActionQueue] = {}  # guild_id -> queue
        logger.info(f"Advanced AI Music Service initialized (Synthesis: {synthesis_service is not None})")
    
    def get_queue(self, guild_id: int) -> AIActionQueue:
        """Get or create action queue for a guild"""
        if guild_id not in self.action_queues:
            self.action_queues[guild_id] = AIActionQueue()
        return self.action_queues[guild_id]
    
    async def parse_complex_intent(self, query: str, guild_id: int) -> List[Action]:
        """
        Parse complex natural language into a sequence of actions
        
        Args:
            query: Natural language query from user
            guild_id: Discord guild ID
            
        Returns:
            List of Action objects to execute
            
        Examples:
            "play jazz for 10 minutes then switch to rock"
            "create a workout playlist with 15 energetic songs"
            "synthesize upbeat electronic music based on what I've been listening to"
            "generate original chill music for studying"
        """
        if not await self.llm.is_available():
            # Fallback to simple parsing
            return await self._simple_parse(query)
        
        # Check if synthesis is available for prompt enhancement
        synthesis_available = self.synthesis and await self.synthesis.is_available()
        synthesis_note = "\n- synthesize_music: Generate original AI music (params: prompt, style, mood, duration)" if synthesis_available else ""
        
        prompt = f"""Parse this complex music bot command into a sequence of actions.

User request: "{query}"

Analyze the request and break it down into individual actions with their triggers.

Action types available:
- play: Play music (params: query, mood, genre)
- skip: Skip current song
- pause/resume/stop: Playback control
- volume: Set volume (params: level)
- loop: Enable/disable loop
- create_playlist: Create new playlist (params: name, criteria)
- generate_playlist: AI-generate playlist (params: mood, genre, count, criteria)
- analyze_song: Analyze current song
- find_similar: Find similar songs (params: reference_song)
- auto_dj: Enable auto-DJ mode (params: mood, energy_level)
- fetch_lyrics: Get song lyrics
- mood_transition: Gradually transition moods (params: from_mood, to_mood, duration)
- smart_shuffle: Intelligent shuffle based on flow{synthesis_note}

Trigger types:
- immediate: Execute now
- after_songs: After N songs (params: count)
- after_time: After N seconds (params: seconds)
- on_mood_change: When mood changes
- on_song_end: When current song ends

Respond with ONLY valid JSON array:
[
  {{
    "action": "play",
    "parameters": {{"query": "jazz music", "mood": "relaxed"}},
    "trigger": "immediate",
    "trigger_value": null,
    "description": "Play relaxed jazz music"
  }},
  {{
    "action": "volume",
    "parameters": {{"level": 30}},
    "trigger": "immediate",
    "trigger_value": null,
    "description": "Set volume to 30%"
  }},
  {{
    "action": "play",
    "parameters": {{"query": "rock music", "mood": "energetic"}},
    "trigger": "after_time",
    "trigger_value": 600,
    "description": "Switch to energetic rock after 10 minutes"
  }}
]

Examples:
"play jazz then rock after 3 songs" → [play jazz (immediate), play rock (after_songs: 3)]
"create a workout playlist with 10 songs" → [generate_playlist (immediate, count: 10, mood: energetic)]
"synthesize chill music" → [synthesize_music (immediate, prompt: "chill music", mood: "relaxed")]
"generate original upbeat music based on my history" → [synthesize_music (immediate, prompt: "upbeat music", use_history: true)]
"""
        
        try:
            response = await self.llm._call_llm(prompt)
            actions_data = json.loads(response)
            
            actions = []
            for action_data in actions_data:
                action = Action(
                    action_type=ActionType(action_data['action']),
                    parameters=action_data.get('parameters', {}),
                    trigger=TriggerType(action_data.get('trigger', 'immediate')),
                    trigger_value=action_data.get('trigger_value'),
                    description=action_data.get('description', '')
                )
                actions.append(action)
            
            logger.info(f"Parsed {len(actions)} actions from complex intent")
            return actions
            
        except Exception as e:
            logger.error(f"Error parsing complex intent: {e}", exc_info=True)
            return await self._simple_parse(query)
    
    async def _simple_parse(self, query: str) -> List[Action]:
        """Fallback simple parsing when LLM unavailable"""
        # Basic keyword matching
        actions = []
        
        if 'play' in query.lower():
            actions.append(Action(
                action_type=ActionType.PLAY,
                parameters={'query': query},
                description=f"Play: {query}"
            ))
        elif any(word in query.lower() for word in ['synthesize', 'generate', 'create music', 'compose']):
            # Simple synthesis detection
            actions.append(Action(
                action_type=ActionType.SYNTHESIZE_MUSIC,
                parameters={'prompt': query},
                description=f"Synthesize: {query}"
            ))
        
        return actions
    
    async def synthesize_music(
        self,
        prompt: str,
        guild_id: int,
        style: Optional[str] = None,
        mood: Optional[str] = None,
        duration: int = 30,
        use_history: bool = True
    ) -> Optional[str]:
        """
        Synthesize original music using AI
        
        Args:
            prompt: Description of music to generate
            guild_id: Discord guild ID for history context
            style: Optional music style
            mood: Optional mood
            duration: Duration in seconds
            use_history: Whether to use listening history for personalization
            
        Returns:
            Path to generated audio file or None
        """
        if not self.synthesis or not await self.synthesis.is_available():
            logger.warning("Music synthesis not available")
            return None
        
        try:
            from .music_synthesis_service import MusicGenerationRequest, GenerationQuality
            
            # Get listening history if requested
            listening_history = None
            if use_history:
                queue = self.get_queue(guild_id)
                listening_history = queue.listening_history
            
            # Create synthesis request
            request = MusicGenerationRequest(
                prompt=prompt,
                style=style,
                mood=mood,
                duration=duration,
                quality=GenerationQuality.MEDIUM,
                guild_id=guild_id
            )
            
            # Generate music
            logger.info(f"Synthesizing music: {prompt} (style: {style}, mood: {mood})")
            result = await self.synthesis.generate_music(request, listening_history)
            
            if result:
                logger.info(f"Successfully synthesized: {result.title} ({result.generation_time:.2f}s)")
                return result.file_path
            else:
                logger.error("Music synthesis failed")
                return None
        
        except Exception as e:
            logger.error(f"Error synthesizing music: {e}", exc_info=True)
            return None
    
    async def generate_mood_playlist(
        self,
        mood: str,
        genre: Optional[str] = None,
        count: int = 10,
        energy_level: Optional[str] = None
    ) -> List[str]:
        """
        Generate a playlist based on mood and criteria
        
        Args:
            mood: Target mood (happy, sad, energetic, calm, etc.)
            genre: Optional genre filter
            count: Number of songs to generate
            energy_level: Optional energy level (low, medium, high)
            
        Returns:
            List of song queries
        """
        if not await self.llm.is_available():
            return []
        
        prompt = f"""Generate a {count}-song playlist with these criteria:

Mood: {mood}
Genre: {genre or 'any'}
Energy Level: {energy_level or 'medium'}

Requirements:
- Real, popular songs that exist on YouTube
- Include artist name
- Diverse selection within the mood
- Good flow between songs
- Format: "Artist - Song Title"

Respond with ONLY valid JSON array:
["Artist1 - Song1", "Artist2 - Song2", ...]
"""
        
        try:
            response = await self.llm._call_llm(prompt)
            songs = json.loads(response)
            logger.info(f"Generated {len(songs)} songs for mood: {mood}")
            return songs[:count]
        except Exception as e:
            logger.error(f"Error generating mood playlist: {e}")
            return []
    
    async def analyze_song(self, song_title: str, artist: Optional[str] = None) -> MusicAnalysis:
        """
        Analyze a song's musical characteristics
        
        Args:
            song_title: Song title
            artist: Optional artist name
            
        Returns:
            MusicAnalysis object with song characteristics
        """
        if not await self.llm.is_available():
            return MusicAnalysis()
        
        song_query = f"{artist} - {song_title}" if artist else song_title
        
        prompt = f"""Analyze this song's musical characteristics: "{song_query}"

Provide analysis in the following format (use your knowledge of the song):

Respond with ONLY valid JSON:
{{
  "tempo": 120,  // BPM (integer)
  "key": "C Major",  // Musical key
  "mood": "energetic",  // happy, sad, energetic, calm, melancholic, uplifting, etc.
  "energy": 0.8,  // 0.0 to 1.0
  "danceability": 0.7,  // 0.0 to 1.0
  "valence": 0.6,  // 0.0 to 1.0 (positivity)
  "genre": "pop",
  "similar_artists": ["Artist1", "Artist2", "Artist3"],
  "tags": ["upbeat", "catchy", "summer"]
}}
"""
        
        try:
            response = await self.llm._call_llm(prompt)
            data = json.loads(response)
            
            analysis = MusicAnalysis(
                tempo=data.get('tempo'),
                key=data.get('key'),
                mood=data.get('mood'),
                energy=data.get('energy'),
                danceability=data.get('danceability'),
                valence=data.get('valence'),
                genre=data.get('genre'),
                similar_artists=data.get('similar_artists', []),
                tags=data.get('tags', [])
            )
            
            logger.info(f"Analyzed song: {song_query} - Mood: {analysis.mood}, Energy: {analysis.energy}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing song: {e}")
            return MusicAnalysis()
    
    async def find_similar_songs(
        self,
        reference_song: str,
        reference_artist: Optional[str] = None,
        count: int = 5
    ) -> List[str]:
        """
        Find songs similar to a reference song
        
        Args:
            reference_song: Reference song title
            reference_artist: Optional reference artist
            count: Number of similar songs to find
            
        Returns:
            List of similar song queries
        """
        if not await self.llm.is_available():
            return []
        
        song_query = f"{reference_artist} - {reference_song}" if reference_artist else reference_song
        
        prompt = f"""Find {count} songs similar to: "{song_query}"

Consider:
- Similar mood and energy
- Similar genre and style
- Similar tempo and vibe
- Artists with similar sound

Requirements:
- Real, popular songs on YouTube
- Include artist name
- Format: "Artist - Song Title"

Respond with ONLY valid JSON array:
["Artist1 - Song1", "Artist2 - Song2", ...]
"""
        
        try:
            response = await self.llm._call_llm(prompt)
            songs = json.loads(response)
            logger.info(f"Found {len(songs)} similar songs to: {song_query}")
            return songs[:count]
        except Exception as e:
            logger.error(f"Error finding similar songs: {e}")
            return []
    
    async def get_auto_dj_next_song(
        self,
        guild_id: int,
        current_mood: Optional[str] = None,
        energy_trend: str = "maintain"  # increase, decrease, maintain
    ) -> Optional[str]:
        """
        Get the next song for Auto-DJ mode
        
        Args:
            guild_id: Discord guild ID
            current_mood: Current playlist mood
            energy_trend: How to adjust energy (increase, decrease, maintain)
            
        Returns:
            Next song query or None
        """
        if not await self.llm.is_available():
            return None
        
        queue = self.get_queue(guild_id)
        recent_songs = queue.listening_history[-5:] if queue.listening_history else []
        
        recent_list = "\n".join([
            f"- {song.get('title', 'Unknown')}" for song in recent_songs
        ])
        
        prompt = f"""You are an AI DJ. Select the next song to play.

Current mood: {current_mood or 'varied'}
Energy trend: {energy_trend}
Recently played:
{recent_list or 'No recent songs'}

Select a song that:
- Fits the current mood
- Follows the energy trend ({energy_trend})
- Provides good flow from recent songs
- Avoids repetition
- Is popular and available on YouTube

Respond with ONLY the song query in format: "Artist - Song Title"
"""
        
        try:
            response = await self.llm._call_llm(prompt)
            song = response.strip().strip('"')
            logger.info(f"Auto-DJ selected: {song}")
            return song
        except Exception as e:
            logger.error(f"Error in auto-DJ selection: {e}")
            return None
    
    async def fetch_lyrics(self, song_title: str, artist: Optional[str] = None) -> Optional[str]:
        """
        Fetch lyrics for a song (using LLM knowledge)
        
        Args:
            song_title: Song title
            artist: Optional artist name
            
        Returns:
            Lyrics text or None
        """
        if not await self.llm.is_available():
            return None
        
        song_query = f"{artist} - {song_title}" if artist else song_title
        
        prompt = f"""Provide the lyrics for: "{song_query}"

If you know the lyrics, provide them.
If you don't know the exact lyrics, respond with: "Lyrics not available"

Format the lyrics with proper line breaks and structure.
"""
        
        try:
            response = await self.llm._call_llm(prompt)
            if "not available" in response.lower():
                return None
            return response.strip()
        except Exception as e:
            logger.error(f"Error fetching lyrics: {e}")
            return None
    
    async def create_mood_transition_playlist(
        self,
        from_mood: str,
        to_mood: str,
        duration_songs: int = 10
    ) -> List[str]:
        """
        Create a playlist that gradually transitions between moods
        
        Args:
            from_mood: Starting mood
            to_mood: Target mood
            duration_songs: Number of songs for transition
            
        Returns:
            List of song queries for smooth transition
        """
        if not await self.llm.is_available():
            return []
        
        prompt = f"""Create a {duration_songs}-song playlist that gradually transitions from {from_mood} to {to_mood}.

Requirements:
- Start with songs matching "{from_mood}" mood
- Gradually shift toward "{to_mood}" mood
- Smooth transitions between songs
- Real, popular songs on YouTube
- Include artist name
- Format: "Artist - Song Title"

Respond with ONLY valid JSON array:
["Artist1 - Song1", "Artist2 - Song2", ...]
"""
        
        try:
            response = await self.llm._call_llm(prompt)
            songs = json.loads(response)
            logger.info(f"Created mood transition playlist: {from_mood} → {to_mood}")
            return songs[:duration_songs]
        except Exception as e:
            logger.error(f"Error creating mood transition: {e}")
            return []
    
    async def smart_shuffle(
        self,
        songs: List[str],
        optimize_for: str = "flow"  # flow, energy, variety
    ) -> List[str]:
        """
        Intelligently shuffle songs for optimal listening experience
        
        Args:
            songs: List of songs to shuffle
            optimize_for: Optimization strategy (flow, energy, variety)
            
        Returns:
            Reordered list of songs
        """
        if not await self.llm.is_available() or len(songs) <= 2:
            return songs
        
        songs_list = "\n".join([f"{i+1}. {song}" for i, song in enumerate(songs)])
        
        prompt = f"""Reorder these songs for optimal listening experience.

Songs:
{songs_list}

Optimize for: {optimize_for}
- flow: Smooth transitions between songs
- energy: Gradually build or vary energy
- variety: Mix genres and styles

Respond with ONLY valid JSON array of song titles in new order:
["Song1", "Song2", ...]
"""
        
        try:
            response = await self.llm._call_llm(prompt)
            reordered = json.loads(response)
            logger.info(f"Smart shuffled {len(songs)} songs (optimize: {optimize_for})")
            return reordered
        except Exception as e:
            logger.error(f"Error in smart shuffle: {e}")
            return songs
    
    async def get_personalized_recommendations(
        self,
        guild_id: int,
        count: int = 5
    ) -> List[str]:
        """
        Get personalized song recommendations based on listening history
        
        Args:
            guild_id: Discord guild ID
            count: Number of recommendations
            
        Returns:
            List of recommended song queries
        """
        if not await self.llm.is_available():
            return []
        
        queue = self.get_queue(guild_id)
        if not queue.listening_history:
            return []
        
        recent_songs = queue.listening_history[-20:]
        songs_list = "\n".join([
            f"- {song.get('title', 'Unknown')}" for song in recent_songs
        ])
        
        prompt = f"""Based on this listening history, recommend {count} songs the user would enjoy.

Recent listening history:
{songs_list}

Analyze patterns in:
- Genres and styles
- Moods and energy levels
- Artists and similar sounds

Recommend songs that:
- Match discovered preferences
- Introduce similar new artists
- Maintain variety
- Are popular and on YouTube

Respond with ONLY valid JSON array:
["Artist1 - Song1", "Artist2 - Song2", ...]
"""
        
        try:
            response = await self.llm._call_llm(prompt)
            recommendations = json.loads(response)
            logger.info(f"Generated {len(recommendations)} personalized recommendations")
            return recommendations[:count]
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return []


# Global instance (will be initialized with LLM service)
advanced_ai_service: Optional[AdvancedAIMusicService] = None


def create_advanced_ai_service(llm_service, synthesis_service=None) -> AdvancedAIMusicService:
    """
    Factory function to create advanced AI music service
    
    Args:
        llm_service: LLM service instance
        synthesis_service: Optional music synthesis service
        
    Returns:
        AdvancedAIMusicService instance
    """
    global advanced_ai_service
    advanced_ai_service = AdvancedAIMusicService(llm_service, synthesis_service)
    return advanced_ai_service
