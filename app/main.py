import asyncio
from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI, HTTPException, Response
from loguru import logger
from sqlalchemy import func, select

from app.config import Settings
from app.database import (
    Article,
    ContentPlan,
    async_session,
    dedupe_content_plan,
    init_db,
)
from app.scheduler.jobs import publish_next_article


settings = Settings()

logger.add(
    "data/blog_automation.log",
    rotation="1 day",
    retention="30 days",
    level=settings.log_level,
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
)

scheduler = AsyncIOScheduler(timezone=settings.timezone)

# Prevent overlapping publishes if /publish-now is hammered or a cron tick starts
# while the previous one is still running.
_publish_lock = asyncio.Lock()


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
    if _publish_lock.locked():
        logger.warning("Previous publish still running; skipping this tick")
        return
    async with _publish_lock:
        try:
            result = await publish_next_article(settings)
            if result:
                logger.info(f"Scheduled publish result: {result}")
        except Exception as e:
            logger.exception(f"Scheduled publish failed: {e}")


async def _maybe_autoseed():
    """If the content plan is empty, auto-seed so the first deploy does not stall."""
    if not settings.autoseed_on_startup:
        return
    async with async_session() as session:
        count = await session.scalar(select(func.count(ContentPlan.id)))
    if count and count > 0:
        removed = await dedupe_content_plan()
        if removed:
            logger.info(f"Startup dedupe removed {removed} duplicate plan rows")
        return
    logger.info("Content plan empty - running auto-seed")
    from seed_content_plan import seed as seed_fn
    try:
        inserted = await seed_fn()
        logger.info(f"Auto-seed inserted {inserted} topics")
    except Exception as e:
        logger.error(f"Auto-seed failed: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logger.info("Database initialized")

    await _maybe_autoseed()

    scheduler.add_job(
        _scheduled_publish,
        trigger=_build_cron_trigger(),
        id="publish_article",
        name="Publish next article",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
        misfire_grace_time=600,
    )
    scheduler.start()
    logger.info(
        f"Scheduler started: {settings.publish_days} at "
        f"{settings.publish_hour:02d}:{settings.publish_minute:02d} {settings.timezone}"
    )

    yield

    scheduler.shutdown()
    logger.info("Scheduler stopped")


app = FastAPI(
    title="IA Practica Blog Automation",
    version="2.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    async with async_session() as session:
        total = await session.scalar(select(func.count(Article.id))) or 0
        remaining = await session.scalar(
            select(func.count(ContentPlan.id)).where(ContentPlan.used.is_(False))
        ) or 0
    return {
        "status": "ok",
        "service": "iapractica-blog-automation",
        "version": "2.0.0",
        "scheduler_running": scheduler.running,
        "articles_published": total,
        "topics_remaining": remaining,
    }


@app.get("/stats")
async def stats():
    async with async_session() as session:
        total = await session.scalar(select(func.count(Article.id))) or 0
        published = await session.scalar(
            select(func.count(Article.id)).where(Article.published.is_(True))
        ) or 0
        remaining_topics = await session.scalar(
            select(func.count(ContentPlan.id)).where(ContentPlan.used.is_(False))
        ) or 0
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
        "lock_held": _publish_lock.locked(),
    }


@app.post("/publish-now")
async def publish_now():
    """Manually trigger article generation and publication. Rejected if another publish is in flight."""
    if _publish_lock.locked():
        raise HTTPException(
            status_code=409,
            detail="Another publish is in progress; try again in a few minutes",
        )
    async with _publish_lock:
        result = await publish_next_article(settings)
    if not result:
        raise HTTPException(status_code=404, detail="No topics available in content plan")
    return result


@app.post("/seed")
async def seed_now():
    """Run the content-plan seeder. Idempotent."""
    from seed_content_plan import seed as seed_fn
    inserted = await seed_fn()
    async with async_session() as session:
        total = await session.scalar(select(func.count(ContentPlan.id))) or 0
        remaining = await session.scalar(
            select(func.count(ContentPlan.id)).where(ContentPlan.used.is_(False))
        ) or 0
    return {"inserted": inserted, "total_topics": total, "remaining_topics": remaining}


@app.post("/dedupe")
async def dedupe():
    """Remove duplicate rows in content_plan that existed before the unique index."""
    removed = await dedupe_content_plan()
    return {"removed": removed}


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
            "outline": (a.outline or "")[:200],
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
            {"id": j.id, "name": j.name, "next_run": str(j.next_run_time)}
            for j in jobs
        ],
    }


@app.post("/publish-pages")
async def publish_pages():
    """Publish/update the legal + about + contact pages (AdSense prerequisites)."""
    from app.services.pages_publisher import PagesPublisher
    publisher = PagesPublisher(settings)
    result = await publisher.publish_all()
    return result


@app.get("/ads.txt", response_class=Response)
async def ads_txt():
    """Serve ads.txt so AdSense can verify publisher ownership.

    Sergio: point your WordPress hosting .htaccess or plugin to proxy /ads.txt
    here, OR configure ADSENSE_PUBLISHER_ID in env once your AdSense pub-ID is
    approved.
    """
    pub_id = settings.adsense_publisher_id.strip()
    if not pub_id:
        return Response(
            content="# ads.txt not yet configured. Set ADSENSE_PUBLISHER_ID once your AdSense account is approved.\n",
            media_type="text/plain",
        )
    line = f"google.com, {pub_id}, DIRECT, f08c47fec0942fa0\n"
    return Response(content=line, media_type="text/plain")
