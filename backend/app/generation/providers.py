"""LLM providers. All expose `complete(system, user) -> str`."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from collections.abc import Iterator

import httpx


class LLMError(RuntimeError):
    pass


class LLMProvider(ABC):
    name: str = "base"

    @abstractmethod
    def complete(self, system: str, user: str) -> str: ...

    def stream(self, system: str, user: str) -> Iterator[str]:
        yield self.complete(system, user)


class AnthropicProvider(LLMProvider):
    name = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-sonnet-5-5", max_tokens: int = 1024,
                 base_url: str = "https://api.anthropic.com",
                 client: httpx.Client | None = None) -> None:
        if not api_key:
            raise LLMError("RAGFORGE_LLM_API_KEY is required for the anthropic provider")
        self.model = model
        self.max_tokens = max_tokens
        self.base_url = base_url.rstrip("/")
        self.client = client or httpx.Client(timeout=120)
        self.headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01"}

    def complete(self, system: str, user: str) -> str:
        resp = self.client.post(
            f"{self.base_url}/v1/messages",
            headers=self.headers,
            json={"model": self.model, "max_tokens": self.max_tokens, "system": system,
                  "messages": [{"role": "user", "content": user}]},
        )
        if resp.status_code >= 400:
            raise LLMError(f"Anthropic API error {resp.status_code}: {resp.text[:200]}")
        return "".join(b.get("text", "") for b in resp.json()["content"] if b["type"] == "text")

    def stream(self, system: str, user: str) -> Iterator[str]:
        body = {"model": self.model, "max_tokens": self.max_tokens, "system": system,
                "stream": True, "messages": [{"role": "user", "content": user}]}
        with self.client.stream("POST", f"{self.base_url}/v1/messages", headers=self.headers,
                                json=body) as resp:
            if resp.status_code >= 400:
                resp.read()
                raise LLMError(f"Anthropic API error {resp.status_code}: {resp.text[:200]}")
            for line in resp.iter_lines():
                if not line.startswith("data:"):
                    continue
                event = json.loads(line[5:].strip())
                if event.get("type") == "content_block_delta":
                    delta = event.get("delta", {})
                    if delta.get("type") == "text_delta":
                        yield delta.get("text", "")


class OpenAICompatibleProvider(LLMProvider):
    """Works with any /chat/completions endpoint: OpenAI, Ollama, vLLM, LM Studio."""

    name = "openai"

    def __init__(self, base_url: str, model: str, api_key: str = "",
                 temperature: float = 0.1, client: httpx.Client | None = None) -> None:
        if not base_url or not model:
            raise LLMError("base_url and model are required for the openai provider")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature
        self.client = client or httpx.Client(timeout=120)
        self.headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}

    def complete(self, system: str, user: str) -> str:
        resp = self.client.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json={"model": self.model, "temperature": self.temperature,
                  "messages": [{"role": "system", "content": system},
                               {"role": "user", "content": user}]},
        )
        if resp.status_code >= 400:
            raise LLMError(f"LLM endpoint error {resp.status_code}: {resp.text[:200]}")
        return resp.json()["choices"][0]["message"]["content"]

    def stream(self, system: str, user: str) -> Iterator[str]:
        body = {"model": self.model, "temperature": self.temperature, "stream": True,
                "messages": [{"role": "system", "content": system},
                             {"role": "user", "content": user}]}
        with self.client.stream("POST", f"{self.base_url}/chat/completions",
                                headers=self.headers, json=body) as resp:
            if resp.status_code >= 400:
                resp.read()
                raise LLMError(f"LLM endpoint error {resp.status_code}: {resp.text[:200]}")
            for line in resp.iter_lines():
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                delta = json.loads(payload)["choices"][0].get("delta", {})
                if delta.get("content"):
                    yield delta["content"]
