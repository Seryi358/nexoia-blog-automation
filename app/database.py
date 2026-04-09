from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime, timezone


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
    focus_keyword = Column(String(200))
    wp_post_id = Column(Integer)
    featured_image_url = Column(String(1000))
    word_count = Column(Integer)
    published = Column(Boolean, default=False)
    published_at = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class ContentPlan(Base):
    __tablename__ = "content_plan"

    id = Column(Integer, primary_key=True, autoincrement=True)
    topic = Column(String(500), nullable=False)
    cluster = Column(String(200), nullable=False)
    category = Column(String(200), nullable=False)
    focus_keyword = Column(String(200), nullable=False)
    secondary_keywords = Column(Text)  # JSON list
    priority = Column(Integer, default=5)
    used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


DATABASE_URL = "sqlite+aiosqlite:///data/blog_automation.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
