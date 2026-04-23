"""Smoke tests that validate pure functions and module imports without external services."""
import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Stub env so pydantic-settings doesn't crash when the app module is imported.
os.environ.setdefault("OPENAI_API_KEY", "test")
os.environ.setdefault("KIE_API_KEY", "test")
os.environ.setdefault("WP_URL", "https://example.test")
os.environ.setdefault("WP_USER", "test")
os.environ.setdefault("WP_APP_PASSWORD", "test")
os.environ.setdefault("AUTOSEED_ON_STARTUP", "false")


def test_imports():
    import app.config  # noqa: F401
    import app.database  # noqa: F401
    import app.models  # noqa: F401
    import app.main  # noqa: F401
    import app.scheduler.jobs  # noqa: F401
    import app.services.content_generator  # noqa: F401
    import app.services.image_generator  # noqa: F401
    import app.services.seo_optimizer  # noqa: F401
    import app.services.wordpress_client  # noqa: F401
    import seed_content_plan  # noqa: F401


def test_slugify():
    from app.services.content_generator import ContentGenerator
    assert ContentGenerator._slugify("Cómo usar IA en 2026!") == "como-usar-ia-en-2026"
    assert ContentGenerator._slugify("España & México") == "espana-mexico"
    assert ContentGenerator._slugify("") == "articulo"


def test_word_count():
    from app.services.content_generator import ContentGenerator
    html = "<h2>Hola</h2><p>Esto es una prueba de conteo.</p>"
    assert ContentGenerator._count_words(html) == 7


def test_topic_similarity():
    from app.services.seo_optimizer import is_duplicate_topic, topic_similarity

    # Near-duplicates should be flagged.
    sim = topic_similarity(
        "Como ganar dinero con IA desde casa en 2026",
        "5 Formas de Ganar Dinero con IA sin Inversion en 2026",
    )
    assert sim > 0.3

    # Totally different topics shouldn't be flagged.
    sim2 = topic_similarity(
        "Midjourney v7 tutorial para crear imagenes",
        "Regulacion de IA en Europa y Latam",
    )
    assert sim2 < 0.2

    recent = [{"title": "Prompts de ChatGPT para emprendedores", "focus_keyword": "prompts chatgpt"}]
    is_dup, offender = is_duplicate_topic(
        "50 Prompts de ChatGPT para Emprendedores 2026",
        "prompts chatgpt emprendedores 2026",
        recent,
        threshold=0.45,
    )
    assert is_dup is True
    assert offender == "Prompts de ChatGPT para emprendedores"


def test_jsonld_builder():
    from app.services.seo_optimizer import build_article_jsonld

    block = build_article_jsonld(
        title="Test",
        description="Test desc",
        url="https://iapractica.co/test/",
        image_url="https://cdn.example/test.jpg",
        published_date="2026-04-22T10:00:00Z",
        faqs=[{"question": "Q1?", "answer": "A1"}],
    )
    assert "Article" in block
    assert "FAQPage" in block
    assert "application/ld+json" in block


def test_affiliate_picker():
    from app.prompts.article_writer import get_affiliate_instruction

    out = get_affiliate_instruction("Tutorial de Cursor AI 2026", cluster="tutoriales")
    assert "Cursor" in out
    out_cluster = get_affiliate_instruction("Estrategia general de IA", cluster="negocios")
    assert "Hostinger" in out_cluster or "ChatGPT" in out_cluster


def test_archetype_rotation_deterministic():
    from app.services.content_generator import ContentGenerator
    from app.prompts.article_writer import ARTICLE_ARCHETYPES

    class _Stub(ContentGenerator):
        def __init__(self):
            pass

    cg = _Stub()
    a1 = cg._pick_archetype("Tema A", "kw a")
    a2 = cg._pick_archetype("Tema A", "kw a")
    assert a1 == a2
    assert a1 in ARTICLE_ARCHETYPES


def test_seed_loads_without_db_errors():
    """Ensure the seed module at least parses and the CONTENT_PLAN is coherent."""
    import seed_content_plan as s
    assert len(s.CONTENT_PLAN) >= 50
    # Every item should have required keys and unique (topic, focus_keyword) composite.
    required = {"topic", "cluster", "category", "focus_keyword", "secondary_keywords", "priority"}
    seen = set()
    for item in s.CONTENT_PLAN:
        assert required.issubset(item.keys()), f"Missing keys in {item}"
        key = (item["topic"], item["focus_keyword"])
        assert key not in seen, f"Duplicate topic/focus_keyword pair: {key}"
        seen.add(key)


def test_unique_constraint_declared():
    """The dedupe story relies on the composite unique constraint on content_plan."""
    from app.database import ContentPlan
    constraints = [
        c for c in ContentPlan.__table__.constraints
        if c.__class__.__name__ == "UniqueConstraint"
    ]
    assert any(
        tuple(col.name for col in c.columns) == ("topic", "focus_keyword")
        for c in constraints
    ), "Composite UNIQUE(topic, focus_keyword) is required for idempotent seeding"
