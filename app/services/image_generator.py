import asyncio
import hashlib
import json

import httpx
from loguru import logger

from app.config import Settings
from app.prompts.image_prompt import STYLE_VARIANTS, build_image_prompt


# Map article category -> concrete visual ideas the image model can interpret.
VISUAL_ELEMENTS_MAP = {
    "herramientas-ia": "abstract gears, interconnected UI panels, floating dashboards, productivity workflow icons",
    "ia-negocios": "line charts rising, automation nodes, geometric office props, growth arrows, data dashboards",
    "tutoriales-ia": "stepped paths, stacked cards, arrow indicators, layered documentation visuals, step icons",
    "ia-creadores": "painter palette fused with circuit board, creative tools floating, camera aperture, sound waves",
    "noticias-ia": "newspaper layers, timeline markers, bar-chart fragments, glowing data points, future cityscape silhouette",
}


class ImageGenerator:
    """Wrapper over KIE AI Nano Banana 2 image generation."""

    def __init__(self, settings: Settings):
        self.api_key = settings.kie_api_key
        self.base_url = settings.kie_base_url.rstrip("/")
        self.model = getattr(settings, "kie_image_model", "nano-banana-2")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_featured_image(
        self, topic: str, category: str
    ) -> str | None:
        visual_elements = VISUAL_ELEMENTS_MAP.get(
            category, "technology, AI, digital innovation, abstract network connections"
        )
        style_key = self._pick_style(topic)
        prompt = build_image_prompt(topic, visual_elements, style_key=style_key)

        body = {
            "model": self.model,
            "input": {
                "prompt": prompt,
                "aspect_ratio": "16:9",
                "resolution": "2K",
                "output_format": "jpg",
            },
        }

        logger.info(
            f"KIE image request | model={self.model} | style={style_key} | topic='{topic[:70]}'"
        )

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.base_url}/jobs/createTask",
                    json=body,
                    headers=self.headers,
                )
                if resp.status_code >= 400:
                    logger.error(
                        f"KIE AI createTask failed {resp.status_code}: {resp.text[:500]}"
                    )
                    return None

                payload = resp.json()
                task_id = (payload.get("data") or {}).get("taskId")
                if not task_id:
                    logger.error(f"KIE AI createTask response without taskId: {payload}")
                    return None

                logger.info(f"KIE image task created: {task_id}")

                # Poll for completion (up to ~3 minutes).
                for attempt in range(36):
                    await asyncio.sleep(5)
                    status_resp = await client.get(
                        f"{self.base_url}/jobs/recordInfo",
                        params={"taskId": task_id},
                        headers=self.headers,
                    )
                    if status_resp.status_code >= 400:
                        logger.warning(
                            f"recordInfo {status_resp.status_code}: {status_resp.text[:200]}"
                        )
                        continue

                    data = (status_resp.json() or {}).get("data") or {}
                    state = str(data.get("state", "unknown")).lower()

                    if state in ("completed", "success", "finished"):
                        url = self._extract_url(data)
                        if url:
                            logger.info(f"Image ready ({attempt+1} polls): {url}")
                            return url
                        logger.warning("Image task completed but no URL in response")
                        return None

                    if state in ("failed", "error"):
                        logger.error(
                            f"Image generation failed for topic '{topic}': {data}"
                        )
                        return None

                logger.warning(f"Image generation timeout for topic: {topic}")
                return None

        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return None

    @staticmethod
    def _extract_url(data: dict) -> str | None:
        """KIE returns URLs either as resultJson string or as a list. Handle both."""
        rj = data.get("resultJson")
        if rj:
            try:
                parsed = json.loads(rj) if isinstance(rj, str) else rj
                urls = parsed.get("resultUrls") if isinstance(parsed, dict) else None
                if urls:
                    return urls[0]
            except (json.JSONDecodeError, AttributeError):
                pass

        direct_urls = data.get("resultUrls") or data.get("urls")
        if isinstance(direct_urls, list) and direct_urls:
            return direct_urls[0]

        return None

    @staticmethod
    def _pick_style(topic: str) -> str:
        keys = list(STYLE_VARIANTS.keys())
        seed = hashlib.md5(topic.encode("utf-8")).hexdigest()
        return keys[int(seed[:8], 16) % len(keys)]
