"""SEO utilities for internal linking and schema markup."""
import json
from sqlalchemy import select
from app.database import async_session, Article


async def get_related_articles(category: str, limit: int = 5) -> list[dict]:
    """Fetch published articles in the same category for internal linking."""
    async with async_session() as session:
        stmt = (
            select(Article)
            .where(Article.published.is_(True), Article.category == category)
            .order_by(Article.published_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        articles = result.scalars().all()

    return [
        {"title": a.title, "url": f"/{a.slug}/"}
        for a in articles
    ]


def build_article_schema(title: str, description: str, url: str, image_url: str, published_date: str) -> str:
    """Generate JSON-LD structured data for an article (FAQ + Article schema)."""
    schema = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title,
        "description": description,
        "url": url,
        "image": image_url,
        "datePublished": published_date,
        "dateModified": published_date,
        "author": {
            "@type": "Organization",
            "name": "NexoIA",
        },
        "publisher": {
            "@type": "Organization",
            "name": "NexoIA",
            "logo": {
                "@type": "ImageObject",
                "url": f"{url.split('/')[0]}//{url.split('/')[2]}/wp-content/uploads/nexoia-logo.png",
            },
        },
    }
    return f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>'
