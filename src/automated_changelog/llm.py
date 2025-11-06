"""LLM client configuration for changelog generation."""

import os
import ssl

from dotenv import load_dotenv
from litellm import completion

# Load environment variables (.env file overrides shell environment)
load_dotenv(override=True)

# Disable SSL verification for internal proxies if needed
# This is set via environment variable: SSL_VERIFY=false
if os.getenv("SSL_VERIFY", "true").lower() == "false":
    ssl._create_default_https_context = ssl._create_unverified_context


def get_llm_client():
    """
    Get configured LLM client based on environment variables.

    Requires LiteLLM Proxy configuration:
    - LITELLM_PROXY_API_BASE: Base URL for LiteLLM proxy
    - LITELLM_PROXY_API_KEY or LITELLM_API_KEY: API key for the proxy

    Returns:
        Configured client settings dict
    """
    proxy_base = os.getenv("LITELLM_PROXY_API_BASE")
    # Try multiple key names for proxy
    proxy_key = os.getenv("LITELLM_PROXY_API_KEY") or os.getenv("LITELLM_API_KEY")

    if proxy_base and proxy_key:
        return {
            "api_base": proxy_base,
            "api_key": proxy_key,
            "provider": "litellm_proxy",
        }
    else:
        raise ValueError(
            "No LLM API credentials found. Please set:\n"
            "  - LITELLM_PROXY_API_BASE and\n"
            "  - LITELLM_PROXY_API_KEY (or LITELLM_API_KEY)"
        )


def call_llm(
    prompt: str,
    model: str = "claude-sonnet-4-5",
    max_tokens: int = 7096,
) -> str:
    """
    Call LLM with the given prompt via LiteLLM proxy.

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
        "api_base": client_config["api_base"],
        "api_key": client_config["api_key"],
    }

    response = completion(**kwargs)
    return response.choices[0].message.content or ""
