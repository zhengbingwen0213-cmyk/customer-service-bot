"""Initialize the local SQLite database and seed demo data."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy.engine import make_url

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from src.core.config import AppSettings, get_settings  # noqa: E402
from src.db.schema import (  # noqa: E402
    count_document_keyword_matches,
    count_qa_keyword_matches,
    rebuild_fts5_indexes,
)
from src.db.seed import seed_demo_data  # noqa: E402
from src.db.session import close_db, engine, get_db_context, init_db  # noqa: E402

QA_FTS_PROBE_KEYWORD = "退款多久到账"
DOCUMENT_FTS_PROBE_KEYWORD = "售后政策及退款流程"


async def main() -> None:
    settings = get_settings()
    try:
        await init_db()
        async with get_db_context() as session:
            summary = await seed_demo_data(session)

        async with engine.begin() as conn:
            await rebuild_fts5_indexes(conn)
            qa_matches = await count_qa_keyword_matches(conn, QA_FTS_PROBE_KEYWORD)
            document_matches = await count_document_keyword_matches(
                conn,
                DOCUMENT_FTS_PROBE_KEYWORD,
            )

        if qa_matches < 1 and document_matches < 1:
            raise RuntimeError("SQLite FTS5 keyword probe did not return demo data")

        database_path = _sqlite_database_path(settings)
        if not database_path.exists():
            raise RuntimeError(f"SQLite database file was not created: {database_path}")

        _verify_upload_dir(Path(settings.upload_dir))

        print("SQLite database initialized")
        print(f"- database: {database_path}")
        print(f"- upload_dir: {settings.upload_dir}")
        print(f"- seed_counts: {summary}")
        print(f"- qa_fts_matches[{QA_FTS_PROBE_KEYWORD}]: {qa_matches}")
        print(f"- document_fts_matches[{DOCUMENT_FTS_PROBE_KEYWORD}]: {document_matches}")
    finally:
        await close_db()


def _sqlite_database_path(settings: AppSettings) -> Path:
    url = make_url(settings.database_url)
    if not url.drivername.startswith("sqlite"):
        raise RuntimeError("Only SQLite database URLs are supported by this initializer")

    database = url.database
    if not database or database == ":memory:":
        raise RuntimeError("A file-based SQLite database is required")

    return Path(database).expanduser().resolve()


def _verify_upload_dir(upload_dir: Path) -> None:
    upload_dir.mkdir(parents=True, exist_ok=True)
    probe_file = upload_dir / ".__sdd_write_probe.tmp"
    probe_file.write_text("ok", encoding="utf-8")
    if probe_file.read_text(encoding="utf-8") != "ok":
        raise RuntimeError(f"Upload directory write probe failed: {upload_dir}")
    probe_file.unlink()


if __name__ == "__main__":
    asyncio.run(main())
