from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    Boolean,
    Index,
    UniqueConstraint,
    text,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime, timezone
from pathlib import Path


class Base(DeclarativeBase):
    pass


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(500), nullable=False)
    slug = Column(String(500), unique=True, nullable=False)
    category = Column(String(200), nullable=False)
    cluster = Column(String(200), nullable=False)
    content_html = Column(Text, nullable=False)
    meta_description = Column(String(300))
    focus_keyword = Column(String(200), index=True)
    wp_post_id = Column(Integer)
    featured_image_url = Column(String(1000))
    word_count = Column(Integer)
    outline = Column(Text, default="")
    published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ContentPlan(Base):
    __tablename__ = "content_plan"
    __table_args__ = (
        UniqueConstraint("topic", "focus_keyword", name="uq_topic_kw"),
        Index("ix_content_plan_used_priority", "used", "priority"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(500), nullable=False)
    cluster = Column(String(200), nullable=False)
    category = Column(String(200), nullable=False)
    focus_keyword = Column(String(200), nullable=False)
    secondary_keywords = Column(Text)  # JSON list
    priority = Column(Integer, default=5)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


DATA_DIR = Path("data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite+aiosqlite:///{DATA_DIR}/blog_automation.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Create tables and backfill columns introduced after the first deploy."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # SQLite tolerant migrations: add columns that may be missing when an
        # older DB is re-used.
        existing_cols = await conn.exec_driver_sql(
            "PRAGMA table_info(articles);"
        )
        names = {row[1] for row in existing_cols.fetchall()}
        if "outline" not in names:
            await conn.exec_driver_sql(
                "ALTER TABLE articles ADD COLUMN outline TEXT DEFAULT '';"
            )

        # Ensure the uniqueness index exists even on legacy DBs without the
        # UniqueConstraint in the original schema.
        await conn.exec_driver_sql(
            "CREATE UNIQUE INDEX IF NOT EXISTS uq_topic_kw "
            "ON content_plan(topic, focus_keyword);"
        )


async def dedupe_content_plan() -> int:
    """Keep only the lowest-id row per (topic, focus_keyword). Returns rows deleted."""
    async with engine.begin() as conn:
        result = await conn.exec_driver_sql(
            """
            DELETE FROM content_plan
            WHERE id NOT IN (
                SELECT MIN(id) FROM content_plan
                GROUP BY topic, focus_keyword
            );
            """
        )
        return result.rowcount or 0
