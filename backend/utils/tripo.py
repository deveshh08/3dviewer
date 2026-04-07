"""
Meshy AI image-to-3D utility.
Submits first product image URL, polls until done, returns GLB URL.
"""
import asyncio
import os
import httpx
from dotenv import load_dotenv
load_dotenv()

_API_KEY    = os.getenv("MESHY_API_KEY", "")
_HEADERS    = {"Authorization": f"Bearer {_API_KEY}", "Content-Type": "application/json"}
_SUBMIT_URL = "https://api.meshy.ai/openapi/v1/image-to-3d"
_STATUS_URL = "https://api.meshy.ai/openapi/v1/image-to-3d/{task_id}"


async def generate_glb(image_urls: list[str]) -> tuple[str, str]:
    """
    Submits the first image URL to Meshy AI, polls for completion.
    Returns (glb_url, task_id).
    """
    payload = {
        "image_url": image_urls[0],
        "ai_model": "meshy-6",
        "should_texture": True,
        "enable_pbr": True,
    }

    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.post(_SUBMIT_URL, json=payload, headers=_HEADERS, timeout=30)
        resp.raise_for_status()
        task_id = resp.json()["result"]

        while True:
            res = await client.get(
                _STATUS_URL.format(task_id=task_id), headers=_HEADERS, timeout=15
            )
            res.raise_for_status()
            data = res.json()
            status = data.get("status", "")

            if status == "SUCCEEDED":
                return data["model_urls"]["glb"], task_id
            elif status == "FAILED":
                raise ValueError(f"Meshy generation failed: {data.get('task_error')}")

            await asyncio.sleep(5)
