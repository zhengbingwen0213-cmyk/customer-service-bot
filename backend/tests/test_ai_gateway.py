from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from src.core.config import DEFAULT_BAILIAN_BASE_URL, AppSettings
from src.services.ai_gateway import (
    BailianAPIError,
    BailianConfigurationError,
    BailianGateway,
    ChatMessage,
)


def _settings(**overrides: object) -> AppSettings:
    data: dict[str, object] = {
        "dashscope_api_key": "test-key",
        "bailian_base_url": "https://example.invalid/compatible-mode/v1",
        "bailian_chat_model": "qwen-test",
        "bailian_embedding_model": "embedding-test",
        "bailian_embedding_dimensions": 3,
    }
    data.update(overrides)
    return AppSettings(**data)


def test_bailian_chat_completion_uses_openai_compatible_http_payload() -> None:
    async def run() -> None:
        requests: list[httpx.Request] = []

        def handler(request: httpx.Request) -> httpx.Response:
            requests.append(request)
            body = json.loads(request.content)
            assert request.url.path == "/compatible-mode/v1/chat/completions"
            assert request.headers["authorization"] == "Bearer test-key"
            assert body["model"] == "qwen-test"
            assert body["messages"] == [{"role": "user", "content": "ping"}]
            return httpx.Response(
                200,
                json={
                    "model": "qwen-test",
                    "choices": [{"message": {"role": "assistant", "content": "pong"}}],
                    "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
                },
            )

        gateway = BailianGateway(_settings(), transport=httpx.MockTransport(handler))
        result = await gateway.chat_completion([ChatMessage(role="user", content="ping")])

        assert len(requests) == 1
        assert result.content == "pong"
        assert result.model == "qwen-test"
        assert result.usage["total_tokens"] == 2

    asyncio.run(run())


def test_bailian_embedding_parses_dimensions_and_usage() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            assert request.url.path == "/compatible-mode/v1/embeddings"
            assert body == {
                "model": "embedding-test",
                "input": ["退款多久到账？"],
                "encoding_format": "float",
                "dimensions": 3,
            }
            return httpx.Response(
                200,
                json={
                    "model": "embedding-test",
                    "data": [{"index": 0, "embedding": [0.1, 0.2, 0.3]}],
                    "usage": {"prompt_tokens": 3, "total_tokens": 3},
                },
            )

        gateway = BailianGateway(_settings(), transport=httpx.MockTransport(handler))
        result = await gateway.create_embeddings(["退款多久到账？"])

        assert result.model == "embedding-test"
        assert result.dimensions == 3
        assert result.embeddings[0].embedding == [0.1, 0.2, 0.3]
        assert result.usage["total_tokens"] == 3

    asyncio.run(run())


def test_bailian_embedding_configuration_does_not_require_base_url() -> None:
    settings = _settings(bailian_base_url="")
    gateway = BailianGateway(settings)

    assert gateway.is_embedding_configured()
    assert not gateway.is_chat_configured()


def test_bailian_embedding_uses_default_gateway_endpoint_when_base_url_blank() -> None:
    async def run() -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            assert str(request.url) == f"{DEFAULT_BAILIAN_BASE_URL}/embeddings"
            return httpx.Response(
                200,
                json={
                    "model": "embedding-test",
                    "data": [{"index": 0, "embedding": [0.1, 0.2, 0.3]}],
                },
            )

        gateway = BailianGateway(
            _settings(bailian_base_url=""),
            transport=httpx.MockTransport(handler),
        )
        result = await gateway.create_embeddings(["退款多久到账？"])

        assert result.dimensions == 3

    asyncio.run(run())


def test_bailian_embedding_configuration_error_lists_only_embedding_fields() -> None:
    async def run() -> None:
        gateway = BailianGateway(_settings(bailian_embedding_model=""))

        with pytest.raises(BailianConfigurationError) as exc_info:
            await gateway.create_embeddings(["退款多久到账？"])

        message = str(exc_info.value)
        assert "DASHSCOPE_API_KEY" in message
        assert "BAILIAN_EMBEDDING_MODEL" in message
        assert "BAILIAN_EMBEDDING_DIMENSIONS" in message
        assert "BAILIAN_BASE_URL" not in message

    asyncio.run(run())


def test_bailian_gateway_surfaces_api_errors() -> None:
    async def run() -> None:
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                401,
                json={"error": {"message": "invalid api key"}},
            )

        gateway = BailianGateway(_settings(), transport=httpx.MockTransport(handler))
        with pytest.raises(BailianAPIError, match="invalid api key"):
            await gateway.chat_completion([ChatMessage(role="user", content="ping")])

    asyncio.run(run())


def test_bailian_embedding_dimension_mismatch_fails_loudly() -> None:
    async def run() -> None:
        def handler(_request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "model": "embedding-test",
                    "data": [{"index": 0, "embedding": [0.1, 0.2]}],
                },
            )

        gateway = BailianGateway(_settings(), transport=httpx.MockTransport(handler))
        with pytest.raises(BailianAPIError, match="dimensions mismatch"):
            await gateway.create_embeddings(["退款多久到账？"])

    asyncio.run(run())
