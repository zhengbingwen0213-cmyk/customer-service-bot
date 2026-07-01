from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.api.deps import get_db
from src.db.models import Base, ConversationMessage
from src.db.schema import create_fts5_indexes
from src.db.seed import seed_demo_data
from src.main import app
from src.services.auth import reset_token_store


def test_ticket_pool_query_filter_and_claim_use_isolated_sqlite(tmp_path: Path) -> None:
    db_path = tmp_path / "ticket_pool_test.db"
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

    try:
        asyncio.run(_setup_database(test_engine, session_factory))
        reset_token_store()
        app.dependency_overrides[get_db] = override_get_db

        with TestClient(app) as client:
            missing_auth = client.get("/api/tickets", params={"scope": "pool"})
            assert missing_auth.status_code == 401
            assert missing_auth.json() == {
                "code": 401,
                "message": "登录状态已失效",
                "data": None,
            }

            headers = _login_headers(client)

            my_tickets = client.get(
                "/api/tickets",
                headers=headers,
                params={"scope": "mine"},
            )
            assert my_tickets.status_code == 200
            my_ticket_data = my_tickets.json()["data"]
            my_ticket_ids = {item["id"] for item in my_ticket_data["items"]}
            assert my_ticket_data["total"] == 4
            assert my_ticket_ids == {"TK-1003", "TK-1004", "TK-1005", "TK-1006"}
            assert "TK-2001" not in my_ticket_ids
            assert all(
                item["assignee_id"] == "user_001"
                and item["status"] in {"processing", "completed"}
                for item in my_ticket_data["items"]
            )

            agent02_headers = _login_headers(client, username="agent02")
            assert agent02_headers["Authorization"] != headers["Authorization"]

            agent01_after_agent02_me = client.get("/api/auth/me", headers=headers)
            assert agent01_after_agent02_me.status_code == 200
            assert agent01_after_agent02_me.json()["data"]["user"]["id"] == "user_001"

            agent01_after_agent02_tickets = client.get(
                "/api/tickets",
                headers=headers,
                params={"scope": "mine"},
            )
            assert agent01_after_agent02_tickets.status_code == 200
            agent01_after_agent02_items = agent01_after_agent02_tickets.json()["data"]["items"]
            assert {item["id"] for item in agent01_after_agent02_items} == {
                "TK-1003",
                "TK-1004",
                "TK-1005",
                "TK-1006",
            }
            assert all(item["assignee_id"] == "user_001" for item in agent01_after_agent02_items)

            agent02_me = client.get("/api/auth/me", headers=agent02_headers)
            assert agent02_me.status_code == 200
            assert agent02_me.json()["data"]["user"]["id"] == "user_002"

            agent02_mine = client.get(
                "/api/tickets",
                headers=agent02_headers,
                params={"scope": "mine"},
            )
            assert agent02_mine.status_code == 200
            agent02_items = agent02_mine.json()["data"]["items"]
            assert [item["id"] for item in agent02_items] == ["TK-2001"]
            assert all(item["assignee_id"] == "user_002" for item in agent02_items)

            processing_tickets = client.get(
                "/api/tickets",
                headers=headers,
                params={"scope": "mine", "status": "processing"},
            )
            assert processing_tickets.status_code == 200
            assert {
                item["id"] for item in processing_tickets.json()["data"]["items"]
            } == {"TK-1003", "TK-1005", "TK-1006"}

            completed_tickets = client.get(
                "/api/tickets",
                headers=headers,
                params={"scope": "mine", "status": "completed"},
            )
            assert completed_tickets.status_code == 200
            assert [item["id"] for item in completed_tickets.json()["data"]["items"]] == [
                "TK-1004"
            ]

            own_detail = client.get("/api/tickets/TK-1005", headers=headers)
            assert own_detail.status_code == 200
            own_detail_ticket = own_detail.json()["data"]["ticket"]
            assert own_detail_ticket["id"] == "TK-1005"
            assert own_detail_ticket["assignee_id"] == "user_001"
            assert own_detail_ticket["customer"] == {
                "id": "customer_001",
                "name": "张三",
                "level": "VIP 会员",
            }

            messages = client.get("/api/tickets/TK-1005/messages", headers=headers)
            assert messages.status_code == 200
            message_items = messages.json()["data"]["items"]
            assert [item["id"] for item in message_items] == [
                "msg_1005_001",
                "msg_1005_002",
                "msg_1005_003",
            ]
            assert [item["sender"] for item in message_items] == ["customer", "bot", "customer"]
            assert all(item["ticket_id"] == "TK-1005" for item in message_items)

            blank_reply = client.post(
                "/api/tickets/TK-1005/messages",
                headers=headers,
                json={"content": "   "},
            )
            assert blank_reply.status_code == 400
            assert blank_reply.json() == {
                "code": 400,
                "message": "回复内容不能为空",
                "data": None,
            }

            sent_reply = client.post(
                "/api/tickets/TK-1005/messages",
                headers=headers,
                json={
                    "content": "您好，已经为您查询到订单状态，请稍后刷新会员权益。",
                    "used_assistant_answer_id": "answer_001",
                },
            )
            assert sent_reply.status_code == 200
            sent_message = sent_reply.json()["data"]["message"]
            assert sent_message["ticket_id"] == "TK-1005"
            assert sent_message["sender"] == "employee"
            assert sent_message["sender_name"] == "客服一组员工"
            assert sent_message["content"] == "您好，已经为您查询到订单状态，请稍后刷新会员权益。"
            assert sent_message["created_at"].endswith("+08:00")
            assert "used_assistant_answer_id" not in sent_message

            persisted_message = asyncio.run(
                _get_conversation_message(session_factory, sent_message["id"])
            )
            assert persisted_message is not None
            assert persisted_message.used_assistant_answer_id == "answer_001"

            messages_after_reply = client.get("/api/tickets/TK-1005/messages", headers=headers)
            assert messages_after_reply.status_code == 200
            assert messages_after_reply.json()["data"]["items"][-1] == sent_message

            cross_employee_messages = client.get("/api/tickets/TK-2001/messages", headers=headers)
            assert cross_employee_messages.status_code == 403
            assert cross_employee_messages.json() == {
                "code": 403,
                "message": "无权查看该工单",
                "data": None,
            }

            completed = client.post(
                "/api/tickets/TK-1005/complete",
                headers=headers,
                json={
                    "employee_id": "user_001",
                    "summary": "已告知客户支付状态延迟原因，并提供处理建议。",
                },
            )
            assert completed.status_code == 200
            completed_ticket = completed.json()["data"]["ticket"]
            assert completed_ticket["id"] == "TK-1005"
            assert completed_ticket["status"] == "completed"
            assert completed_ticket["completed_at"].endswith("+08:00")

            completed_detail = client.get("/api/tickets/TK-1005", headers=headers)
            assert completed_detail.status_code == 200
            completed_detail_ticket = completed_detail.json()["data"]["ticket"]
            assert completed_detail_ticket["status"] == "completed"
            assert completed_detail_ticket["completed_at"] == completed_ticket["completed_at"]

            cross_employee_complete = client.post(
                "/api/tickets/TK-2001/complete",
                headers=headers,
                json={
                    "employee_id": "user_001",
                    "summary": "尝试完成跨账号工单。",
                },
            )
            assert cross_employee_complete.status_code == 403
            assert cross_employee_complete.json() == {
                "code": 403,
                "message": "只能完成当前账号已接取的工单",
                "data": None,
            }

            cross_employee_detail = client.get("/api/tickets/TK-2001", headers=headers)
            assert cross_employee_detail.status_code == 403
            assert cross_employee_detail.json() == {
                "code": 403,
                "message": "无权查看该工单",
                "data": None,
            }

            missing_detail = client.get("/api/tickets/TK-9999", headers=headers)
            assert missing_detail.status_code == 404
            assert missing_detail.json() == {
                "code": 404,
                "message": "工单不存在",
                "data": None,
            }

            invalid_token = client.post(
                "/api/tickets/TK-1001/claim",
                headers={"Authorization": "Bearer invalid-token"},
                json={"employee_id": "user_001"},
            )
            assert invalid_token.status_code == 401
            assert invalid_token.json() == {
                "code": 401,
                "message": "登录状态已失效",
                "data": None,
            }

            first_page = client.get(
                "/api/tickets",
                headers=headers,
                params={"scope": "pool", "status": "open", "page": 1, "page_size": 1},
            )
            assert first_page.status_code == 200
            first_page_data = first_page.json()["data"]
            assert first_page_data["total"] == 2
            assert first_page_data["page"] == 1
            assert first_page_data["page_size"] == 1
            assert len(first_page_data["items"]) == 1
            assert first_page_data["items"][0]["status"] == "open"
            assert first_page_data["items"][0]["assignee_id"] is None

            high_priority = client.get(
                "/api/tickets",
                headers=headers,
                params={"scope": "pool", "status": "open", "priority": "high"},
            )
            assert high_priority.status_code == 200
            assert [item["id"] for item in high_priority.json()["data"]["items"]] == ["TK-1001"]

            keyword = client.get(
                "/api/tickets",
                headers=headers,
                params={"scope": "pool", "keyword": "报表"},
            )
            assert keyword.status_code == 200
            assert [item["id"] for item in keyword.json()["data"]["items"]] == ["TK-1002"]

            invalid_status = client.get(
                "/api/tickets",
                headers=headers,
                params={"scope": "pool", "status": "pending"},
            )
            assert invalid_status.status_code == 400
            assert invalid_status.json() == {
                "code": 400,
                "message": "status 参数不合法",
                "data": None,
            }

            claimed = client.post(
                "/api/tickets/TK-1001/claim",
                headers=headers,
                json={"employee_id": "user_001"},
            )
            assert claimed.status_code == 200
            assert claimed.json()["data"]["ticket"] == {
                "id": "TK-1001",
                "status": "processing",
                "assignee_id": "user_001",
                "assignee_name": "客服一组员工",
                "updated_at": claimed.json()["data"]["ticket"]["updated_at"],
            }

            after_claim = client.get(
                "/api/tickets",
                headers=headers,
                params={"scope": "pool", "status": "open"},
            )
            assert after_claim.status_code == 200
            after_claim_items = after_claim.json()["data"]["items"]
            assert "TK-1001" not in {item["id"] for item in after_claim_items}
            assert after_claim.json()["data"]["total"] == 1

            duplicate_claim = client.post(
                "/api/tickets/TK-1001/claim",
                headers=headers,
                json={"employee_id": "user_001"},
            )
            assert duplicate_claim.status_code == 400
            assert duplicate_claim.json() == {
                "code": 400,
                "message": "工单已被接取",
                "data": None,
            }

            already_processing = client.post(
                "/api/tickets/TK-1005/claim",
                headers=headers,
                json={"employee_id": "user_001"},
            )
            assert already_processing.status_code == 400
            assert already_processing.json() == {
                "code": 400,
                "message": "工单已被接取",
                "data": None,
            }
    finally:
        app.dependency_overrides.pop(get_db, None)
        reset_token_store()
        asyncio.run(test_engine.dispose())


def _login_headers(client: TestClient, username: str = "agent01") -> dict[str, str]:
    login = client.post(
        "/api/auth/login",
        json={"username": username, "password": "password123"},
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


async def _get_conversation_message(
    session_factory: async_sessionmaker[AsyncSession],
    message_id: str,
) -> ConversationMessage | None:
    async with session_factory() as session:
        result = await session.execute(
            select(ConversationMessage).where(ConversationMessage.id == message_id)
        )
        return result.scalar_one_or_none()
