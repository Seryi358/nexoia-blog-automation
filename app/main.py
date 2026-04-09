import asyncio
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, HTTPException
from loguru import logger

from app.config import Settings
from app.database import init_db, async_session, Article, ContentPlan
from app.scheduler.jobs import publish_next_article
from sqlalchemy import select, func

settings = Settings()

# Configure logging
logger.add(
    "data/blog_automation.log",
    rotation="1 day",
    retention="30 days",
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)

scheduler = AsyncIOScheduler(timezone=settings.timezone)


def _build_cron_trigger() -> CronTrigger:
    """Build cron trigger from settings. Default: Mon/Wed/Fri at 9:00 AM Bogota."""
    day_map = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}
    days = settings.publish_days.split(",")
    day_numbers = [str(day_map.get(d.strip().lower(), 0)) for d in days]
    return CronTrigger(
        day_of_week=",".join(day_numbers),
        hour=settings.publish_hour,
        minute=settings.publish_minute,
        timezone=settings.timezone,
    )


async def _scheduled_publish():
    """Wrapper for the scheduled job."""
    try:
        result = await publish_next_article(settings)
        if result:
            logger.info(f"Scheduled publish result: {result}")
    except Exception as e:
        logger.error(f"Scheduled publish failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    logger.info("Database initialized")

    scheduler.add_job(
        _scheduled_publish,
        trigger=_build_cron_trigger(),
        id="publish_article",
        name="Publish next article",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(f"Scheduler started: {settings.publish_days} at {settings.publish_hour:02d}:{settings.publish_minute:02d} {settings.timezone}")

    yield

    # Shutdown
    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(
    title="NexoIA Blog Automation",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "nexoia-blog-automation",
        "scheduler_running": scheduler.running,
    }


@app.get("/stats")
async def stats():
    async with async_session() as session:
        total = await session.scalar(select(func.count(Article.id)))
        published = await session.scalar(
            select(func.count(Article.id)).where(Article.published.is_(True))
        )
        remaining_topics = await session.scalar(
            select(func.count(ContentPlan.id)).where(ContentPlan.used.is_(False))
        )
        latest = await session.scalar(
            select(Article.title)
            .where(Article.published.is_(True))
            .order_by(Article.published_at.desc())
        )

    jobs = scheduler.get_jobs()
    next_run = str(jobs[0].next_run_time) if jobs else "No jobs scheduled"

    return {
        "total_articles": total,
        "published": published,
        "remaining_topics": remaining_topics,
        "latest_article": latest,
        "next_scheduled": next_run,
    }


@app.post("/publish-now")
async def publish_now():
    """Manually trigger article generation and publication."""
    result = await publish_next_article(settings)
    if not result:
        raise HTTPException(status_code=404, detail="No topics available in content plan")
    return result


@app.get("/articles")
async def list_articles(limit: int = 20):
    async with async_session() as session:
        stmt = (
            select(Article)
            .order_by(Article.created_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        articles = result.scalars().all()

    return [
        {
            "id": a.id,
            "title": a.title,
            "slug": a.slug,
            "category": a.category,
            "published": a.published,
            "published_at": str(a.published_at) if a.published_at else None,
            "wp_post_id": a.wp_post_id,
            "word_count": a.word_count,
        }
        for a in articles
    ]


@app.get("/schedule")
async def get_schedule():
    jobs = scheduler.get_jobs()
    return {
        "publish_days": settings.publish_days,
        "publish_time": f"{settings.publish_hour:02d}:{settings.publish_minute:02d}",
        "timezone": settings.timezone,
        "jobs": [
            {
                "id": j.id,
                "name": j.name,
                "next_run": str(j.next_run_time),
            }
            for j in jobs
        ],
    }
