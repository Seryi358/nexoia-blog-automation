"""SEO utilities: internal linking, similar-topic detection, JSON-LD schema."""
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from sqlalchemy import select

from app.database import async_session, Article


_STOPWORDS_ES = {
    "de", "la", "el", "los", "las", "un", "una", "unos", "unas", "y", "o", "u",
    "a", "en", "con", "sin", "para", "por", "que", "del", "al", "lo", "se", "tu",
    "mi", "es", "son", "como", "mas", "menos", "muy", "cuando", "donde", "quien",
    "qué", "cómo", "cuál", "2025", "2026", "2027",
}


async def get_related_articles(category: str, limit: int = 6) -> list[dict]:
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

    return [{"title": a.title, "url": f"/{a.slug}/"} for a in articles]


async def get_recent_posts_for_context(limit: int = 15) -> list[dict]:
    """Fetch latest published posts across all categories as anti-repetition context."""
    async with async_session() as session:
        stmt = (
            select(Article)
            .where(Article.published.is_(True))
            .order_by(Article.published_at.desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        articles = result.scalars().all()

    return [
        {
            "title": a.title,
            "focus_keyword": a.focus_keyword or "",
            "slug": a.slug,
            "outline": a.outline or "",
        }
        for a in articles
    ]


def _normalize_keywords(text: str) -> set[str]:
    text = (text or "").lower()
    text = re.sub(r"[^a-z0-9áéíóúñü\s]", " ", text)
    tokens = [t for t in text.split() if t and t not in _STOPWORDS_ES and len(t) > 2]
    return set(tokens)


def topic_similarity(topic_a: str, topic_b: str) -> float:
    """Jaccard similarity over non-stopword tokens. 0.0 = different, 1.0 = identical."""
    a, b = _normalize_keywords(topic_a), _normalize_keywords(topic_b)
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def is_duplicate_topic(
    candidate_topic: str,
    candidate_kw: str,
    recent_posts: list[dict],
    threshold: float = 0.6,
) -> tuple[bool, str | None]:
    """Check if a candidate topic is too similar to any recent post. Returns (is_dup, offending_title)."""
    candidate_combined = f"{candidate_topic} {candidate_kw}"
    for post in recent_posts:
        against = f"{post.get('title','')} {post.get('focus_keyword','')}"
        if topic_similarity(candidate_combined, against) >= threshold:
            return True, post.get("title")
    return False, None


def build_article_jsonld(
    title: str,
    description: str,
    url: str,
    image_url: str | None,
    published_date: str | None,
    faqs: list[dict] | None = None,
    site_name: str = "IA Practica",
) -> str:
    """Build a combined JSON-LD block with Article schema and FAQPage schema."""
    parsed = urlparse(url)
    origin = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme else ""

    published_iso = published_date or datetime.now(timezone.utc).isoformat()

    article = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": title[:110],
        "description": description,
        "url": url,
        "datePublished": published_iso,
        "dateModified": published_iso,
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "author": {"@type": "Organization", "name": site_name, "url": origin or url},
        "publisher": {
            "@type": "Organization",
            "name": site_name,
            "logo": {
                "@type": "ImageObject",
                "url": f"{origin}/wp-content/uploads/iapractica-logo.png",
            },
        },
    }
    if image_url:
        article["image"] = image_url

    blocks = [json.dumps(article, ensure_ascii=False)]

    if faqs:
        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": (f.get("question") or "")[:300],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": (f.get("answer") or "")[:1500],
                    },
                }
                for f in faqs
                if f.get("question") and f.get("answer")
            ],
        }
        if faq_schema["mainEntity"]:
            blocks.append(json.dumps(faq_schema, ensure_ascii=False))

    return "\n".join(
        f'<script type="application/ld+json">{b}</script>' for b in blocks
    )
