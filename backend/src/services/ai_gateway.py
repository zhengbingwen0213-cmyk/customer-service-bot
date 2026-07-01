"""Bailian HTTP gateways for chat completions and embeddings."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any, Literal

import httpx
from pycore.core import get_logger

from src.core.config import DEFAULT_BAILIAN_BASE_URL, AppSettings, get_settings

ChatRole = Literal["system", "user", "assistant"]


class BailianGatewayError(RuntimeError):
    """Base error for Bailian gateway failures."""


class BailianConfigurationError(BailianGatewayError):
    """Raised when required Bailian configuration is missing."""


class BailianAPIError(BailianGatewayError):
    """Raised when Bailian returns an error response or invalid payload."""


@dataclass(frozen=True)
class ChatMessage:
    role: ChatRole
    content: str


@dataclass(frozen=True)
class ChatCompletionResult:
    content: str
    model: str
    usage: dict[str, Any]


@dataclass(frozen=True)
class EmbeddingItem:
    index: int
    embedding: list[float]


@dataclass(frozen=True)
class EmbeddingResult:
    embeddings: list[EmbeddingItem]
    model: str
    dimensions: int
    usage: dict[str, Any]


class BailianGateway:
    """Minimal OpenAI-compatible HTTP client for Bailian."""

    def __init__(
        self,
        settings: AppSettings | None = None,
        *,
        timeout: float = 30.0,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._timeout = timeout
        self._transport = transport
        self._logger = get_logger()

    def is_chat_configured(self) -> bool:
        return all(
            (
                self._settings.dashscope_api_key.strip(),
                self._settings.bailian_base_url.strip(),
                self._settings.bailian_chat_model.strip(),
            )
        )

    def is_embedding_configured(self) -> bool:
        return all(
            (
                self._settings.dashscope_api_key.strip(),
                self._settings.bailian_embedding_model.strip(),
                self._settings.bailian_embedding_dimensions > 0,
            )
        )

    async def chat_completion(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> ChatCompletionResult:
        """Call Bailian chat completions through the OpenAI-compatible endpoint."""

        if not messages:
            raise ValueError("messages must not be empty")
        self._ensure_chat_configured()

        payload = {
            "model": self._settings.bailian_chat_model,
            "messages": [
                {
                    "role": message.role,
                    "content": message.content,
                }
                for message in messages
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        data = await self._post_json("chat/completions", payload)
        return self._parse_chat_response(data)

    async def create_embeddings(self, inputs: Sequence[str]) -> EmbeddingResult:
        """Create embeddings through Bailian's OpenAI-compatible endpoint."""

        if not inputs:
            raise ValueError("inputs must not be empty")
        self._ensure_embedding_configured()

        payload = {
            "model": self._settings.bailian_embedding_model,
            "input": list(inputs),
            "encoding_format": "float",
            "dimensions": self._settings.bailian_embedding_dimensions,
        }
        data = await self._post_json("embeddings", payload)
        return self._parse_embedding_response(data)

    async def _post_json(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        url = self._endpoint_url(endpoint)
        headers = {
            "Authorization": f"Bearer {self._settings.dashscope_api_key}",
            "Content-Type": "application/json",
        }
        try:
            async with httpx.AsyncClient(
                trust_env=False,
                timeout=self._timeout,
                transport=self._transport,
            ) as client:
                response = await client.post(url, headers=headers, json=payload)
        except httpx.HTTPError as exc:
            self._logger.error("Bailian HTTP request failed", endpoint=endpoint, error_msg=str(exc))
            raise BailianAPIError(f"Bailian HTTP request failed: {exc}") from exc

        try:
            data = response.json()
        except ValueError as exc:
            self._logger.error(
                "Bailian response is not valid JSON",
                endpoint=endpoint,
                status_code=response.status_code,
            )
            raise BailianAPIError("Bailian response is not valid JSON") from exc

        if response.status_code >= 400:
            error_detail = _extract_error_detail(data)
            self._logger.error(
                "Bailian API returned error",
                endpoint=endpoint,
                status_code=response.status_code,
                error_msg=error_detail,
            )
            raise BailianAPIError(
                f"Bailian API returned {response.status_code}: {error_detail}"
            )

        if not isinstance(data, dict):
            self._logger.error("Bailian response JSON is not an object", endpoint=endpoint)
            raise BailianAPIError("Bailian response JSON is not an object")

        return data

    def _endpoint_url(self, endpoint: str) -> str:
        base_url = (self._settings.bailian_base_url.strip() or DEFAULT_BAILIAN_BASE_URL).rstrip(
            "/"
        )
        if base_url.endswith(f"/{endpoint}"):
            return base_url
        return f"{base_url}/{endpoint}"

    def _ensure_chat_configured(self) -> None:
        if not self.is_chat_configured():
            raise BailianConfigurationError(
                "Bailian chat is not configured; required fields: "
                "DASHSCOPE_API_KEY, BAILIAN_BASE_URL, BAILIAN_CHAT_MODEL"
            )

    def _ensure_embedding_configured(self) -> None:
        if not self.is_embedding_configured():
            raise BailianConfigurationError(
                "Bailian embeddings are not configured; required fields: "
                "DASHSCOPE_API_KEY, BAILIAN_EMBEDDING_MODEL, "
                "BAILIAN_EMBEDDING_DIMENSIONS"
            )

    def _parse_chat_response(self, data: dict[str, Any]) -> ChatCompletionResult:
        try:
            choices = data["choices"]
            first_choice = choices[0]
            content = first_choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            self._logger.error("Bailian chat response has unexpected shape", keys=list(data))
            raise BailianAPIError("Bailian chat response has unexpected shape") from exc

        if not isinstance(content, str) or not content:
            raise BailianAPIError("Bailian chat response content is empty")

        usage = data.get("usage", {})
        return ChatCompletionResult(
            content=content,
            model=_string_value(data.get("model"), self._settings.bailian_chat_model),
            usage=usage if isinstance(usage, dict) else {},
        )

    def _parse_embedding_response(self, data: dict[str, Any]) -> EmbeddingResult:
        raw_items = data.get("data")
        if not isinstance(raw_items, list) or not raw_items:
            raise BailianAPIError("Bailian embedding response data is empty")

        items: list[EmbeddingItem] = []
        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                raise BailianAPIError("Bailian embedding response item is invalid")
            raw_embedding = raw_item.get("embedding")
            if not isinstance(raw_embedding, list) or not raw_embedding:
                raise BailianAPIError("Bailian embedding vector is empty")
            embedding = [float(value) for value in raw_embedding]
            if len(embedding) != self._settings.bailian_embedding_dimensions:
                raise BailianAPIError(
                    "Bailian embedding dimensions mismatch: "
                    f"expected {self._settings.bailian_embedding_dimensions}, "
                    f"got {len(embedding)}"
                )
            items.append(
                EmbeddingItem(
                    index=int(raw_item.get("index", len(items))),
                    embedding=embedding,
                )
            )

        usage = data.get("usage", {})
        return EmbeddingResult(
            embeddings=items,
            model=_string_value(data.get("model"), self._settings.bailian_embedding_model),
            dimensions=self._settings.bailian_embedding_dimensions,
            usage=usage if isinstance(usage, dict) else {},
        )


def _extract_error_detail(data: Any) -> str:
    if isinstance(data, dict):
        error = data.get("error")
        if isinstance(error, dict):
            detail = error.get("message") or error.get("code")
            if detail:
                return str(detail)
        for key in ("message", "code", "request_id"):
            value = data.get(key)
            if value:
                return str(value)
    return "unknown error"


def _string_value(value: Any, fallback: str) -> str:
    if isinstance(value, str) and value:
        return value
    return fallback
