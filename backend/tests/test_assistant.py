from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Generator, Sequence
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.api.deps import get_db
from src.db.models import Base
from src.db.schema import create_fts5_indexes, rebuild_fts5_indexes
from src.db.seed import seed_demo_data
from src.main import app
from src.services.ai_gateway import (
    BailianAPIError,
    BailianGateway,
    ChatCompletionResult,
    ChatMessage,
)
from src.services.auth import reset_token_store


class ChatRecorder:
    def __init__(self, answer: str = "fake generated answer") -> None:
        self.answer = answer
        self.calls: list[list[ChatMessage]] = []

    async def chat_completion(
        self,
        messages: Sequence[ChatMessage],
        *,
        temperature: float = 0.2,
        max_tokens: int = 512,
    ) -> ChatCompletionResult:
        del temperature, max_tokens
        self.calls.append(list(messages))
        return ChatCompletionResult(content=self.answer, model="fake-qwen", usage={})


@pytest.fixture()
def client(tmp_path: Path) -> Generator[TestClient, None, None]:
    db_path = tmp_path / "assistant_test.db"
    test_engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", future=True)
    session_factory = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        async with session_factory() as session:
            yield session

    asyncio.run(_setup_database(test_engine, session_factory))
    reset_token_store()
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
        reset_token_store()
        asyncio.run(test_engine.dispose())


def test_assistant_qa_direct_uses_enabled_qa_before_generation(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_if_called(*_args: Any, **_kwargs: Any) -> ChatCompletionResult:
        raise AssertionError("QA direct must not call chat generation")

    monkeypatch.setattr(BailianGateway, "chat_completion", fail_if_called)
    headers = _login_headers(client)

    response = client.post(
        "/api/assistant/ask",
        headers=headers,
        json={"question": "退款多久到账？", "scene": "debug"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    answer = body["data"]["answer"]
    assert answer["answer_type"] == "qa_direct"
    assert answer["answer"] == "正常情况下，退款会在 1-3 个工作日内原路退回您的支付账户。"
    assert answer["references"][0]["type"] == "qa"
    assert answer["references"][0]["source_id"] == "qa_001"
    assert answer["references"][0]["score"] >= 0.8


def test_assistant_returns_clarification_for_ambiguous_question_without_chat(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_if_called(*_args: Any, **_kwargs: Any) -> ChatCompletionResult:
        raise AssertionError("clarification must not call chat generation")

    monkeypatch.setattr(BailianGateway, "chat_completion", fail_if_called)
    headers = _login_headers(client)

    response = client.post(
        "/api/assistant/ask",
        headers=headers,
        json={"question": "这个超过了怎么办", "scene": "debug"},
    )

    assert response.status_code == 200
    answer = response.json()["data"]["answer"]
    assert answer["answer_type"] == "clarification"
    assert answer["missing_fields"]
    assert answer["references"] == []


def test_assistant_generates_answer_from_document_references(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorder = ChatRecorder("请先核对支付渠道流水，再人工补单或按原路径退款。")
    monkeypatch.setattr(BailianGateway, "chat_completion", recorder.chat_completion)
    headers = _login_headers(client)

    response = client.post(
        "/api/assistant/ask",
        headers=headers,
        json={
            "question": "支付后会员未生效且渠道已扣款，客服应该如何人工补单？",
            "scene": "debug",
        },
    )

    assert response.status_code == 200
    answer = response.json()["data"]["answer"]
    assert answer["answer_type"] == "generated"
    assert answer["answer"] == "请先核对支付渠道流水，再人工补单或按原路径退款。"
    assert any(reference["type"] == "document" for reference in answer["references"])
    assert len(recorder.calls) == 1


def test_assistant_uses_only_latest_three_context_messages(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorder = ChatRecorder("已根据最近上下文生成。")
    monkeypatch.setattr(BailianGateway, "chat_completion", recorder.chat_completion)
    headers = _login_headers(client)
    context_messages = [
        {"sender": "customer", "content": "第一条旧上下文，不应进入提示词"},
        {"sender": "employee", "content": "第二条：用户已提供订单号"},
        {"sender": "customer", "content": "第三条：支付宝渠道已扣款"},
        {"sender": "employee", "content": "第四条：准备核对人工补单"},
    ]

    response = client.post(
        "/api/assistant/ask",
        headers=headers,
        json={
            "question": "支付后会员未生效且渠道已扣款，客服应该如何人工补单？",
            "scene": "debug",
            "context_messages": context_messages,
        },
    )

    assert response.status_code == 200
    answer = response.json()["data"]["answer"]
    assert answer["answer_type"] == "generated"
    assert answer["context_messages_used"] == 3
    prompt_text = "\n".join(message.content for message in recorder.calls[0])
    assert "第一条旧上下文" not in prompt_text
    assert "第二条：用户已提供订单号" in prompt_text
    assert "第三条：支付宝渠道已扣款" in prompt_text
    assert "第四条：准备核对人工补单" in prompt_text


def test_assistant_chat_failure_returns_model_unavailable_envelope(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fail_chat(*_args: Any, **_kwargs: Any) -> ChatCompletionResult:
        raise BailianAPIError("upstream failed")

    monkeypatch.setattr(BailianGateway, "chat_completion", fail_chat)
    headers = _login_headers(client)

    response = client.post(
        "/api/assistant/ask",
        headers=headers,
        json={
            "question": "支付后会员未生效且渠道已扣款，客服应该如何人工补单？",
            "scene": "debug",
        },
    )

    assert response.status_code == 500
    assert response.json() == {"code": 500, "message": "模型服务暂时不可用", "data": None}


def test_assistant_requires_login_and_valid_payload(client: TestClient) -> None:
    missing_login = client.post(
        "/api/assistant/ask",
        json={"question": "退款多久到账？", "scene": "debug"},
    )
    assert missing_login.status_code == 401
    assert missing_login.json() == {"code": 401, "message": "登录状态已失效", "data": None}

    headers = _login_headers(client)
    empty_question = client.post(
        "/api/assistant/ask",
        headers=headers,
        json={"question": "   ", "scene": "debug"},
    )
    assert empty_question.status_code == 400
    assert empty_question.json()["message"] == "参数错误"

    invalid_scene = client.post(
        "/api/assistant/ask",
        headers=headers,
        json={"question": "退款多久到账？", "scene": "other"},
    )
    assert invalid_scene.status_code == 400
    assert invalid_scene.json()["message"] == "参数错误"


def _login_headers(client: TestClient) -> dict[str, str]:
    login = client.post(
        "/api/auth/login",
        json={"username": "agent01", "password": "password123"},
    )
    assert login.status_code == 200
    token = str(login.json()["data"]["access_token"])
    return {"Authorization": f"Bearer {token}"}


async def _setup_database(
    test_engine: AsyncEngine,
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await create_fts5_indexes(conn)

    async with session_factory() as session:
        await seed_demo_data(session)

    async with test_engine.begin() as conn:
        await rebuild_fts5_indexes(conn)
