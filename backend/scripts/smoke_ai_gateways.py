"""Smoke-test Bailian gateways and SQLite vector-extension status."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.core.config import AppSettings, get_settings  # noqa: E402
from src.services.ai_gateway import BailianGateway, BailianGatewayError, ChatMessage  # noqa: E402
from src.services.retrieval import SQLiteVectorProbe  # noqa: E402


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if Bailian live checks cannot complete.",
    )
    args = parser.parse_args()

    settings = get_settings()
    gateway = BailianGateway(settings)
    live_chat = await _smoke_chat(gateway)
    live_embedding = await _smoke_embedding(gateway)
    _smoke_vector_probe(settings)

    if args.strict and not (live_chat and live_embedding):
        return 1
    return 0


async def _smoke_chat(gateway: BailianGateway) -> bool:
    if not gateway.is_chat_configured():
        print("Bailian chat: fallback")
        print("- reason: required chat configuration fields are not fully configured")
        return False

    try:
        result = await gateway.chat_completion(
            [
                ChatMessage(role="system", content="你是接口连通性测试助手。"),
                ChatMessage(role="user", content="请只回复 ok"),
            ],
            temperature=0,
            max_tokens=8,
        )
    except BailianGatewayError as exc:
        print("Bailian chat: fallback")
        print(f"- error: {exc}")
        return False

    print("Bailian chat: live")
    print(f"- model: {result.model}")
    print(
        "- response_structure: "
        f"content_length={len(result.content)}, usage_keys={list(result.usage)}"
    )
    return True


async def _smoke_embedding(gateway: BailianGateway) -> bool:
    if not gateway.is_embedding_configured():
        print("Bailian embedding: fallback")
        print("- reason: required embedding configuration fields are not fully configured")
        return False

    try:
        result = await gateway.create_embeddings(["退款多久到账？"])
    except BailianGatewayError as exc:
        print("Bailian embedding: fallback")
        print(f"- error: {exc}")
        return False

    print("Bailian embedding: live")
    print(f"- model: {result.model}")
    print(
        "- response_structure: "
        f"items={len(result.embeddings)}, dimensions={result.dimensions}, "
        f"usage_keys={list(result.usage)}"
    )
    return True


def _smoke_vector_probe(settings: AppSettings) -> None:
    result = SQLiteVectorProbe(settings).probe()
    print(f"SQLite vector plugin: {result.status}")
    if result.available:
        print(f"- plugin: {result.plugin_name}")
        print(f"- version: {result.version or 'unknown'}")
    else:
        print("- fallback: FTS5 / LIKE")
        print(f"- reason: {result.reason}")


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
