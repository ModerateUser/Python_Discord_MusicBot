"""
AI Music Synthesis Service
Generates original music using AI based on prompts, listening history, and current context
Supports multiple backends: Suno API, MusicGen (local), and MIDI fallback
"""
import asyncio
import aiohttp
import logging
import json
import hashlib
import os
import time
from pathlib import Path
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger('discord_bot')


class SynthesisBackend(Enum):
    """Available music synthesis backends"""
    SUNO_API = "suno_api"
    MUSICGEN_LOCAL = "musicgen_local"
    MIDI_FALLBACK = "midi_fallback"
    DISABLED = "disabled"


class GenerationQuality(Enum):
    """Quality levels for music generation"""
    LOW = "low"          # Fast, lower quality
    MEDIUM = "medium"    # Balanced
    HIGH = "high"        # Best quality, slower
    ULTRA = "ultra"      # Maximum quality (if supported)


@dataclass
class MusicGenerationRequest:
    """Request for music generation"""
    prompt: str
    style: Optional[str] = None
    mood: Optional[str] = None
    tempo: Optional[int] = None  # BPM
    duration: int = 30  # seconds
    quality: GenerationQuality = GenerationQuality.MEDIUM
    reference_songs: Optional[List[str]] = None
    user_id: Optional[int] = None
    guild_id: Optional[int] = None


@dataclass
class GeneratedMusic:
    """Result of music generation"""
    file_path: str
    title: str
    prompt: str
    style: str
    mood: str
    duration: int
    backend: SynthesisBackend
    generation_time: float
    metadata: Dict[str, Any]


class MusicSynthesisService:
    """
    Advanced AI Music Synthesis Service
    
    Generates original music using multiple AI backends with intelligent
    prompt engineering based on listening history and user preferences.
    """
    
    def __init__(self, config: dict, llm_service=None):
        """
        Initialize the music synthesis service
        
        Args:
            config: Configuration dictionary with synthesis settings
            llm_service: LLM service for prompt enhancement
        """
        self.config = config
        self.llm_service = llm_service
        
        # Get synthesis configuration
        synthesis_config = config.get('music_synthesis', {})
        self.enabled = synthesis_config.get('enabled', False)
        self.backend = SynthesisBackend(synthesis_config.get('backend', 'disabled'))
        self.cache_dir = Path(synthesis_config.get('cache_dir', 'generated_music'))
        self.max_cache_size_mb = synthesis_config.get('max_cache_size_mb', 1000)
        self.default_duration = synthesis_config.get('default_duration', 30)
        self.default_quality = GenerationQuality(synthesis_config.get('default_quality', 'medium'))
        
        # Backend-specific configuration
        self.suno_api_key = synthesis_config.get('suno_api_key')
        self.suno_api_url = synthesis_config.get('suno_api_url', 'https://api.suno.ai/v1')
        self.musicgen_model = synthesis_config.get('musicgen_model', 'facebook/musicgen-small')
        
        # Create cache directory
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Generation statistics
        self.stats = {
            'total_generations': 0,
            'successful_generations': 0,
            'failed_generations': 0,
            'total_generation_time': 0.0,
            'cache_hits': 0,
            'backend_usage': {backend.value: 0 for backend in SynthesisBackend}
        }
        
        # Initialize backend
        self._initialize_backend()
        
        logger.info(f"Music Synthesis Service initialized - Backend: {self.backend.value}, Enabled: {self.enabled}")
    
    def _initialize_backend(self):
        """Initialize the selected backend"""
        if not self.enabled:
            logger.info("Music synthesis is disabled")
            return
        
        if self.backend == SynthesisBackend.SUNO_API:
            if not self.suno_api_key:
                logger.warning("Suno API key not configured, synthesis will fail")
            else:
                logger.info("Suno API backend initialized")
        
        elif self.backend == SynthesisBackend.MUSICGEN_LOCAL:
            try:
                # Try to import audiocraft (MusicGen)
                import audiocraft
                logger.info(f"MusicGen backend initialized with model: {self.musicgen_model}")
            except ImportError:
                logger.error(
                    "MusicGen backend selected but audiocraft not installed. "
                    "Install with: pip install audiocraft"
                )
                self.enabled = False
        
        elif self.backend == SynthesisBackend.MIDI_FALLBACK:
            logger.info("MIDI fallback backend initialized")
    
    async def is_available(self) -> bool:
        """Check if music synthesis is available"""
        return self.enabled and self.backend != SynthesisBackend.DISABLED
    
    async def generate_music(
        self,
        request: MusicGenerationRequest,
        listening_history: Optional[List[Dict]] = None
    ) -> Optional[GeneratedMusic]:
        """
        Generate music based on request and context
        
        Args:
            request: Music generation request
            listening_history: Recent listening history for personalization
            
        Returns:
            GeneratedMusic object or None on failure
        """
        if not await self.is_available():
            logger.warning("Music synthesis not available")
            return None
        
        start_time = time.time()
        self.stats['total_generations'] += 1
        
        try:
            # Enhance prompt with context
            enhanced_prompt = await self._enhance_prompt(request, listening_history)
            
            # Check cache first
            cache_key = self._generate_cache_key(enhanced_prompt, request)
            cached_result = await self._check_cache(cache_key)
            if cached_result:
                self.stats['cache_hits'] += 1
                logger.info(f"Cache hit for music generation: {cache_key[:16]}...")
                return cached_result
            
            # Generate music using selected backend
            result = None
            if self.backend == SynthesisBackend.SUNO_API:
                result = await self._generate_with_suno(enhanced_prompt, request)
            elif self.backend == SynthesisBackend.MUSICGEN_LOCAL:
                result = await self._generate_with_musicgen(enhanced_prompt, request)
            elif self.backend == SynthesisBackend.MIDI_FALLBACK:
                result = await self._generate_with_midi(enhanced_prompt, request)
            
            if result:
                generation_time = time.time() - start_time
                result.generation_time = generation_time
                
                self.stats['successful_generations'] += 1
                self.stats['total_generation_time'] += generation_time
                self.stats['backend_usage'][self.backend.value] += 1
                
                # Cache the result
                await self._cache_result(cache_key, result)
                
                logger.info(
                    f"Successfully generated music: {result.title} "
                    f"({generation_time:.2f}s, {self.backend.value})"
                )
                
                return result
            else:
                self.stats['failed_generations'] += 1
                logger.error("Music generation failed")
                return None
        
        except Exception as e:
            self.stats['failed_generations'] += 1
            logger.error(f"Error generating music: {e}", exc_info=True)
            return None
    
    async def _enhance_prompt(
        self,
        request: MusicGenerationRequest,
        listening_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Enhance the generation prompt using LLM and context
        
        Args:
            request: Original request
            listening_history: Recent listening history
            
        Returns:
            Enhanced prompt string
        """
        base_prompt = request.prompt
        
        # If no LLM service, return base prompt with basic enhancements
        if not self.llm_service or not await self.llm_service.is_available():
            enhanced = base_prompt
            if request.style:
                enhanced += f", {request.style} style"
            if request.mood:
                enhanced += f", {request.mood} mood"
            if request.tempo:
                enhanced += f", {request.tempo} BPM"
            return enhanced
        
        # Build context for LLM
        context_parts = []
        
        if listening_history:
            # Analyze listening history
            genres = []
            moods = []
            artists = []
            
            for song in listening_history[-10:]:  # Last 10 songs
                if 'genre' in song:
                    genres.append(song['genre'])
                if 'mood' in song:
                    moods.append(song['mood'])
                if 'artist' in song:
                    artists.append(song['artist'])
            
            if genres:
                context_parts.append(f"Recent genres: {', '.join(set(genres))}")
            if moods:
                context_parts.append(f"Recent moods: {', '.join(set(moods))}")
            if artists:
                context_parts.append(f"Recent artists: {', '.join(set(artists)[:5])}")
        
        if request.reference_songs:
            context_parts.append(f"Reference songs: {', '.join(request.reference_songs)}")
        
        context = "\n".join(context_parts) if context_parts else "No specific context"
        
        # Create LLM prompt for enhancement
        llm_prompt = f"""You are an expert music producer. Enhance this music generation prompt to be more specific and effective for AI music generation.

Original prompt: "{base_prompt}"
Style: {request.style or 'not specified'}
Mood: {request.mood or 'not specified'}
Tempo: {request.tempo or 'not specified'} BPM
Duration: {request.duration} seconds

User context:
{context}

Create an enhanced, detailed prompt that:
1. Incorporates the user's listening preferences
2. Specifies musical elements (instruments, structure, energy)
3. Maintains the original intent
4. Is optimized for AI music generation
5. Is concise but descriptive (max 200 characters)

Respond with ONLY the enhanced prompt, no explanation."""
        
        try:
            enhanced = await self.llm_service._call_llm(llm_prompt)
            enhanced = enhanced.strip().strip('"').strip("'")
            
            # Validate length
            if len(enhanced) > 300:
                enhanced = enhanced[:297] + "..."
            
            logger.debug(f"Enhanced prompt: {base_prompt} -> {enhanced}")
            return enhanced
        
        except Exception as e:
            logger.warning(f"Failed to enhance prompt with LLM: {e}")
            return base_prompt
    
    async def _generate_with_suno(
        self,
        prompt: str,
        request: MusicGenerationRequest
    ) -> Optional[GeneratedMusic]:
        """
        Generate music using Suno API
        
        Args:
            prompt: Enhanced prompt
            request: Original request
            
        Returns:
            GeneratedMusic or None
        """
        if not self.suno_api_key:
            logger.error("Suno API key not configured")
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                # Create generation request
                payload = {
                    "prompt": prompt,
                    "duration": request.duration,
                    "style": request.style,
                    "mood": request.mood,
                }
                
                if request.tempo:
                    payload["tempo"] = request.tempo
                
                headers = {
                    "Authorization": f"Bearer {self.suno_api_key}",
                    "Content-Type": "application/json"
                }
                
                # Submit generation request
                async with session.post(
                    f"{self.suno_api_url}/generate",
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Suno API error: {response.status} - {error_text}")
                        return None
                    
                    result = await response.json()
                    generation_id = result.get('id')
                    
                    if not generation_id:
                        logger.error("No generation ID returned from Suno API")
                        return None
                
                # Poll for completion
                max_attempts = 60  # 5 minutes max
                for attempt in range(max_attempts):
                    await asyncio.sleep(5)  # Check every 5 seconds
                    
                    async with session.get(
                        f"{self.suno_api_url}/generate/{generation_id}",
                        headers=headers,
                        timeout=aiohttp.ClientTimeout(total=30)
                    ) as status_response:
                        if status_response.status != 200:
                            continue
                        
                        status_data = await status_response.json()
                        
                        if status_data.get('status') == 'completed':
                            audio_url = status_data.get('audio_url')
                            
                            if not audio_url:
                                logger.error("No audio URL in completed generation")
                                return None
                            
                            # Download audio file
                            file_path = await self._download_audio(
                                session,
                                audio_url,
                                f"suno_{generation_id}.mp3"
                            )
                            
                            if not file_path:
                                return None
                            
                            # Create result
                            return GeneratedMusic(
                                file_path=str(file_path),
                                title=status_data.get('title', 'Generated Music'),
                                prompt=prompt,
                                style=request.style or 'various',
                                mood=request.mood or 'neutral',
                                duration=request.duration,
                                backend=SynthesisBackend.SUNO_API,
                                generation_time=0.0,  # Will be set by caller
                                metadata=status_data
                            )
                        
                        elif status_data.get('status') == 'failed':
                            logger.error(f"Suno generation failed: {status_data.get('error')}")
                            return None
                
                logger.error("Suno generation timed out")
                return None
        
        except asyncio.TimeoutError:
            logger.error("Suno API request timed out")
            return None
        except Exception as e:
            logger.error(f"Error with Suno API: {e}", exc_info=True)
            return None
    
    async def _generate_with_musicgen(
        self,
        prompt: str,
        request: MusicGenerationRequest
    ) -> Optional[GeneratedMusic]:
        """
        Generate music using MusicGen (local)
        
        Args:
            prompt: Enhanced prompt
            request: Original request
            
        Returns:
            GeneratedMusic or None
        """
        try:
            from audiocraft.models import MusicGen
            from audiocraft.data.audio import audio_write
            import torch
            
            # Load model (cached after first load)
            if not hasattr(self, '_musicgen_model'):
                logger.info(f"Loading MusicGen model: {self.musicgen_model}")
                self._musicgen_model = MusicGen.get_pretrained(self.musicgen_model)
                logger.info("MusicGen model loaded")
            
            model = self._musicgen_model
            
            # Set generation parameters
            model.set_generation_params(
                duration=request.duration,
                temperature=1.0,
                top_k=250,
                top_p=0.0,
                cfg_coef=3.0
            )
            
            # Generate music
            logger.info(f"Generating music with MusicGen: {prompt}")
            
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            wav = await loop.run_in_executor(
                None,
                lambda: model.generate([prompt])
            )
            
            # Save audio file
            timestamp = int(time.time())
            filename = f"musicgen_{timestamp}"
            file_path = self.cache_dir / f"{filename}.wav"
            
            await loop.run_in_executor(
                None,
                lambda: audio_write(
                    str(self.cache_dir / filename),
                    wav[0].cpu(),
                    model.sample_rate,
                    strategy="loudness",
                    loudness_compressor=True
                )
            )
            
            # Create result
            return GeneratedMusic(
                file_path=str(file_path),
                title=f"Generated: {prompt[:50]}",
                prompt=prompt,
                style=request.style or 'various',
                mood=request.mood or 'neutral',
                duration=request.duration,
                backend=SynthesisBackend.MUSICGEN_LOCAL,
                generation_time=0.0,
                metadata={
                    'model': self.musicgen_model,
                    'sample_rate': model.sample_rate
                }
            )
        
        except ImportError:
            logger.error("audiocraft not installed, cannot use MusicGen backend")
            return None
        except Exception as e:
            logger.error(f"Error with MusicGen: {e}", exc_info=True)
            return None
    
    async def _generate_with_midi(
        self,
        prompt: str,
        request: MusicGenerationRequest
    ) -> Optional[GeneratedMusic]:
        """
        Generate music using MIDI fallback (simple procedural generation)
        
        This is a basic fallback that creates simple MIDI-based music.
        Quality is lower but doesn't require external APIs or heavy models.
        
        Args:
            prompt: Enhanced prompt
            request: Original request
            
        Returns:
            GeneratedMusic or None
        """
        try:
            # This would require a MIDI generation library
            # For now, return None and log that it's not implemented
            logger.warning("MIDI fallback generation not yet implemented")
            return None
            
            # TODO: Implement basic MIDI generation using:
            # - mido library for MIDI creation
            # - FluidSynth for MIDI to audio conversion
            # - Simple chord progressions and melodies based on mood/style
        
        except Exception as e:
            logger.error(f"Error with MIDI generation: {e}", exc_info=True)
            return None
    
    async def _download_audio(
        self,
        session: aiohttp.ClientSession,
        url: str,
        filename: str
    ) -> Optional[Path]:
        """
        Download audio file from URL
        
        Args:
            session: aiohttp session
            url: Audio file URL
            filename: Filename to save as
            
        Returns:
            Path to downloaded file or None
        """
        try:
            file_path = self.cache_dir / filename
            
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as response:
                if response.status != 200:
                    logger.error(f"Failed to download audio: {response.status}")
                    return None
                
                with open(file_path, 'wb') as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)
            
            logger.info(f"Downloaded audio to: {file_path}")
            return file_path
        
        except Exception as e:
            logger.error(f"Error downloading audio: {e}", exc_info=True)
            return None
    
    def _generate_cache_key(self, prompt: str, request: MusicGenerationRequest) -> str:
        """Generate cache key for a request"""
        key_data = {
            'prompt': prompt,
            'style': request.style,
            'mood': request.mood,
            'tempo': request.tempo,
            'duration': request.duration,
            'quality': request.quality.value,
            'backend': self.backend.value
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    async def _check_cache(self, cache_key: str) -> Optional[GeneratedMusic]:
        """Check if cached result exists"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            # Check if audio file still exists
            audio_path = Path(data['file_path'])
            if not audio_path.exists():
                # Cache invalid, remove metadata
                cache_file.unlink()
                return None
            
            # Reconstruct GeneratedMusic object
            return GeneratedMusic(
                file_path=data['file_path'],
                title=data['title'],
                prompt=data['prompt'],
                style=data['style'],
                mood=data['mood'],
                duration=data['duration'],
                backend=SynthesisBackend(data['backend']),
                generation_time=data['generation_time'],
                metadata=data['metadata']
            )
        
        except Exception as e:
            logger.warning(f"Error reading cache: {e}")
            return None
    
    async def _cache_result(self, cache_key: str, result: GeneratedMusic):
        """Cache generation result"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        try:
            data = asdict(result)
            data['backend'] = result.backend.value
            
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Clean up old cache if needed
            await self._cleanup_cache()
        
        except Exception as e:
            logger.warning(f"Error caching result: {e}")
    
    async def _cleanup_cache(self):
        """Clean up old cache files if size exceeds limit"""
        try:
            # Calculate total cache size
            total_size = 0
            cache_files = []
            
            for file in self.cache_dir.iterdir():
                if file.is_file():
                    size = file.stat().st_size
                    total_size += size
                    cache_files.append((file, size, file.stat().st_mtime))
            
            # Convert to MB
            total_size_mb = total_size / (1024 * 1024)
            
            if total_size_mb > self.max_cache_size_mb:
                logger.info(f"Cache size ({total_size_mb:.2f}MB) exceeds limit ({self.max_cache_size_mb}MB), cleaning up...")
                
                # Sort by modification time (oldest first)
                cache_files.sort(key=lambda x: x[2])
                
                # Remove oldest files until under limit
                for file, size, _ in cache_files:
                    if total_size_mb <= self.max_cache_size_mb * 0.8:  # 80% of limit
                        break
                    
                    file.unlink()
                    total_size_mb -= size / (1024 * 1024)
                    logger.debug(f"Removed cache file: {file.name}")
        
        except Exception as e:
            logger.warning(f"Error cleaning up cache: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get generation statistics"""
        stats = self.stats.copy()
        
        if stats['successful_generations'] > 0:
            stats['avg_generation_time'] = (
                stats['total_generation_time'] / stats['successful_generations']
            )
        else:
            stats['avg_generation_time'] = 0.0
        
        if stats['total_generations'] > 0:
            stats['success_rate'] = (
                stats['successful_generations'] / stats['total_generations']
            )
        else:
            stats['success_rate'] = 0.0
        
        return stats


def create_music_synthesis_service(config: dict, llm_service=None) -> MusicSynthesisService:
    """
    Factory function to create music synthesis service
    
    Args:
        config: Configuration dictionary
        llm_service: Optional LLM service for prompt enhancement
        
    Returns:
        MusicSynthesisService instance
    """
    return MusicSynthesisService(config, llm_service)
