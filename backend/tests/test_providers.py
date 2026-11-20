import json

import httpx
import pytest

from app.generation.providers import AnthropicProvider, LLMError, OpenAICompatibleProvider


def _client(status, payload, seen):
    def handler(request):
        seen.append((str(request.url), dict(request.headers), json.loads(request.content)))
        return httpx.Response(status, json=payload)
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_anthropic_provider_sends_system_and_joins_text():
    seen = []
    payload = {"content": [{"type": "text", "text": "Hello "}, {"type": "text", "text": "[1]"}]}
    p = AnthropicProvider("k", model="m", client=_client(200, payload, seen))
    assert p.complete("sys", "user") == "Hello [1]"
    url, headers, body = seen[0]
    assert url.endswith("/v1/messages")
    assert headers["x-api-key"] == "k"
    assert body["system"] == "sys" and body["messages"][0]["content"] == "user"


def test_anthropic_provider_requires_key():
    with pytest.raises(LLMError):
        AnthropicProvider("")


def test_anthropic_provider_raises_on_http_error():
    p = AnthropicProvider("k", client=_client(429, {"error": "rate"}, []))
    with pytest.raises(LLMError, match="429"):
        p.complete("s", "u")


def test_openai_provider_round_trip():
    seen = []
    payload = {"choices": [{"message": {"content": "answer"}}]}
    p = OpenAICompatibleProvider("http://localhost:11434/v1", "llama3",
                                 client=_client(200, payload, seen))
    assert p.complete("s", "u") == "answer"
    assert seen[0][0] == "http://localhost:11434/v1/chat/completions"
    assert seen[0][2]["messages"][0] == {"role": "system", "content": "s"}


def test_openai_provider_requires_url_and_model():
    with pytest.raises(LLMError):
        OpenAICompatibleProvider("", "")


from app.config import Settings  # noqa: E402
from app.generation.extractive import ExtractiveProvider  # noqa: E402
from app.generation.factory import build_llm  # noqa: E402


def test_factory_defaults_to_extractive():
    assert isinstance(build_llm(Settings()), ExtractiveProvider)


def test_factory_builds_openai_compatible():
    p = build_llm(Settings(llm_provider="ollama", llm_base_url="http://h/v1", llm_model="m"))
    assert isinstance(p, OpenAICompatibleProvider)


def test_factory_rejects_unknown():
    with pytest.raises(ValueError):
        build_llm(Settings(llm_provider="nope"))
