"""Assistant API DTOs aligned with docs/api-contracts.md."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

AssistantScene = Literal["quick", "ticket", "debug"]
AssistantAnswerType = Literal["qa_direct", "clarification", "generated"]
AssistantReferenceType = Literal["qa", "document"]
AssistantContextSender = Literal["customer", "employee", "bot"]


class AssistantContextMessage(BaseModel):
    sender: AssistantContextSender
    content: str = Field(min_length=1)

    @field_validator("content")
    @classmethod
    def content_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("content must not be blank")
        return stripped


class AssistantAskRequest(BaseModel):
    question: str = Field(min_length=1)
    scene: AssistantScene
    ticket_id: str | None = None
    conversation_id: str | None = None
    context_messages: list[AssistantContextMessage] = Field(default_factory=list)

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question must not be blank")
        return stripped


class AssistantReference(BaseModel):
    type: AssistantReferenceType
    source_id: str
    title: str
    snippet: str
    score: float


class AssistantAnswer(BaseModel):
    answer_id: str
    answer_type: AssistantAnswerType
    answer: str
    confidence: float
    missing_fields: list[str]
    references: list[AssistantReference]
    context_messages_used: int


class AssistantAskResponseData(BaseModel):
    answer: AssistantAnswer
