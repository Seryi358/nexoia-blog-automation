import json
import asyncio
import httpx
from loguru import logger

from app.config import Settings
from app.prompts.image_prompt import FEATURED_IMAGE_PROMPT


# Map categories to visual elements for image generation
VISUAL_ELEMENTS_MAP = {
    "herramientas-ia": "AI tools, gears, digital interfaces, productivity dashboards",
    "ia-negocios": "business charts, automation flows, office technology, growth arrows",
    "tutoriales-ia": "step-by-step guides, learning paths, code snippets, tutorials",
    "ia-creadores": "creative tools, design elements, content creation, media",
    "noticias-ia": "news feeds, trending graphs, innovation symbols, future tech",
}


class ImageGenerator:
    def __init__(self, settings: Settings):
        self.api_key = settings.kie_api_key
        self.base_url = settings.kie_base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_featured_image(
        self, topic: str, category: str
    ) -> str | None:
        visual_elements = VISUAL_ELEMENTS_MAP.get(
            category, "technology, AI, digital innovation"
        )
        prompt = FEATURED_IMAGE_PROMPT.format(
            topic=topic, visual_elements=visual_elements
        )

        body = {
            "model": "nano-banana-pro",
            "input": {
                "prompt": prompt,
                "aspect_ratio": "16:9",
                "resolution": "2K",
                "output_format": "jpg",
            },
        }

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{self.base_url}/jobs/createTask",
                    json=body,
                    headers=self.headers,
                )
                if resp.status_code >= 400:
                    logger.error(f"KIE AI image creation failed: {resp.status_code}")
                    return None

                task_id = resp.json()["data"]["taskId"]
                logger.info(f"Image task created: {task_id}")

                # Poll for completion (max 3 minutes)
                for _ in range(36):
                    await asyncio.sleep(5)
                    status_resp = await client.get(
                        f"{self.base_url}/jobs/recordInfo",
                        params={"taskId": task_id},
                        headers=self.headers,
                    )
                    data = status_resp.json()["data"]
                    state = data.get("state", "unknown")

                    if state in ("completed", "success"):
                        if data.get("resultJson"):
                            parsed = json.loads(data["resultJson"])
                            urls = parsed.get("resultUrls", [])
                            if urls:
                                logger.info(f"Image ready: {urls[0]}")
                                return urls[0]
                        return None
                    elif state == "failed":
                        logger.error(f"Image generation failed for: {topic}")
                        return None

                logger.warning(f"Image generation timeout for: {topic}")
                return None

        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return None
