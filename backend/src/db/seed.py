"""Seed data for local SQLite development and frontend integration."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import (
    ConversationMessage,
    Customer,
    CustomerMemory,
    Document,
    DocumentChunk,
    QaItem,
    Ticket,
    User,
    VectorIndex,
)

DEFAULT_EMBEDDING_MODEL = "text-embedding-v4"
DEFAULT_EMBEDDING_DIMENSION = 1024


@dataclass(frozen=True)
class SeedSummary:
    users: int
    customers: int
    tickets: int
    conversation_messages: int
    qa_items: int
    documents: int
    document_chunks: int
    vector_indexes: int
    customer_memories: int


async def seed_demo_data(session: AsyncSession) -> SeedSummary:
    """Upsert deterministic demo data required by the PRD data contract."""

    for entity in _demo_entities():
        await session.merge(entity)

    await session.commit()
    return await collect_table_counts(session)


async def collect_table_counts(session: AsyncSession) -> SeedSummary:
    counts: dict[str, int] = {}
    models: tuple[tuple[str, type[Any]], ...] = (
        ("users", User),
        ("customers", Customer),
        ("tickets", Ticket),
        ("conversation_messages", ConversationMessage),
        ("qa_items", QaItem),
        ("documents", Document),
        ("document_chunks", DocumentChunk),
        ("vector_indexes", VectorIndex),
        ("customer_memories", CustomerMemory),
    )
    for name, model in models:
        result = await session.execute(select(func.count()).select_from(model))
        counts[name] = int(result.scalar_one())

    return SeedSummary(**counts)


def _demo_entities() -> list[object]:
    users = [
        User(
            id="user_001",
            name="客服一组员工",
            username="agent01",
            password_hash="$2b$12$N9/3q3XVkkO8cwXwF3U3iupyjenaQnGilHdSoTVJh8fN.JeQ/Cni.",
            created_at=_dt("2026-05-23T09:00:00+08:00"),
        ),
        User(
            id="user_002",
            name="客服二组员工",
            username="agent02",
            password_hash="$2b$12$N9/3q3XVkkO8cwXwF3U3iupyjenaQnGilHdSoTVJh8fN.JeQ/Cni.",
            created_at=_dt("2026-05-23T09:05:00+08:00"),
        )
    ]
    customers = [
        Customer(
            id="customer_001",
            name="张三",
            level="VIP 会员",
            created_at=_dt("2026-05-23T14:00:00+08:00"),
        ),
        Customer(
            id="customer_101",
            name="张三",
            level="企业客户",
            created_at=_dt("2026-05-23T09:00:00+08:00"),
        ),
        Customer(
            id="customer_102",
            name="李四",
            level="普通客户",
            created_at=_dt("2026-05-23T09:30:00+08:00"),
        ),
        Customer(
            id="customer_103",
            name="赵六",
            level="企业客户",
            created_at=_dt("2026-05-23T14:00:00+08:00"),
        ),
        Customer(
            id="customer_104",
            name="钱七",
            level="企业客户",
            created_at=_dt("2026-05-23T10:00:00+08:00"),
        ),
        Customer(
            id="customer_106",
            name="孙八",
            level="普通客户",
            created_at=_dt("2026-05-23T09:20:00+08:00"),
        ),
        Customer(
            id="customer_201",
            name="周九",
            level="企业客户",
            created_at=_dt("2026-05-23T13:20:00+08:00"),
        ),
    ]
    tickets = [
        Ticket(
            id="TK-1001",
            title="无法登录系统账号",
            description="客户反馈多次输入正确账号密码后仍提示登录失败，需要人工核实账号状态。",
            status="open",
            priority="high",
            assignee_id=None,
            customer_id="customer_101",
            related_order_id="20231024001",
            created_at=_dt("2023-10-24T09:12:33+08:00"),
            updated_at=_dt("2023-10-24T09:12:33+08:00"),
            completed_at=None,
        ),
        Ticket(
            id="TK-1002",
            title="报表数据导出异常",
            description="客户在导出经营报表时页面长时间无响应，下载文件为空。",
            status="open",
            priority="medium",
            assignee_id=None,
            customer_id="customer_102",
            related_order_id="20231024002",
            created_at=_dt("2023-10-24T09:45:10+08:00"),
            updated_at=_dt("2023-10-24T09:45:10+08:00"),
            completed_at=None,
        ),
        Ticket(
            id="TK-1005",
            title="会员支付后未生效",
            description="客户反馈在 APP 内购买年度会员，支付宝已扣款，但账户状态未更新。",
            status="processing",
            priority="high",
            assignee_id="user_001",
            customer_id="customer_001",
            related_order_id="20260523001",
            created_at=_dt("2026-05-23T14:30:00+08:00"),
            updated_at=_dt("2026-05-23T14:35:00+08:00"),
            completed_at=None,
        ),
        Ticket(
            id="TK-1003",
            title="支付回调延迟问题排查",
            description="客户反馈支付回调延迟，当前订单状态与支付渠道状态不一致。",
            status="processing",
            priority="high",
            assignee_id="user_001",
            customer_id="customer_103",
            related_order_id="20231027003",
            created_at=_dt("2023-10-27T14:32:01+08:00"),
            updated_at=_dt("2023-10-27T14:36:00+08:00"),
            completed_at=None,
        ),
        Ticket(
            id="TK-1004",
            title="企业实名认证驳回咨询",
            description="客户提交企业实名认证后被驳回，需要确认驳回原因和补充材料。",
            status="completed",
            priority="medium",
            assignee_id="user_001",
            customer_id="customer_104",
            related_order_id="20231027004",
            created_at=_dt("2023-10-27T10:50:00+08:00"),
            updated_at=_dt("2023-10-27T11:15:44+08:00"),
            completed_at=_dt("2023-10-27T11:15:44+08:00"),
            completion_summary="已根据驳回原因说明需要补充的材料。",
        ),
        Ticket(
            id="TK-1006",
            title="发票开具失败",
            description="客户提交发票开具申请后提示税务系统超时，需要客服跟进处理。",
            status="processing",
            priority="low",
            assignee_id="user_001",
            customer_id="customer_106",
            related_order_id="20231027006",
            created_at=_dt("2023-10-27T09:40:12+08:00"),
            updated_at=_dt("2023-10-27T09:42:00+08:00"),
            completed_at=None,
        ),
        Ticket(
            id="TK-2001",
            title="跨员工账号隔离验证工单",
            description="该工单属于客服二组员工，用于验证我的工单不会返回跨员工数据。",
            status="processing",
            priority="medium",
            assignee_id="user_002",
            customer_id="customer_201",
            related_order_id="20260523099",
            created_at=_dt("2026-05-23T13:30:00+08:00"),
            updated_at=_dt("2026-05-23T13:36:00+08:00"),
            completed_at=None,
        ),
    ]
    messages = [
        ConversationMessage(
            id="msg_1001_001",
            ticket_id="TK-1001",
            sender="customer",
            sender_name="张三",
            content="我多次输入正确账号密码后还是提示登录失败，麻烦帮我看一下。",
            created_at=_dt("2026-05-23T09:15:00+08:00"),
        ),
        ConversationMessage(
            id="msg_1002_001",
            ticket_id="TK-1002",
            sender="customer",
            sender_name="李四",
            content="导出经营报表一直没有响应，最后下载下来的文件也是空的。",
            created_at=_dt("2026-05-23T09:48:00+08:00"),
        ),
        ConversationMessage(
            id="msg_1003_001",
            ticket_id="TK-1003",
            sender="customer",
            sender_name="赵六",
            content="支付渠道已经扣款，但订单状态还是待支付。",
            created_at=_dt("2026-05-23T14:33:00+08:00"),
        ),
        ConversationMessage(
            id="msg_1003_002",
            ticket_id="TK-1003",
            sender="employee",
            sender_name="客服一组员工",
            content="您好，我先核对支付渠道回调和订单状态。",
            created_at=_dt("2026-05-23T14:36:00+08:00"),
        ),
        ConversationMessage(
            id="msg_1005_001",
            ticket_id="TK-1005",
            sender="customer",
            sender_name="张三",
            content="你好，我刚刚购买了年费会员，但是没有生效。",
            created_at=_dt("2026-05-23T14:32:00+08:00"),
        ),
        ConversationMessage(
            id="msg_1005_002",
            ticket_id="TK-1005",
            sender="bot",
            sender_name="系统回复",
            content="您好，系统可能存在网络延迟，请您提供一下订单号。",
            created_at=_dt("2026-05-23T14:33:00+08:00"),
        ),
        ConversationMessage(
            id="msg_1005_003",
            ticket_id="TK-1005",
            sender="customer",
            sender_name="张三",
            content="好的，订单号是 20260523001。你们核实一下，如果不行能退款吗？",
            created_at=_dt("2026-05-23T14:34:00+08:00"),
        ),
    ]
    qa_items = [
        QaItem(
            id="qa_001",
            question="退款多久到账？",
            answer="正常情况下，退款会在 1-3 个工作日内原路退回您的支付账户。",
            status="enabled",
            created_at=_dt("2026-05-23T10:00:00+08:00"),
            updated_at=_dt("2026-05-23T10:00:00+08:00"),
        ),
        QaItem(
            id="qa_002",
            question="支付状态为什么延迟？",
            answer="网络波动或银行结算通道拥堵可能导致短暂延迟，建议 5 分钟后刷新订单状态。",
            status="enabled",
            created_at=_dt("2026-05-23T09:30:00+08:00"),
            updated_at=_dt("2026-05-24T10:15:00+08:00"),
        ),
        QaItem(
            id="qa_003",
            question="会员权益说明",
            answer="会员权益包含专属客服、优先处理和每月权益券，具体以订单页展示为准。",
            status="disabled",
            created_at=_dt("2026-05-23T10:45:00+08:00"),
            updated_at=_dt("2026-05-23T10:45:00+08:00"),
        ),
    ]
    documents = [
        Document(
            id="doc_001",
            name="售后政策及退款流程.pdf",
            status="completed",
            chunk_count=12,
            storage_path="documents/doc_001/售后政策及退款流程.pdf",
            uploaded_by_id="user_001",
            created_at=_dt("2026-05-23T11:00:00+08:00"),
            updated_at=_dt("2026-05-23T11:02:00+08:00"),
        ),
        Document(
            id="doc_002",
            name="会员权益手册.docx",
            status="processing",
            chunk_count=0,
            storage_path="documents/doc_002/会员权益手册.docx",
            uploaded_by_id="user_001",
            created_at=_dt("2026-05-23T15:05:10+08:00"),
            updated_at=_dt("2026-05-23T15:05:10+08:00"),
        ),
        Document(
            id="doc_003",
            name="支付问题处理指南.pdf",
            status="failed",
            chunk_count=0,
            storage_path="documents/doc_003/支付问题处理指南.pdf",
            uploaded_by_id="user_001",
            created_at=_dt("2026-05-23T11:20:05+08:00"),
            updated_at=_dt("2026-05-23T11:20:05+08:00"),
        ),
    ]
    chunks = _document_chunks()
    vectors = [
        *[
            _vector(
                vector_id=f"vec_{qa.id}",
                source_type="qa",
                source_id=qa.id,
                created_at=qa.updated_at,
            )
            for qa in qa_items
        ],
        *[
            _vector(
                vector_id=f"vec_{chunk.id}",
                source_type="document_chunk",
                source_id=chunk.id,
                created_at=chunk.created_at,
            )
            for chunk in chunks
        ],
    ]
    memories = [
        CustomerMemory(
            id="mem_customer_001_payment_context",
            customer_id="customer_001",
            memory_key="recent_payment_context",
            memory_value="客户最近一次咨询涉及支付宝年费会员支付和退款处理。",
            source_ticket_id="TK-1005",
            created_at=_dt("2026-05-23T14:34:00+08:00"),
            updated_at=_dt("2026-05-23T14:34:00+08:00"),
        )
    ]

    return [
        *users,
        *customers,
        *tickets,
        *messages,
        *qa_items,
        *documents,
        *chunks,
        *vectors,
        *memories,
    ]


def _document_chunks() -> list[DocumentChunk]:
    contents = [
        "售后政策及退款流程：用户支付后未生效时，客服需先核对订单号和支付渠道流水。",
        "如渠道已扣款但业务状态未同步，客服可登记流水并发起人工补单。",
        "无法补单时，款项会在 1-3 个工作日内按原支付路径退回。",
        "支付宝、微信等渠道可能存在短时回调延迟，建议用户保留账单截图。",
        "会员权益激活失败时，应优先确认订单状态、用户账号和购买商品类型。",
        "重复扣款场景需核对多笔交易流水，确认后保留有效订单并退回重复款项。",
        "用户要求退款时，客服需说明退款发起时间、到账时间和节假日顺延规则。",
        "已完成退款不可再次发起同一订单的补单，需要用户重新购买会员。",
        "企业客户退款需记录企业名称、联系人和原始支付凭证。",
        "售后处理完成后，客服应在工单中记录处理摘要并标记完成。",
        "涉及支付争议时，优先按渠道流水和业务订单状态进行交叉核验。",
        "文档入库完成后，这些售后政策切片可作为智能回答引用来源。",
    ]
    return [
        DocumentChunk(
            id=f"chunk_doc_001_{index:03d}",
            document_id="doc_001",
            content=content,
            chunk_index=index,
            created_at=_dt("2026-05-23T11:02:00+08:00"),
        )
        for index, content in enumerate(contents, start=1)
    ]


def _vector(
    *,
    vector_id: str,
    source_type: str,
    source_id: str,
    created_at: datetime,
) -> VectorIndex:
    return VectorIndex(
        id=vector_id,
        source_type=source_type,
        source_id=source_id,
        vector_dimension=DEFAULT_EMBEDDING_DIMENSION,
        embedding_model=DEFAULT_EMBEDDING_MODEL,
        created_at=created_at,
    )


def _dt(value: str) -> datetime:
    return datetime.fromisoformat(value)
