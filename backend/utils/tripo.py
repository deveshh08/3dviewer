"""
TripoAI image-to-3D utility (api.tripo3d.ai v2).
Submits first product image URL, polls until done, returns GLB URL.
"""
import asyncio
import os
import httpx
from dotenv import load_dotenv
load_dotenv()

_API_KEY     = os.getenv("TRIPO_API_KEY", "")
_HEADERS     = {"Authorization": f"Bearer {_API_KEY}", "Content-Type": "application/json"}
_SUBMIT_URL  = "https://api.tripo3d.ai/v2/openapi/task"
_STATUS_URL  = "https://api.tripo3d.ai/v2/openapi/task/{task_id}"


async def generate_glb(image_urls: list[str]) -> tuple[str, str]:
    """
    Submits the first image URL to TripoAI, polls for completion.
    Returns (glb_url, task_id).
    """
    payload = {
        "type": "image_to_model",
        "file": {"type": "url", "url": image_urls[0]},
    }

    async with httpx.AsyncClient(follow_redirects=True) as client:
        resp = await client.post(_SUBMIT_URL, json=payload, headers=_HEADERS, timeout=30)
        resp.raise_for_status()
        body = resp.json()
        task_id = body.get("data", {}).get("task_id")
        if not task_id:
            raise ValueError(f"No task_id in response: {resp.text}")

        # Poll for completion
        while True:
            res = await client.get(
                _STATUS_URL.format(task_id=task_id), headers=_HEADERS, timeout=15
            )
            res.raise_for_status()
            data = res.json().get("data", {})
            status = data.get("status", "")

            if status in ("success", "SUCCESS"):
                glb_url = data["output"]["model"]
                return glb_url, task_id
            elif status in ("failed", "FAILED", "cancelled"):
                raise ValueError(f"TripoAI task {status}: {data}")

            await asyncio.sleep(3)
