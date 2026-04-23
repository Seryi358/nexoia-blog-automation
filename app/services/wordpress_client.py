import base64
import httpx
from loguru import logger

from app.config import Settings
from app.models import ArticleGenerated, PublishResult
from app.services.seo_optimizer import build_article_jsonld


# WordPress category name → ID cache.
_category_cache: dict[str, int] = {}

CATEGORY_MAP = {
    "herramientas-ia": "Herramientas IA",
    "ia-negocios": "IA para Negocios",
    "tutoriales-ia": "Tutoriales IA",
    "ia-creadores": "IA para Creadores",
    "noticias-ia": "Noticias IA",
}


class WordPressClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.wp_url.rstrip("/")
        self.api_url = f"{self.base_url}/wp-json/wp/v2"
        credentials = f"{settings.wp_user}:{settings.wp_app_password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        self.auth_header = f"Basic {encoded}"
        self.headers = {
            "Authorization": self.auth_header,
            "Content-Type": "application/json",
            "User-Agent": "IAPracticaBot/1.0 (+https://iapractica.co)",
        }

    async def _ensure_category(self, slug: str) -> int:
        if slug in _category_cache:
            return _category_cache[slug]

        name = CATEGORY_MAP.get(slug, slug.replace("-", " ").title())

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"{self.api_url}/categories",
                params={"slug": slug},
                headers=self.headers,
            )
            try:
                cats = resp.json()
            except Exception:
                cats = []
            if isinstance(cats, list) and cats:
                _category_cache[slug] = cats[0]["id"]
                return cats[0]["id"]

            resp = await client.post(
                f"{self.api_url}/categories",
                json={"name": name, "slug": slug},
                headers=self.headers,
            )
            if resp.status_code in (200, 201):
                cat_id = resp.json()["id"]
                _category_cache[slug] = cat_id
                return cat_id

            logger.error(f"Failed to create category {slug}: {resp.status_code} {resp.text[:300]}")
            return 1

    async def _ensure_tags(self, tag_names: list[str]) -> list[int]:
        if not tag_names:
            return []
        tag_ids: list[int] = []
        async with httpx.AsyncClient(timeout=30) as client:
            for tag_name in tag_names[:8]:
                try:
                    resp = await client.get(
                        f"{self.api_url}/tags",
                        params={"search": tag_name},
                        headers=self.headers,
                    )
                    tags = resp.json() if resp.status_code == 200 else []
                    matched = None
                    if isinstance(tags, list):
                        for t in tags:
                            if t.get("name", "").lower() == tag_name.lower():
                                matched = t["id"]
                                break
                    if matched:
                        tag_ids.append(matched)
                        continue

                    create_resp = await client.post(
                        f"{self.api_url}/tags",
                        json={"name": tag_name},
                        headers=self.headers,
                    )
                    if create_resp.status_code in (200, 201):
                        tag_ids.append(create_resp.json()["id"])
                except Exception as e:
                    logger.warning(f"Tag '{tag_name}' failed: {e}")
        return tag_ids

    async def slug_exists(self, slug: str) -> bool:
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{self.api_url}/posts",
                    params={"slug": slug, "status": "publish,draft,future,pending,private"},
                    headers=self.headers,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return isinstance(data, list) and len(data) > 0
        except Exception as e:
            logger.warning(f"slug_exists probe failed: {e}")
        return False

    async def resolve_unique_slug(self, desired: str) -> str:
        if not await self.slug_exists(desired):
            return desired
        for i in range(2, 20):
            candidate = f"{desired}-{i}"
            if not await self.slug_exists(candidate):
                return candidate
        return desired  # give up and let WP handle it

    async def upload_image_from_url(self, image_url: str, filename: str) -> int | None:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                img_resp = await client.get(image_url)
                if img_resp.status_code != 200:
                    logger.error(f"Failed to download image {image_url}: {img_resp.status_code}")
                    return None

                content_type = img_resp.headers.get("content-type", "image/jpeg")
                ext = "jpg" if "jpeg" in content_type or "jpg" in content_type else "png"
                fname = f"{filename}.{ext}"

                upload_headers = {
                    "Authorization": self.auth_header,
                    "Content-Disposition": f'attachment; filename="{fname}"',
                    "Content-Type": content_type,
                    "User-Agent": self.headers["User-Agent"],
                }
                resp = await client.post(
                    f"{self.api_url}/media",
                    content=img_resp.content,
                    headers=upload_headers,
                )
                if resp.status_code in (200, 201):
                    media_id = resp.json()["id"]
                    logger.info(f"Image uploaded to WP: media_id={media_id}")
                    return media_id

                logger.error(f"WP media upload failed: {resp.status_code} {resp.text[:300]}")
                return None

        except Exception as e:
            logger.error(f"Image upload error: {e}")
            return None

    async def publish_article(
        self,
        article: ArticleGenerated,
        featured_image_url: str | None = None,
    ) -> PublishResult:
        # Resolve category, tags and a unique slug before composing the payload.
        category_id = await self._ensure_category(article.category)
        tag_ids = await self._ensure_tags(article.tags)
        unique_slug = await self.resolve_unique_slug(article.slug)

        canonical_url = f"{self.base_url}/{unique_slug}/"
        jsonld_block = build_article_jsonld(
            title=article.title,
            description=article.meta_description,
            url=canonical_url,
            image_url=featured_image_url,
            published_date=None,
            faqs=article.faqs_jsonld,
        )

        # Upload featured image.
        featured_media_id = None
        if featured_image_url:
            featured_media_id = await self.upload_image_from_url(
                featured_image_url, unique_slug
            )

        # Schema block goes at the end of the content so WP renders it inside <main>.
        enriched_html = article.content_html + "\n" + jsonld_block

        post_data = {
            "title": article.title,
            "slug": unique_slug,
            "content": enriched_html,
            "status": "publish",
            "categories": [category_id],
            "tags": tag_ids,
            "meta": {
                "rank_math_title": f"{article.title} | IA Practica",
                "rank_math_description": article.meta_description,
                "rank_math_focus_keyword": article.focus_keyword,
            },
            "excerpt": article.meta_description,
        }
        if featured_media_id:
            post_data["featured_media"] = featured_media_id

        async with httpx.AsyncClient(timeout=45) as client:
            resp = await client.post(
                f"{self.api_url}/posts",
                json=post_data,
                headers=self.headers,
            )

            if resp.status_code in (200, 201):
                post = resp.json()
                logger.info(f"Published: {post.get('link')} (id={post.get('id')})")
                return PublishResult(
                    wp_post_id=post["id"],
                    url=post.get("link") or canonical_url,
                    title=article.title,
                )

            logger.error(f"Publish failed: {resp.status_code} {resp.text[:500]}")
            return PublishResult(
                wp_post_id=0,
                url="",
                title=article.title,
                success=False,
            )
