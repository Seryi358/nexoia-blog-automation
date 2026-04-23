import hashlib
import json
import re

from openai import AsyncOpenAI
from loguru import logger

from app.config import Settings
from app.models import ArticleGenerated
from app.prompts.article_writer import (
    ARTICLE_ARCHETYPES,
    ARTICLE_PROMPT,
    INTERNAL_LINKS_TEMPLATE,
    SYSTEM_PROMPT,
    format_recent_posts_blacklist,
    get_affiliate_instruction,
)


EXPAND_PROMPT = """El articulo anterior tiene {current} palabras pero el minimo es {min_words}.

Reescribe el HTML ampliandolo a minimo {target} palabras:
- Anade al menos 2 secciones H2 nuevas sobre angulos no cubiertos (implementacion paso a paso, errores comunes, casos de uso sectoriales, comparativa con alternativas).
- Profundiza las secciones existentes con ejemplos, datos concretos y parrafos adicionales.
- Anade 2 FAQs extra al bloque de preguntas frecuentes.
- NO repitas parrafos ni frases textuales del original. Amplia con sustancia nueva.

Devuelve el mismo JSON (misma estructura) con el contenido ampliado. Mantiene title, slug, meta_description y tags. Actualiza content_html, outline, faqs y word_count.

JSON ORIGINAL:
{previous_json}
"""


class ContentGenerator:
    def __init__(self, settings: Settings):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.min_words = settings.min_word_count
        self.max_words = settings.max_word_count
        self.model = getattr(settings, "openai_model", "gpt-4o")

    async def generate_article(
        self,
        topic: str,
        focus_keyword: str,
        secondary_keywords: list[str],
        category: str,
        cluster: str,
        existing_articles: list[dict] | None = None,
        recent_published: list[dict] | None = None,
    ) -> ArticleGenerated:
        archetype_key = self._pick_archetype(topic, focus_keyword)
        archetype_instructions = ARTICLE_ARCHETYPES[archetype_key]

        internal_links_instruction = ""
        if existing_articles:
            links = "\n".join(
                f'- {a["title"]}: {a["url"]}' for a in existing_articles[:6]
            )
            internal_links_instruction = INTERNAL_LINKS_TEMPLATE.format(links=links)

        affiliate_links_instruction = get_affiliate_instruction(topic, cluster)
        blacklist = format_recent_posts_blacklist(recent_published or [])

        prompt = ARTICLE_PROMPT.format(
            topic=topic,
            focus_keyword=focus_keyword,
            secondary_keywords=", ".join(secondary_keywords) if secondary_keywords else "(ninguna adicional)",
            category=category,
            cluster=cluster,
            min_words=self.min_words,
            max_words=self.max_words,
            archetype_name=archetype_key,
            archetype_instructions=archetype_instructions,
            recent_posts_blacklist=blacklist,
            internal_links_instruction=internal_links_instruction,
            affiliate_links_instruction=affiliate_links_instruction,
        )

        logger.info(
            f"Generating [{archetype_key}] article | topic='{topic}' | kw='{focus_keyword}' | cluster={cluster}"
        )

        data = await self._call_openai(prompt)
        article = self._parse(data, focus_keyword, category, cluster)

        # Retry once with expansion if word count came short.
        if article.word_count < self.min_words:
            logger.warning(
                f"Article too short: {article.word_count} < {self.min_words}. Requesting expansion."
            )
            expanded = await self._expand(data, target=self.min_words + 300)
            if expanded:
                expanded_article = self._parse(expanded, focus_keyword, category, cluster)
                if expanded_article.word_count > article.word_count:
                    article = expanded_article

        logger.info(
            f"Generated '{article.title[:80]}' | {article.word_count} words | slug={article.slug}"
        )
        return article

    async def _call_openai(self, user_prompt: str) -> dict:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.75,
            top_p=0.9,
            frequency_penalty=0.3,
            presence_penalty=0.2,
            max_tokens=12000,
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content or "{}"
        return json.loads(raw)

    async def _expand(self, previous: dict, target: int) -> dict | None:
        try:
            resp = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": EXPAND_PROMPT.format(
                            current=self._count_words(previous.get("content_html", "")),
                            min_words=self.min_words,
                            target=target,
                            previous_json=json.dumps(previous, ensure_ascii=False)[:16000],
                        ),
                    },
                ],
                temperature=0.7,
                frequency_penalty=0.4,
                presence_penalty=0.3,
                max_tokens=14000,
                response_format={"type": "json_object"},
            )
            return json.loads(resp.choices[0].message.content or "{}")
        except Exception as e:
            logger.error(f"Expansion step failed: {e}")
            return None

    def _parse(
        self, data: dict, focus_keyword: str, category: str, cluster: str
    ) -> ArticleGenerated:
        title = data.get("title", "").strip() or "Articulo sin titulo"
        raw_slug = data.get("slug") or self._slugify(title)
        slug = self._slugify(raw_slug)

        content_html = data.get("content_html", "") or ""
        meta_description = (data.get("meta_description") or "").strip()[:300]
        outline = (data.get("outline") or "").strip()[:2000]
        tags = data.get("tags") or []
        if not isinstance(tags, list):
            tags = []
        tags = [str(t).strip()[:60] for t in tags if str(t).strip()][:8]

        faqs_raw = data.get("faqs") or []
        faqs = []
        if isinstance(faqs_raw, list):
            for item in faqs_raw[:8]:
                if isinstance(item, dict):
                    q = (item.get("question") or item.get("q") or "").strip()
                    a = (item.get("answer") or item.get("a") or "").strip()
                    if q and a:
                        faqs.append({"question": q, "answer": a})

        word_count = self._count_words(content_html)

        return ArticleGenerated(
            title=title[:200],
            slug=slug[:200],
            meta_description=meta_description,
            focus_keyword=focus_keyword,
            category=category,
            cluster=cluster,
            content_html=content_html,
            word_count=word_count,
            outline=outline,
            faqs_jsonld=faqs,
            tags=tags,
        )

    def _pick_archetype(self, topic: str, focus_keyword: str) -> str:
        """Deterministically rotate archetypes based on topic hash so runs are reproducible."""
        seed = hashlib.md5(f"{topic}|{focus_keyword}".encode("utf-8")).hexdigest()
        idx = int(seed[:8], 16) % len(ARTICLE_ARCHETYPES)
        return list(ARTICLE_ARCHETYPES.keys())[idx]

    @staticmethod
    def _count_words(html: str) -> int:
        text = re.sub(r"<[^>]+>", " ", html or "")
        text = re.sub(r"\s+", " ", text)
        return len(text.split())

    @staticmethod
    def _slugify(value: str) -> str:
        value = (value or "").lower().strip()
        # Strip accents / diacritics
        replacements = (
            ("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"),
            ("ñ", "n"), ("ü", "u"),
        )
        for src, dst in replacements:
            value = value.replace(src, dst)
        value = re.sub(r"[^a-z0-9\s-]", "", value)
        value = re.sub(r"[\s-]+", "-", value).strip("-")
        return value[:180] or "articulo"
