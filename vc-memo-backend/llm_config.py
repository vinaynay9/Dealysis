import os
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()


def get_llm(model: str = "gpt-4", temperature: float = 0.3) -> ChatOpenAI:
    """Get OpenAI LLM instance with rate limiting configuration"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")

    return ChatOpenAI(
        model=model,
        api_key=api_key,
        temperature=temperature,
        timeout=120.0,  # Increased timeout for rate limit retries
        max_retries=0,  # We handle retries ourselves with rate_limiter
    )


def get_extraction_llm() -> ChatOpenAI:
    """High-precision LLM for data extraction"""
    return get_llm(model="gpt-4", temperature=0.1)


def get_generation_llm() -> ChatOpenAI:
    """Creative LLM for memo writing"""
    return get_llm(model="gpt-4", temperature=0.4)
