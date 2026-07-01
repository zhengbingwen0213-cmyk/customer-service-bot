"""Assistant orchestration for QA-first retrieval and generated answers."""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.assistant import (
    AssistantAnswer,
    AssistantAskRequest,
    AssistantContextMessage,
    AssistantReference,
)
from src.services.ai_gateway import BailianGateway, BailianGatewayError, ChatMessage
from src.services.retrieval import KnowledgeSearchAdapter, SearchHit

QA_DIRECT_THRESHOLD = 0.8
MAX_CONTEXT_MESSAGES = 3

DOMAIN_KEYWORDS = (
    "支付",
    "退款",
    "会员",
    "发票",
    "登录",
    "订单",
    "支付宝",
    "微信",
    "补单",
    "到账",
)
PAYMENT_KEYWORDS = ("支付", "退款", "支付宝", "微信", "渠道", "到账", "扣款", "超期", "超过")
ORDER_KEYWORDS = ("订单", "补单", "会员", "生效", "购买")
VAGUE_KEYWORDS = ("这个", "那个", "它", "怎么办", "不行", "超期", "超过", "没到账")


class AssistantModelUnavailableError(RuntimeError):
    """Raised when generated answers cannot be produced by the model gateway."""


class AssistantService:
    def __init__(
        self,
        *,
        retrieval: KnowledgeSearchAdapter | None = None,
        gateway: BailianGateway | None = None,
    ) -> None:
        self._retrieval = retrieval or KnowledgeSearchAdapter()
        self._gateway = gateway or BailianGateway()

    async def ask(
        self,
        session: AsyncSession,
        request: AssistantAskRequest,
    ) -> AssistantAnswer:
        question = request.question.strip()
        context_messages = request.context_messages[-MAX_CONTEXT_MESSAGES:]

        qa_hits = await self._retrieval.search_qa(session, question, limit=5)
        best_qa_hit = qa_hits[0] if qa_hits else None
        if best_qa_hit is not None and best_qa_hit.score >= QA_DIRECT_THRESHOLD:
            return AssistantAnswer(
                answer_id=_new_answer_id(),
                answer_type="qa_direct",
                answer=best_qa_hit.snippet,
                confidence=_clamp_score(best_qa_hit.score),
                missing_fields=[],
                references=[_to_reference(best_qa_hit)],
                context_messages_used=len(context_messages),
            )

        clarification = _build_clarification(question, context_messages)
        if clarification is not None:
            answer, missing_fields = clarification
            return AssistantAnswer(
                answer_id=_new_answer_id(),
                answer_type="clarification",
                answer=answer,
                confidence=0.66,
                missing_fields=missing_fields,
                references=[],
                context_messages_used=len(context_messages),
            )

        document_hits = await self._search_documents(session, question)
        references = [_to_reference(hit) for hit in document_hits]
        generated_answer = await self._generate_answer(question, context_messages, document_hits)
        confidence = _clamp_score(max((hit.score for hit in document_hits), default=0.72))
        return AssistantAnswer(
            answer_id=_new_answer_id(),
            answer_type="generated",
            answer=generated_answer,
            confidence=confidence,
            missing_fields=[],
            references=references,
            context_messages_used=len(context_messages),
        )

    async def _search_documents(
        self,
        session: AsyncSession,
        question: str,
    ) -> list[SearchHit]:
        seen: set[tuple[str, str]] = set()
        hits: list[SearchHit] = []
        for query in _document_search_queries(question):
            for hit in await self._retrieval.search_documents(session, query, limit=5):
                key = (hit.reference_type, hit.source_id)
                if key in seen:
                    continue
                seen.add(key)
                hits.append(hit)
            if hits:
                break
        return hits[:5]

    async def _generate_answer(
        self,
        question: str,
        context_messages: list[AssistantContextMessage],
        document_hits: list[SearchHit],
    ) -> str:
        messages = [
            ChatMessage(
                role="system",
                content=(
                    "你是客服知识库问答助手。请只根据给定上下文和引用资料回答，"
                    "无法确认时提示客服继续核实。"
                ),
            ),
            ChatMessage(
                role="user",
                content=_build_generation_prompt(question, context_messages, document_hits),
            ),
        ]
        try:
            result = await self._gateway.chat_completion(messages, temperature=0.2, max_tokens=512)
        except BailianGatewayError as exc:
            raise AssistantModelUnavailableError("模型服务暂时不可用") from exc
        return result.content


def _build_clarification(
    question: str,
    context_messages: list[AssistantContextMessage],
) -> tuple[str, list[str]] | None:
    if not _is_vague_question(question):
        return None

    context_text = " ".join(message.content for message in context_messages)
    if any(keyword in context_text for keyword in DOMAIN_KEYWORDS):
        return None

    missing_fields = _missing_fields_for_question(question)
    return _clarification_text(missing_fields), missing_fields


def _is_vague_question(question: str) -> bool:
    compact = question.strip()
    if not compact:
        return True
    return any(keyword in compact for keyword in VAGUE_KEYWORDS) and not any(
        keyword in compact for keyword in DOMAIN_KEYWORDS
    )


def _missing_fields_for_question(question: str) -> list[str]:
    if any(keyword in question for keyword in ORDER_KEYWORDS):
        return ["订单号"]
    if any(keyword in question for keyword in PAYMENT_KEYWORDS) or "超过" in question:
        return ["支付渠道"]
    return ["业务场景"]


def _clarification_text(missing_fields: list[str]) -> str:
    if "支付渠道" in missing_fields:
        return "请问您是通过哪个渠道支付的？不同渠道的超期处理方式略有不同。"
    if "订单号" in missing_fields:
        return "请提供订单号，我再帮您判断下一步处理方式。"
    return "请补充具体业务场景或客户问题，我再继续检索知识库。"


def _document_search_queries(question: str) -> list[str]:
    queries = [question]
    for keyword in DOMAIN_KEYWORDS:
        if keyword in question and keyword not in queries:
            queries.append(keyword)
    if "扣款" in question and "支付" not in queries:
        queries.append("支付")
    if "生效" in question and "会员" not in queries:
        queries.append("会员")
    return queries


def _build_generation_prompt(
    question: str,
    context_messages: list[AssistantContextMessage],
    document_hits: list[SearchHit],
) -> str:
    context_block = "\n".join(
        f"- {message.sender}: {message.content}" for message in context_messages
    )
    if not context_block:
        context_block = "- 无"

    reference_block = "\n".join(
        f"- [{index}] {hit.title}: {hit.snippet}"
        for index, hit in enumerate(document_hits, start=1)
    )
    if not reference_block:
        reference_block = "- 未检索到可用文档引用"

    return (
        f"员工问题：{question}\n\n"
        f"最近上下文：\n{context_block}\n\n"
        f"引用资料：\n{reference_block}\n\n"
        "请输出一段可直接给客服参考的简洁回答。"
    )


def _to_reference(hit: SearchHit) -> AssistantReference:
    return AssistantReference(
        type=hit.reference_type,
        source_id=hit.source_id,
        title=hit.title,
        snippet=hit.snippet,
        score=_clamp_score(hit.score),
    )


def _new_answer_id() -> str:
    return f"answer_{uuid4().hex[:12]}"


def _clamp_score(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))
