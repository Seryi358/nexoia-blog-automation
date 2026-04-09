import base64
import httpx
from loguru import logger

from app.config import Settings
from app.models import ArticleGenerated, PublishResult


# WordPress category name → ID mapping (populated on first use)
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
        self.headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json",
        }

    async def _ensure_category(self, slug: str) -> int:
        if slug in _category_cache:
            return _category_cache[slug]

        name = CATEGORY_MAP.get(slug, slug)

        async with httpx.AsyncClient(timeout=30) as client:
            # Check if category exists
            resp = await client.get(
                f"{self.api_url}/categories",
                params={"slug": slug},
                headers=self.headers,
            )
            cats = resp.json()
            if cats and isinstance(cats, list) and len(cats) > 0:
                _category_cache[slug] = cats[0]["id"]
                return cats[0]["id"]

            # Create category
            resp = await client.post(
                f"{self.api_url}/categories",
                json={"name": name, "slug": slug},
                headers=self.headers,
            )
            if resp.status_code in (200, 201):
                cat_id = resp.json()["id"]
                _category_cache[slug] = cat_id
                return cat_id

            logger.error(f"Failed to create category {slug}: {resp.text}")
            return 1  # Default "Uncategorized"

    async def _ensure_tags(self, tag_names: list[str]) -> list[int]:
        tag_ids = []
        async with httpx.AsyncClient(timeout=30) as client:
            for tag_name in tag_names[:5]:  # Max 5 tags
                # Check existing
                resp = await client.get(
                    f"{self.api_url}/tags",
                    params={"search": tag_name},
                    headers=self.headers,
                )
                tags = resp.json()
                if tags and isinstance(tags, list):
                    for t in tags:
                        if t["name"].lower() == tag_name.lower():
                            tag_ids.append(t["id"])
                            break
                    else:
                        # Create tag
                        resp = await client.post(
                            f"{self.api_url}/tags",
                            json={"name": tag_name},
                            headers=self.headers,
                        )
                        if resp.status_code in (200, 201):
                            tag_ids.append(resp.json()["id"])
        return tag_ids

    async def upload_image_from_url(self, image_url: str, filename: str) -> int | None:
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                # Download image
                img_resp = await client.get(image_url)
                if img_resp.status_code != 200:
                    logger.error(f"Failed to download image: {image_url}")
                    return None

                content_type = img_resp.headers.get("content-type", "image/jpeg")
                ext = "jpg" if "jpeg" in content_type else "png"
                fname = f"{filename}.{ext}"

                # Upload to WordPress media library
                upload_headers = {
                    "Authorization": self.headers["Authorization"],
                    "Content-Disposition": f'attachment; filename="{fname}"',
                    "Content-Type": content_type,
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

                logger.error(f"WP media upload failed: {resp.status_code} {resp.text}")
                return None

        except Exception as e:
            logger.error(f"Image upload error: {e}")
            return None

    async def publish_article(
        self,
        article: ArticleGenerated,
        featured_image_url: str | None = None,
    ) -> PublishResult:
        category_id = await self._ensure_category(article.category)
        tag_ids = await self._ensure_tags(article.tags)

        # Upload featured image if available
        featured_media_id = None
        if featured_image_url:
            featured_media_id = await self.upload_image_from_url(
                featured_image_url, article.slug
            )

        # Build Yoast/RankMath SEO meta via content
        seo_block = (
            f'<!-- wp:rank-math/meta -->'
            f'<!-- /wp:rank-math/meta -->'
        )

        post_data = {
            "title": article.title,
            "slug": article.slug,
            "content": article.content_html + seo_block,
            "status": "publish",
            "categories": [category_id],
            "tags": tag_ids,
            "meta": {
                "rank_math_title": f"{article.title} - NexoIA",
                "rank_math_description": article.meta_description,
                "rank_math_focus_keyword": article.focus_keyword,
            },
            "excerpt": article.meta_description,
        }

        if featured_media_id:
            post_data["featured_media"] = featured_media_id

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{self.api_url}/posts",
                json=post_data,
                headers=self.headers,
            )

            if resp.status_code in (200, 201):
                post = resp.json()
                logger.info(f"Published: {post['link']}")
                return PublishResult(
                    wp_post_id=post["id"],
                    url=post["link"],
                    title=article.title,
                )

            logger.error(f"Publish failed: {resp.status_code} {resp.text}")
            return PublishResult(
                wp_post_id=0,
                url="",
                title=article.title,
                success=False,
            )
