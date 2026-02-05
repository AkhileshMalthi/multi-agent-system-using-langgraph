"""LLM Provider factory for multi-provider support."""

import os
from enum import Enum
from typing import Any

from langchain_core.language_models import BaseChatModel


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    GROQ = "groq"


# Default models for each provider
DEFAULT_MODELS = {
    LLMProvider.OPENAI: "gpt-4o-mini",
    LLMProvider.GROQ: "llama-3.3-70b-versatile",
}


def get_llm_provider() -> LLMProvider:
    """
    Get the configured LLM provider from environment.
    
    Environment variable: LLM_PROVIDER
    Default: groq
    """
    provider = os.environ.get("LLM_PROVIDER", "groq").lower()
    
    try:
        return LLMProvider(provider)
    except ValueError:
        # Default to Groq if invalid provider specified
        return LLMProvider.GROQ


def get_llm(
    temperature: float = 0.3,
    model: str | None = None,
    provider: LLMProvider | None = None,
    **kwargs: Any,
) -> BaseChatModel:
    """
    Get an LLM instance based on the configured provider.
    
    Args:
        temperature: Model temperature (0.0-1.0)
        model: Optional model name override
        provider: Optional provider override (uses env var if not specified)
        **kwargs: Additional provider-specific arguments
        
    Returns:
        A LangChain chat model instance
        
    Raises:
        ValueError: If required API key is not set
    """
    if provider is None:
        provider = get_llm_provider()
    
    if model is None:
        model = DEFAULT_MODELS.get(provider)
    
    if provider == LLMProvider.OPENAI:
        return _get_openai_llm(model, temperature, **kwargs)
    elif provider == LLMProvider.GROQ:
        return _get_groq_llm(model, temperature, **kwargs)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def _get_openai_llm(
    model: str,
    temperature: float,
    **kwargs: Any,
) -> BaseChatModel:
    """Create an OpenAI chat model."""
    from langchain_openai import ChatOpenAI
    
    api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("LLM_API_KEY")
    
    if not api_key:
        raise ValueError(
            "OpenAI API key not found. Set OPENAI_API_KEY or LLM_API_KEY environment variable."
        )
    
    return ChatOpenAI(
        model=model,
        api_key=api_key,
        temperature=temperature,
        **kwargs,
    )


def _get_groq_llm(
    model: str,
    temperature: float,
    **kwargs: Any,
) -> BaseChatModel:
    """Create a Groq chat model."""
    from langchain_groq import ChatGroq
    
    api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("LLM_API_KEY")
    
    if not api_key:
        raise ValueError(
            "Groq API key not found. Set GROQ_API_KEY or LLM_API_KEY environment variable."
        )
    
    return ChatGroq(
        model=model,
        api_key=api_key,
        temperature=temperature,
        **kwargs,
    )
