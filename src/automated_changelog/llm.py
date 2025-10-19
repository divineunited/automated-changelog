"""LLM client configuration for changelog generation."""

import os

from dotenv import load_dotenv
from litellm import completion

# Load environment variables
load_dotenv()


def get_llm_client():
    """
    Get configured LLM client based on environment variables.

    Supports:
    - LiteLLM Proxy (if LITELLM_PROXY_API_BASE and LITELLM_PROXY_API_KEY are set)
    - Direct Anthropic API (if ANTHROPIC_API_KEY is set)

    Returns:
        Configured client settings dict
    """
    proxy_base = os.getenv("LITELLM_PROXY_API_BASE")
    proxy_key = os.getenv("LITELLM_PROXY_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    if proxy_base and proxy_key:
        return {
            "api_base": proxy_base,
            "api_key": proxy_key,
            "provider": "litellm_proxy",
        }
    elif anthropic_key:
        return {
            "api_key": anthropic_key,
            "provider": "anthropic",
        }
    else:
        raise ValueError(
            "No LLM API credentials found. Set either:\n"
            "  - LITELLM_PROXY_API_BASE and LITELLM_PROXY_API_KEY, or\n"
            "  - ANTHROPIC_API_KEY"
        )


def call_llm(
    prompt: str,
    model: str = "claude-sonnet-4-5",
    max_tokens: int = 7096,
) -> str:
    """
    Call LLM with the given prompt.

    Args:
        prompt: The prompt to send to the LLM
        model: Model identifier
        max_tokens: Maximum tokens in response

    Returns:
        LLM response text
    """
    client_config = get_llm_client()

    # Build completion kwargs
    kwargs = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }

    # Add API configuration based on provider
    if client_config["provider"] == "litellm_proxy":
        kwargs["api_base"] = client_config["api_base"]
        kwargs["api_key"] = client_config["api_key"]
    else:
        kwargs["api_key"] = client_config["api_key"]

    response = completion(**kwargs)
    return response.choices[0].message.content
