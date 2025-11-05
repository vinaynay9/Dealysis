import asyncio
import time
from typing import Callable, Any, Optional
from functools import wraps
import openai


class RateLimiter:
    """Rate limiter with exponential backoff for OpenAI API calls"""

    def __init__(
        self,
        max_retries: int = 5,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
    ):
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self._last_request_time = 0.0
        self._min_request_interval = 0.1  # Minimum 100ms between requests

    async def _wait_if_needed(self):
        """Ensure minimum interval between requests"""
        now = time.time()
        time_since_last = now - self._last_request_time
        if time_since_last < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - time_since_last)
        self._last_request_time = time.time()

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay"""
        delay = self.initial_delay * (self.exponential_base ** attempt)
        
        # Apply jitter (random variation)
        if self.jitter:
            import random
            jitter_amount = delay * 0.1  # 10% jitter
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return min(delay, self.max_delay)

    async def _retry_with_backoff(
        self,
        func: Callable,
        *args,
        **kwargs,
    ) -> Any:
        """Execute function with exponential backoff retry logic"""
        
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                # Wait minimum interval before request
                await self._wait_if_needed()
                
                # Execute the function
                # Check if function is a coroutine (handles both functions and bound methods)
                if asyncio.iscoroutinefunction(func) or (
                    hasattr(func, '__func__') and asyncio.iscoroutinefunction(func.__func__)
                ):
                    result = await func(*args, **kwargs)
                else:
                    result = func(*args, **kwargs)
                
                return result
                
            except Exception as e:
                # Check if it's a rate limit error (various exception types)
                error_str = str(e).lower()
                is_rate_limit = (
                    isinstance(e, openai.RateLimitError)
                    or "rate limit" in error_str
                    or "429" in error_str
                    or "rate_limit_exceeded" in error_str
                    or "tokens per min" in error_str
                    or "tpm" in error_str
                )
                
                if is_rate_limit and attempt < self.max_retries - 1:
                    # Extract wait time from error message if available
                    wait_time = self._extract_wait_time(str(e))
                    if wait_time is None:
                        wait_time = self._calculate_delay(attempt)
                    
                    print(f"Rate limit hit (attempt {attempt + 1}/{self.max_retries}). Waiting {wait_time:.2f}s...")
                    await asyncio.sleep(wait_time)
                    last_exception = e
                    continue
                elif self._is_retryable_error(e) and attempt < self.max_retries - 1:
                    # Other retryable errors
                    wait_time = self._calculate_delay(attempt)
                    print(f"Retryable error (attempt {attempt + 1}/{self.max_retries}): {str(e)[:100]}. Waiting {wait_time:.2f}s...")
                    await asyncio.sleep(wait_time)
                    last_exception = e
                    continue
                else:
                    # Non-retryable error or max retries reached
                    raise
                    
        
        # If we exhausted retries, raise the last exception
        if last_exception:
            raise last_exception
        raise Exception("Max retries exceeded")

    def _extract_wait_time(self, error_message: str) -> Optional[float]:
        """Extract wait time from OpenAI rate limit error message"""
        import re
        
        # Look for patterns like "try again in 7.41s" or "retry_after: 5"
        patterns = [
            r"try again in ([\d.]+)s",
            r"retry[_\s]after[:\s]+([\d.]+)",
            r"wait[_\s]+([\d.]+)[\s]*seconds?",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_message, re.IGNORECASE)
            if match:
                try:
                    wait_time = float(match.group(1))
                    # Add small buffer (10%)
                    return wait_time * 1.1
                except ValueError:
                    continue
        
        return None

    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if error is retryable"""
        error_str = str(error).lower()
        
        retryable_patterns = [
            "timeout",
            "connection",
            "temporary",
            "503",
            "502",
            "500",
            "429",
        ]
        
        return any(pattern in error_str for pattern in retryable_patterns)

    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute a function with rate limiting and retry logic"""
        return await self._retry_with_backoff(func, *args, **kwargs)


# Global rate limiter instance
_rate_limiter = RateLimiter()


def rate_limited(func: Callable) -> Callable:
    """Decorator to add rate limiting to async functions"""
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await _rate_limiter.execute(func, *args, **kwargs)
    
    return wrapper


async def batch_process_with_rate_limit(
    items: list,
    process_func: Callable,
    batch_size: int = 5,
    delay_between_batches: float = 0.5,
) -> list:
    """
    Process items in batches with rate limiting and delays between batches.
    
    Args:
        items: List of items to process
        process_func: Async function to process each item
        batch_size: Number of items to process in parallel per batch
        delay_between_batches: Delay in seconds between batches
    
    Returns:
        List of results in the same order as input items
    """
    results = []
    rate_limiter = RateLimiter()
    
    for i in range(0, len(items), batch_size):
        batch = items[i : i + batch_size]
        
        # Process batch with rate limiting
        batch_tasks = [
            rate_limiter.execute(process_func, item) for item in batch
        ]
        
        batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
        results.extend(batch_results)
        
        # Add delay between batches (except for the last batch)
        if i + batch_size < len(items):
            await asyncio.sleep(delay_between_batches)
    
    return results

