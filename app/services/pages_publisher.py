"""Publish legal/about/contact pages to WordPress via REST API.

Used by the /publish-pages endpoint as a one-off bootstrap. Safe to re-run: it
looks up the page slug and updates instead of creating duplicates.
"""
from pathlib import Path

import httpx
from loguru import logger

from app.config import Settings
from app.services.wp_auth import WPAuth


PAGE_SLUGS = {
    "politica-privacidad": "Politica de Privacidad",
    "terminos-condiciones": "Terminos y Condiciones",
    "sobre-nosotros": "Sobre IA Practica",
    "contacto": "Contacto",
}

PAGES_DIR = Path("wordpress-config/pages")


class PagesPublisher:
    def __init__(self, settings: Settings):
        self.base_url = settings.wp_url.rstrip("/")
        self.api_url = f"{self.base_url}/wp-json/wp/v2"
        self.auth = WPAuth(settings)

    async def publish_all(self) -> dict:
        results = {}
        headers = await self.auth.headers()
        async with httpx.AsyncClient(timeout=30) as client:
            for slug, title in PAGE_SLUGS.items():
                html_path = PAGES_DIR / f"{slug}.html"
                if not html_path.exists():
                    results[slug] = {"status": "skipped", "reason": f"{html_path} not found"}
                    continue

                content = html_path.read_text(encoding="utf-8")
                existing_id = await self._find_page_id(client, slug, headers)

                payload = {
                    "title": title,
                    "slug": slug,
                    "content": content,
                    "status": "publish",
                }

                if existing_id:
                    resp = await client.post(
                        f"{self.api_url}/pages/{existing_id}",
                        json=payload,
                        headers=headers,
                    )
                    action = "updated"
                else:
                    resp = await client.post(
                        f"{self.api_url}/pages",
                        json=payload,
                        headers=headers,
                    )
                    action = "created"

                if resp.status_code in (200, 201):
                    data = resp.json()
                    results[slug] = {
                        "status": action,
                        "id": data.get("id"),
                        "link": data.get("link"),
                    }
                    logger.info(f"Page {action}: {slug} (id={data.get('id')})")
                else:
                    results[slug] = {
                        "status": "failed",
                        "http": resp.status_code,
                        "error": resp.text[:300],
                    }
                    logger.error(f"Page {slug} failed: {resp.status_code} {resp.text[:300]}")

        return results

    async def _find_page_id(self, client: httpx.AsyncClient, slug: str, headers: dict) -> int | None:
        resp = await client.get(
            f"{self.api_url}/pages",
            params={"slug": slug, "status": "publish,draft,future,pending,private"},
            headers=headers,
        )
        if resp.status_code != 200:
            return None
        try:
            items = resp.json()
        except Exception:
            return None
        if isinstance(items, list) and items:
            return items[0].get("id")
        return None
