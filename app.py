import cv2
import numpy as np
import aiohttp
import os
import uuid
import asyncio
from fastapi import FastAPI, Query, Request, Response
from fastapi.staticfiles import StaticFiles
import uvicorn

# ✅ Import animation functions
from animations.reveal_zoomout import animate_reveal_zoomout
from animations.rotate_zoomin import animate_rotate_zoomin
from animations.center_reveal_zoomout import animate_center_reveal_zoomout
from animations.blur_zooming_roatation import animate_smooth_zoom_pan
from animations.reveal_vertical import animate_reveal_vertical_zoomout
from animations.blur_reveal6 import animate_blur_reveal
from animations.slide_left_zoom_out7 import animate_slide_left_zoom_out7

from animations.utils import fix_mp4

# ✅ FastAPI app
app = FastAPI(
    title="Image Animation API 🎞️",
    description="Generate animated videos from images using various cinematic effects.",
    version="2.0.0"
)

# ✅ Static serve for outputs folder
OUTDIR = "outputs"
os.makedirs(OUTDIR, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=OUTDIR), name="outputs")


# ---- Handle Render health check ----
@app.head("/")
async def head_check():
    """Handle Render HEAD request for health checks"""
    return Response(status_code=200)


# ---- Root endpoint ----
@app.get("/")
async def home():
    """Root endpoint listing available animation types."""
    return {
        "message": "🎬 Animation API running successfully!",
        "available_animations": [
            "reveal_zoomout",
            "rotate_zoomin",
            "center_reveal_zoomout",
            "smooth_zoom_pan",
            "reveal_vertical_zoomout",
            "blur_reveal",
            "slide_left_zoom_out7"
        ],
        "example_request": "/process?image_url=https://yourimage.jpg&animation=slide_left_zoom_out7"
    }


# ---- Helper: download image ----
async def fetch_image(url: str):
    """Download image from a public URL and return as OpenCV array."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=30) as resp:
                if resp.status != 200:
                    print(f"[ERROR] Invalid image URL: {url}")
                    return None
                data = await resp.read()
                nparr = np.frombuffer(data, np.uint8)
                return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"[ERROR] fetch_image failed: {e}")
        return None


# ---- Helper: run animation synchronously ----
def run_animation_sync(img, out_path, animation):
    """Run animation synchronously (CPU-bound)"""
    try:
        if animation == "reveal_zoomout":
            duration, frames = animate_reveal_zoomout(img, out_path)
        elif animation == "rotate_zoomin":
            duration, frames = animate_rotate_zoomin(img, out_path)
        elif animation == "center_reveal_zoomout":
            duration, frames = animate_center_reveal_zoomout(img, out_path)
        elif animation == "smooth_zoom_pan":
            duration, frames = animate_smooth_zoom_pan(img, out_path)
        elif animation == "reveal_vertical_zoomout":
            duration, frames = animate_reveal_vertical_zoomout(img, out_path)
        elif animation == "blur_reveal":
            duration, frames = animate_blur_reveal(img, out_path)
        elif animation == "slide_left_zoom_out7":
            duration, frames = animate_slide_left_zoom_out7(img, out_path)
        else:
            raise ValueError(f"Invalid animation type: {animation}")

        # ✅ Convert to MP4
        fix_mp4(out_path)
        print(f"[INFO] Animation '{animation}' completed successfully → {out_path}")
        return duration, frames
    except Exception as e:
        print(f"[ERROR] Animation failed: {e}")
        raise


# ---- Main processing endpoint ----
@app.get("/process")
async def process(
    request: Request,
    image_url: str = Query(..., description="Public image URL"),
    animation: str = Query("reveal_zoomout"),
):
    """Download image and apply selected animation (fully synchronous)."""
    img = await fetch_image(image_url)
    if img is None:
        return {"error": "❌ Image download failed or invalid URL"}

    out_path = os.path.join(OUTDIR, f"anim_{uuid.uuid4().hex}.mp4")

    # ✅ Run in background thread (non-blocking for event loop)
    try:
        loop = asyncio.get_event_loop()
        duration, frames = await loop.run_in_executor(
            None, lambda: run_animation_sync(img, out_path, animation)
        )
    except Exception as e:
        return {"error": f"❌ Animation processing failed: {str(e)}"}

    # ✅ Wait until file is actually written
    timeout = 30  # seconds
    for _ in range(timeout):
        if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
            break
        await asyncio.sleep(1)

    if not os.path.exists(out_path):
        return {"error": "⚠️ Video generation failed or file missing."}

    # ✅ Build output URL for the final video
    base_url = str(request.base_url).rstrip("/")
    file_name = os.path.basename(out_path)
    video_url = f"{base_url}/outputs/{file_name}"

    print(f"[SUCCESS] Video ready at: {video_url}")

    return {
        "status": "✅ Success",
        "animation": animation,
        "duration_seconds": duration,
        "frames_written": frames,
        "video_url": video_url,
    }


# ---- Startup event for Render stabilization ----
@app.on_event("startup")
async def startup_event():
    print("🚀 Initializing Animation API...")
    await asyncio.sleep(5)
    print("✅ Startup complete. Ready to process requests.")


# ---- Run the app ----
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=10000, reload=False)
