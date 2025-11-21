"""
Utility decorators for Discord Music Bot
Provides rate limiting, error handling, and common functionality
"""
import asyncio
import functools
import time
from typing import Callable, Dict, Any, Optional
from collections import defaultdict, deque

import discord
from discord.ext import commands

from core.exceptions import RateLimitError, OwnerOnlyError, get_user_friendly_message
from utils.logger import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """
    Rate limiter using token bucket algorithm
    """
    
    def __init__(self, rate: int, per: float):
        """
        Initialize rate limiter
        
        Args:
            rate: Number of calls allowed
            per: Time period in seconds
        """
        self.rate = rate
        self.per = per
        self.allowance = rate
        self.last_check = time.time()
        self.lock = asyncio.Lock()
    
    async def acquire(self) -> bool:
        """
        Try to acquire a token
        
        Returns:
            True if token acquired, False if rate limited
        """
        async with self.lock:
            current = time.time()
            time_passed = current - self.last_check
            self.last_check = current
            
            # Add tokens based on time passed
            self.allowance += time_passed * (self.rate / self.per)
            
            # Cap at rate
            if self.allowance > self.rate:
                self.allowance = self.rate
            
            # Try to consume a token
            if self.allowance < 1.0:
                return False
            
            self.allowance -= 1.0
            return True


class UserRateLimiter:
    """
    Per-user rate limiter
    """
    
    def __init__(self, rate: int, per: float):
        """
        Initialize per-user rate limiter
        
        Args:
            rate: Number of calls allowed per user
            per: Time period in seconds
        """
        self.rate = rate
        self.per = per
        self.limiters: Dict[int, RateLimiter] = {}
        self.cleanup_interval = 300  # Clean up every 5 minutes
        self.last_cleanup = time.time()
    
    def get_limiter(self, user_id: int) -> RateLimiter:
        """Get or create rate limiter for user"""
        if user_id not in self.limiters:
            self.limiters[user_id] = RateLimiter(self.rate, self.per)
        
        # Periodic cleanup
        if time.time() - self.last_cleanup > self.cleanup_interval:
            self._cleanup()
        
        return self.limiters[user_id]
    
    def _cleanup(self):
        """Remove inactive limiters"""
        current = time.time()
        to_remove = []
        
        for user_id, limiter in self.limiters.items():
            if current - limiter.last_check > self.cleanup_interval:
                to_remove.append(user_id)
        
        for user_id in to_remove:
            del self.limiters[user_id]
        
        self.last_cleanup = current
    
    async def acquire(self, user_id: int) -> bool:
        """Try to acquire token for user"""
        limiter = self.get_limiter(user_id)
        return await limiter.acquire()


def rate_limit(rate: int, per: float, per_user: bool = True):
    """
    Rate limiting decorator
    
    Args:
        rate: Number of calls allowed
        per: Time period in seconds
        per_user: If True, rate limit per user; if False, global rate limit
        
    Usage:
        @rate_limit(rate=5, per=60.0, per_user=True)  # 5 calls per minute per user
        async def my_command(ctx):
            ...
    """
    if per_user:
        limiter = UserRateLimiter(rate, per)
    else:
        limiter = RateLimiter(rate, per)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract user ID from context
            ctx = None
            for arg in args:
                if isinstance(arg, commands.Context):
                    ctx = arg
                    break
            
            if not ctx:
                # No context, skip rate limiting
                return await func(*args, **kwargs)
            
            # Check rate limit
            if per_user:
                allowed = await limiter.acquire(ctx.author.id)
            else:
                allowed = await limiter.acquire()
            
            if not allowed:
                raise RateLimitError(
                    f"Rate limit exceeded. Please wait before trying again.",
                    details={"rate": rate, "per": per}
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def owner_only():
    """
    Decorator to restrict command to bot owner only
    
    Usage:
        @owner_only()
        async def admin_command(ctx):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract context
            ctx = None
            for arg in args:
                if isinstance(arg, commands.Context):
                    ctx = arg
                    break
            
            if not ctx:
                return await func(*args, **kwargs)
            
            # Check if user is owner
            app_info = await ctx.bot.application_info()
            if ctx.author.id != app_info.owner.id:
                raise OwnerOnlyError(
                    "This command is restricted to the bot owner",
                    details={"user_id": ctx.author.id}
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def handle_errors(send_to_user: bool = True):
    """
    Error handling decorator with user-friendly messages
    
    Args:
        send_to_user: If True, send error message to user
        
    Usage:
        @handle_errors(send_to_user=True)
        async def my_command(ctx):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            ctx = None
            for arg in args:
                if isinstance(arg, commands.Context):
                    ctx = arg
                    break
            
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Log the error
                logger.error(
                    f"Error in {func.__name__}: {e}",
                    exc_info=True,
                    extra={"function": func.__name__}
                )
                
                # Send user-friendly message
                if send_to_user and ctx:
                    message = get_user_friendly_message(e)
                    try:
                        await ctx.send(message)
                    except discord.HTTPException:
                        logger.error("Failed to send error message to user")
                
                # Re-raise if not handled
                raise
        
        return wrapper
    return decorator


def require_voice():
    """
    Decorator to ensure user is in a voice channel
    
    Usage:
        @require_voice()
        async def play_command(ctx):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            ctx = None
            for arg in args:
                if isinstance(arg, commands.Context):
                    ctx = arg
                    break
            
            if not ctx:
                return await func(*args, **kwargs)
            
            # Check if user is in voice channel
            if not ctx.author.voice:
                await ctx.send("❌ You need to be in a voice channel to use this command!")
                return
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_bot_voice():
    """
    Decorator to ensure bot is in a voice channel
    
    Usage:
        @require_bot_voice()
        async def skip_command(ctx):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            ctx = None
            for arg in args:
                if isinstance(arg, commands.Context):
                    ctx = arg
                    break
            
            if not ctx:
                return await func(*args, **kwargs)
            
            # Check if bot is in voice channel
            if not ctx.voice_client:
                await ctx.send("❌ I'm not in a voice channel!")
                return
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def require_same_voice():
    """
    Decorator to ensure user and bot are in the same voice channel
    
    Usage:
        @require_same_voice()
        async def skip_command(ctx):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            ctx = None
            for arg in args:
                if isinstance(arg, commands.Context):
                    ctx = arg
                    break
            
            if not ctx:
                return await func(*args, **kwargs)
            
            # Check if user is in voice
            if not ctx.author.voice:
                await ctx.send("❌ You need to be in a voice channel!")
                return
            
            # Check if bot is in voice
            if not ctx.voice_client:
                await ctx.send("❌ I'm not in a voice channel!")
                return
            
            # Check if same channel
            if ctx.author.voice.channel.id != ctx.voice_client.channel.id:
                await ctx.send("❌ You need to be in the same voice channel as me!")
                return
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def log_command():
    """
    Decorator to log command usage
    
    Usage:
        @log_command()
        async def my_command(ctx):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            ctx = None
            for arg in args:
                if isinstance(arg, commands.Context):
                    ctx = arg
                    break
            
            if ctx:
                logger.info(
                    f"Command: {func.__name__}",
                    extra={
                        "command": func.__name__,
                        "user_id": ctx.author.id,
                        "user_name": str(ctx.author),
                        "guild_id": ctx.guild.id if ctx.guild else None,
                        "guild_name": ctx.guild.name if ctx.guild else None,
                        "channel_id": ctx.channel.id,
                    }
                )
            
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Retry decorator with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier
        
    Usage:
        @retry(max_attempts=3, delay=1.0, backoff=2.0)
        async def unstable_operation():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {current_delay}s..."
                        )
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )
            
            # All attempts failed, raise last exception
            raise last_exception
        
        return wrapper
    return decorator


def cache_result(ttl: float = 300.0):
    """
    Cache decorator with TTL (time to live)
    
    Args:
        ttl: Time to live in seconds
        
    Usage:
        @cache_result(ttl=300.0)  # Cache for 5 minutes
        async def expensive_operation(param):
            ...
    """
    cache: Dict[str, tuple] = {}  # key -> (result, timestamp)
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Create cache key from args and kwargs
            cache_key = f"{func.__name__}:{str(args)}:{str(sorted(kwargs.items()))}"
            
            # Check cache
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if time.time() - timestamp < ttl:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return result
            
            # Call function
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache[cache_key] = (result, time.time())
            
            # Cleanup old entries (simple approach)
            if len(cache) > 1000:
                current_time = time.time()
                expired = [k for k, (_, ts) in cache.items() if current_time - ts > ttl]
                for k in expired:
                    del cache[k]
            
            return result
        
        return wrapper
    return decorator


def typing_indicator():
    """
    Show typing indicator while command executes
    
    Usage:
        @typing_indicator()
        async def long_running_command(ctx):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            ctx = None
            for arg in args:
                if isinstance(arg, commands.Context):
                    ctx = arg
                    break
            
            if ctx:
                async with ctx.typing():
                    return await func(*args, **kwargs)
            else:
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator
