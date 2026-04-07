"""
Meshy AI image-to-3D utility.
Submits first product image URL, polls until done, returns GLB URL.
"""
import asyncio
import logging
import os
import httpx
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

_API_KEY    = os.getenv("MESHY_API_KEY", "")          # set in Render env vars
# _API_KEY  = "msy_7GUQtPgkyRtsYQfCXiMx9dzn4XHgH1T22gFS"   # local testing
_HEADERS    = {"Authorization": f"Bearer {_API_KEY}", "Content-Type": "application/json"}
_SUBMIT_URL = "https://api.meshy.ai/openapi/v1/image-to-3d"
_STATUS_URL = "https://api.meshy.ai/openapi/v1/image-to-3d/{task_id}"


async def generate_glb(image_urls: list[str]) -> tuple[str, str]:
    """
    Submits the first image URL to Meshy AI.
    Returns (task_id,) immediately — does NOT poll.
    """
    image_url = image_urls[0]
    logger.info("[Meshy] Submitting image-to-3D task | image=%s", image_url)

    payload = {
        "image_url": image_url,
        "ai_model": "meshy-6",
        "should_texture": True,
        "enable_pbr": True,
    }

    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.post(_SUBMIT_URL, json=payload, headers=_HEADERS, timeout=30)
        logger.info("[Meshy] Submit response | status=%d body=%s", resp.status_code, resp.text[:200])
        resp.raise_for_status()
        task_id = resp.json()["result"]
        logger.info("[Meshy] Task created | task_id=%s", task_id)
        return task_id


async def poll_task(task_id: str) -> dict:
    """Returns current status/progress/glb_url for a task."""
    async with httpx.AsyncClient(follow_redirects=True) as client:
        res = await client.get(_STATUS_URL.format(task_id=task_id), headers=_HEADERS, timeout=15)
        res.raise_for_status()
        data = res.json()
        status   = data.get("status", "")
        progress = data.get("progress", 0)
        glb_url  = data.get("model_urls", {}).get("glb", "") if status == "SUCCEEDED" else ""
        logger.info("[Meshy] Poll | task_id=%s status=%s progress=%s%%", task_id, status, progress)
        return {"status": status, "progress": progress, "glb_url": glb_url}
