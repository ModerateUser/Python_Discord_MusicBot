"""
LLM Service - AI-powered music recommendations and natural language processing
Supports multiple providers: Ollama (local), OpenAI, Claude, Gemini
"""
import asyncio
import logging
import json
from typing import Optional, Dict, List, Any
from enum import Enum
import aiohttp

logger = logging.getLogger('discord_bot')


class LLMProvider(Enum):
    """Supported LLM providers"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    CLAUDE = "claude"
    GEMINI = "gemini"
    DISABLED = "disabled"


class LLMService:
    """
    AI service for natural language music interactions
    
    Features:
    - Natural language music search
    - Mood-based recommendations
    - Playlist generation
    - Smart query parsing
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize LLM service
        
        Args:
            config: LLM configuration dictionary
        """
        self.enabled = config.get('enabled', False)
        self.provider = LLMProvider(config.get('provider', 'disabled'))
        self.model = config.get('model', 'llama3')
        self.api_key = config.get('api_key')
        self.base_url = config.get('base_url', 'http://localhost:11434')
        self.timeout = config.get('timeout', 30)
        self.max_tokens = config.get('max_tokens', 500)
        
        if self.enabled and self.provider != LLMProvider.DISABLED:
            logger.info(f"LLM Service initialized: {self.provider.value} ({self.model})")
        else:
            logger.info("LLM Service disabled")
    
    async def is_available(self) -> bool:
        """
        Check if LLM service is available
        
        Returns:
            True if service is ready to use
        """
        if not self.enabled or self.provider == LLMProvider.DISABLED:
            return False
        
        try:
            if self.provider == LLMProvider.OLLAMA:
                return await self._check_ollama_health()
            elif self.provider == LLMProvider.OPENAI:
                return self.api_key is not None
            elif self.provider == LLMProvider.CLAUDE:
                return self.api_key is not None
            elif self.provider == LLMProvider.GEMINI:
                return self.api_key is not None
            return False
        except Exception as e:
            logger.error(f"Error checking LLM availability: {e}")
            return False
    
    async def _check_ollama_health(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    return response.status == 200
        except Exception:
            return False
    
    async def parse_music_query(self, user_query: str) -> Dict[str, Any]:
        """
        Parse natural language music query into structured search
        
        Args:
            user_query: Natural language query from user
            
        Returns:
            Dictionary with parsed query information
            
        Example:
            Input: "play something upbeat and energetic"
            Output: {
                'search_query': 'upbeat energetic music',
                'mood': 'energetic',
                'genre': None,
                'confidence': 0.85
            }
        """
        if not await self.is_available():
            # Fallback: return original query
            return {
                'search_query': user_query,
                'mood': None,
                'genre': None,
                'confidence': 0.5,
                'fallback': True
            }
        
        prompt = f"""Parse this music request into a structured format.
User request: "{user_query}"

Extract:
1. search_query: Best YouTube search terms
2. mood: The emotional tone (happy, sad, energetic, calm, etc.) or null
3. genre: Music genre if mentioned or null
4. confidence: Your confidence (0.0-1.0)

Respond ONLY with valid JSON, no other text:
{{"search_query": "...", "mood": "...", "genre": "...", "confidence": 0.0}}"""
        
        try:
            response = await self._call_llm(prompt)
            parsed = json.loads(response)
            parsed['fallback'] = False
            return parsed
        except Exception as e:
            logger.error(f"Error parsing music query: {e}")
            return {
                'search_query': user_query,
                'mood': None,
                'genre': None,
                'confidence': 0.5,
                'fallback': True
            }
    
    async def generate_playlist_suggestions(
        self, 
        mood: Optional[str] = None,
        genre: Optional[str] = None,
        count: int = 5
    ) -> List[str]:
        """
        Generate playlist suggestions based on mood/genre
        
        Args:
            mood: Desired mood (energetic, calm, happy, etc.)
            genre: Music genre
            count: Number of suggestions
            
        Returns:
            List of song suggestions
        """
        if not await self.is_available():
            return []
        
        mood_str = f"mood: {mood}" if mood else ""
        genre_str = f"genre: {genre}" if genre else ""
        criteria = f"{mood_str} {genre_str}".strip() or "popular music"
        
        prompt = f"""Suggest {count} popular songs for {criteria}.

Requirements:
- Real, well-known songs that exist on YouTube
- Include artist name
- Diverse selection
- Format: "Artist - Song Title"

Respond ONLY with valid JSON array, no other text:
["Artist1 - Song1", "Artist2 - Song2", ...]"""
        
        try:
            response = await self._call_llm(prompt)
            suggestions = json.loads(response)
            return suggestions[:count]
        except Exception as e:
            logger.error(f"Error generating playlist suggestions: {e}")
            return []
    
    async def enhance_search_query(self, query: str) -> str:
        """
        Enhance a search query for better YouTube results
        
        Args:
            query: Original search query
            
        Returns:
            Enhanced search query
        """
        if not await self.is_available():
            return query
        
        prompt = f"""Improve this YouTube music search query for better results.
Original: "{query}"

Make it more specific and likely to find the official/popular version.
Respond with ONLY the improved query, no explanation."""
        
        try:
            enhanced = await self._call_llm(prompt)
            return enhanced.strip().strip('"')
        except Exception as e:
            logger.error(f"Error enhancing search query: {e}")
            return query
    
    async def get_song_info(self, song_title: str) -> Optional[Dict[str, str]]:
        """
        Get additional information about a song
        
        Args:
            song_title: Song title to look up
            
        Returns:
            Dictionary with song information or None
        """
        if not await self.is_available():
            return None
        
        prompt = f"""Provide brief information about this song: "{song_title}"

Include:
- artist: Artist name
- genre: Primary genre
- year: Release year (approximate)
- description: One sentence description

Respond ONLY with valid JSON, no other text:
{{"artist": "...", "genre": "...", "year": "...", "description": "..."}}"""
        
        try:
            response = await self._call_llm(prompt)
            return json.loads(response)
        except Exception as e:
            logger.error(f"Error getting song info: {e}")
            return None
    
    async def _call_llm(self, prompt: str) -> str:
        """
        Call the configured LLM provider
        
        Args:
            prompt: Prompt to send to LLM
            
        Returns:
            LLM response text
        """
        if self.provider == LLMProvider.OLLAMA:
            return await self._call_ollama(prompt)
        elif self.provider == LLMProvider.OPENAI:
            return await self._call_openai(prompt)
        elif self.provider == LLMProvider.CLAUDE:
            return await self._call_claude(prompt)
        elif self.provider == LLMProvider.GEMINI:
            return await self._call_gemini(prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def _call_ollama(self, prompt: str) -> str:
        """Call Ollama API"""
        async with aiohttp.ClientSession() as session:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": self.max_tokens
                }
            }
            
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get('response', '').strip()
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a music expert assistant. Respond concisely."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": self.max_tokens,
                "temperature": 0.7
            }
            
            async with session.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data['choices'][0]['message']['content'].strip()
    
    async def _call_claude(self, prompt: str) -> str:
        """Call Anthropic Claude API"""
        async with aiohttp.ClientSession() as session:
            headers = {
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": self.max_tokens,
                "temperature": 0.7
            }
            
            async with session.post(
                "https://api.anthropic.com/v1/messages",
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data['content'][0]['text'].strip()
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Google Gemini API"""
        async with aiohttp.ClientSession() as session:
            url = f"https://generativelanguage.googleapis.com/v1/models/{self.model}:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": self.max_tokens
                }
            }
            
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data['candidates'][0]['content']['parts'][0]['text'].strip()


# Default configuration
DEFAULT_LLM_CONFIG = {
    'enabled': False,
    'provider': 'ollama',
    'model': 'llama3',
    'api_key': None,
    'base_url': 'http://localhost:11434',
    'timeout': 30,
    'max_tokens': 500
}


def create_llm_service(config: Optional[Dict[str, Any]] = None) -> LLMService:
    """
    Factory function to create LLM service
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        Configured LLMService instance
    """
    if config is None:
        config = DEFAULT_LLM_CONFIG
    return LLMService(config)
