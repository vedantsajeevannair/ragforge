"""Build the configured LLM provider."""

from app.config import Settings
from app.generation.extractive import ExtractiveProvider
from app.generation.providers import AnthropicProvider, LLMProvider, OpenAICompatibleProvider


def build_llm(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.lower()
    if provider == "extractive":
        return ExtractiveProvider()
    if provider == "anthropic":
        return AnthropicProvider(settings.llm_api_key, settings.llm_model or "claude-sonnet-5-5")
    if provider in {"openai", "ollama"}:
        return OpenAICompatibleProvider(settings.llm_base_url, settings.llm_model,
                                        settings.llm_api_key)
    raise ValueError(f"unknown llm provider '{settings.llm_provider}'")
