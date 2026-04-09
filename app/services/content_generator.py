import json
from openai import AsyncOpenAI
from loguru import logger

from app.config import Settings
from app.models import ArticleGenerated
from app.prompts.article_writer import SYSTEM_PROMPT, ARTICLE_PROMPT, INTERNAL_LINKS_TEMPLATE


class ContentGenerator:
    def __init__(self, settings: Settings):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.min_words = settings.min_word_count
        self.max_words = settings.max_word_count

    async def generate_article(
        self,
        topic: str,
        focus_keyword: str,
        secondary_keywords: list[str],
        category: str,
        cluster: str,
        existing_articles: list[dict] | None = None,
    ) -> ArticleGenerated:
        # Build internal links instruction
        internal_links_instruction = ""
        if existing_articles:
            links = "\n".join(
                f'- {a["title"]}: {a["url"]}' for a in existing_articles[:5]
            )
            internal_links_instruction = INTERNAL_LINKS_TEMPLATE.format(links=links)

        prompt = ARTICLE_PROMPT.format(
            topic=topic,
            focus_keyword=focus_keyword,
            secondary_keywords=", ".join(secondary_keywords),
            category=category,
            cluster=cluster,
            min_words=self.min_words,
            max_words=self.max_words,
            internal_links_instruction=internal_links_instruction,
        )

        logger.info(f"Generating article: {topic}")

        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=10000,
            response_format={"type": "json_object"},
        )

        raw = response.choices[0].message.content
        data = json.loads(raw)

        article = ArticleGenerated(
            title=data["title"],
            slug=data["slug"],
            meta_description=data["meta_description"],
            focus_keyword=focus_keyword,
            category=category,
            cluster=cluster,
            content_html=data["content_html"],
            word_count=self._count_words(data["content_html"]),
            tags=data.get("tags", []),
        )

        logger.info(f"Article generated: {article.title} ({article.word_count} words)")
        return article

    @staticmethod
    def _count_words(html: str) -> int:
        import re
        text = re.sub(r"<[^>]+>", " ", html)
        return len(text.split())
