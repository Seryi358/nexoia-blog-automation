import json
from datetime import datetime, timezone
from sqlalchemy import select, update
from loguru import logger

from app.config import Settings
from app.database import async_session, Article, ContentPlan
from app.services.content_generator import ContentGenerator
from app.services.image_generator import ImageGenerator
from app.services.wordpress_client import WordPressClient
from app.services.seo_optimizer import get_related_articles


async def publish_next_article(settings: Settings) -> dict | None:
    """Pick the next topic from the content plan, generate an article, and publish it."""
    logger.info("=== Starting scheduled article publication ===")

    # 1. Get next unpublished topic from content plan
    async with async_session() as session:
        stmt = (
            select(ContentPlan)
            .where(ContentPlan.used.is_(False))
            .order_by(ContentPlan.priority.asc(), ContentPlan.id.asc())
            .limit(1)
        )
        result = await session.execute(stmt)
        topic_row = result.scalar_one_or_none()

    if not topic_row:
        logger.warning("No more topics in content plan! Add more topics.")
        return None

    topic = topic_row.topic
    focus_kw = topic_row.focus_keyword
    secondary_kws = json.loads(topic_row.secondary_keywords) if topic_row.secondary_keywords else []
    category = topic_row.category
    cluster = topic_row.cluster

    logger.info(f"Selected topic: {topic} | KW: {focus_kw}")

    # 2. Get related articles for internal linking
    related = await get_related_articles(category)

    # 3. Generate article content
    generator = ContentGenerator(settings)
    article = await generator.generate_article(
        topic=topic,
        focus_keyword=focus_kw,
        secondary_keywords=secondary_kws,
        category=category,
        cluster=cluster,
        existing_articles=related,
    )

    # 4. Generate featured image
    img_gen = ImageGenerator(settings)
    image_url = await img_gen.generate_featured_image(topic, category)

    # 5. Publish to WordPress
    wp = WordPressClient(settings)
    result = await wp.publish_article(article, featured_image_url=image_url)

    # 6. Record in database
    async with async_session() as session:
        # Mark topic as used
        await session.execute(
            update(ContentPlan)
            .where(ContentPlan.id == topic_row.id)
            .values(used=True)
        )

        # Save article record
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
    }
