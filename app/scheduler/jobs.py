import json
from datetime import datetime, timezone

from loguru import logger
from sqlalchemy import select, update

from app.config import Settings
from app.database import async_session, Article, ContentPlan
from app.services.content_generator import ContentGenerator
from app.services.image_generator import ImageGenerator
from app.services.seo_optimizer import (
    get_recent_posts_for_context,
    get_related_articles,
    is_duplicate_topic,
)
from app.services.wordpress_client import WordPressClient


async def _pick_next_topic(max_attempts: int = 10) -> ContentPlan | None:
    """Pick the next unused topic that is not a near-duplicate of recent posts.

    Scans up to `max_attempts` of the highest-priority unused rows; if they all
    look like duplicates we fall back to the first one to keep the pipeline moving.
    """
    recent = await get_recent_posts_for_context(limit=25)

    async with async_session() as session:
        stmt = (
            select(ContentPlan)
            .where(ContentPlan.used.is_(False))
            .order_by(ContentPlan.priority.asc(), ContentPlan.id.asc())
            .limit(max_attempts)
        )
        result = await session.execute(stmt)
        candidates = list(result.scalars())

    if not candidates:
        return None

    for candidate in candidates:
        is_dup, offender = is_duplicate_topic(
            candidate.topic, candidate.focus_keyword, recent, threshold=0.62
        )
        if not is_dup:
            return candidate
        logger.info(
            f"Skipping candidate '{candidate.topic[:60]}' (too similar to '{offender[:60] if offender else '?'}')"
        )

    logger.warning(
        "All top candidates look duplicated; falling back to highest-priority unused topic."
    )
    return candidates[0]


async def publish_next_article(settings: Settings) -> dict | None:
    """Pick the next topic from the content plan, generate an article, and publish it."""
    logger.info("=== Starting scheduled article publication ===")

    topic_row = await _pick_next_topic()
    if not topic_row:
        logger.warning("No more topics in content plan! Seed more topics via /seed.")
        return None

    topic = topic_row.topic
    focus_kw = topic_row.focus_keyword
    try:
        secondary_kws = json.loads(topic_row.secondary_keywords or "[]")
    except json.JSONDecodeError:
        secondary_kws = []
    category = topic_row.category
    cluster = topic_row.cluster

    logger.info(f"Selected topic: {topic} | KW: {focus_kw}")

    # Context for the model: same-category internal links + recent posts blacklist.
    related = await get_related_articles(category)
    recent = await get_recent_posts_for_context(limit=15)

    generator = ContentGenerator(settings)
    article = await generator.generate_article(
        topic=topic,
        focus_keyword=focus_kw,
        secondary_keywords=secondary_kws,
        category=category,
        cluster=cluster,
        existing_articles=related,
        recent_published=recent,
    )

    img_gen = ImageGenerator(settings)
    image_url = await img_gen.generate_featured_image(topic, category)

    wp = WordPressClient(settings)
    # Ensure the slug we use in DB matches the one WP accepted.
    unique_slug = await wp.resolve_unique_slug(article.slug)
    article.slug = unique_slug

    result = await wp.publish_article(article, featured_image_url=image_url)

    async with async_session() as session:
        await session.execute(
            update(ContentPlan)
            .where(ContentPlan.id == topic_row.id)
            .values(used=True)
        )

        db_article = Article(
            title=article.title,
            slug=article.slug,
            category=category,
            cluster=cluster,
            content_html=article.content_html,
            meta_description=article.meta_description,
            focus_keyword=focus_kw,
            wp_post_id=result.wp_post_id,
            featured_image_url=image_url,
            word_count=article.word_count,
            outline=article.outline,
            published=result.success,
            published_at=datetime.now(timezone.utc) if result.success else None,
        )
        session.add(db_article)
        await session.commit()

    if result.success:
        logger.info(f"SUCCESS: Published '{article.title}' -> {result.url}")
    else:
        logger.error(f"FAILED to publish: {article.title}")

    return {
        "title": article.title,
        "url": result.url,
        "success": result.success,
        "image": image_url,
        "word_count": article.word_count,
        "archetype_hint": article.outline[:120] if article.outline else None,
    }
