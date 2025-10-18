import cv2
import numpy as np
import aiohttp
import os
import uuid
import asyncio
from fastapi import FastAPI, Query, Request, Response
from fastapi.staticfiles import StaticFiles
import uvicorn

# ✅ Import animation + utils
from animations.vertical_reveal import animate_reveal_vertical_zoomout
from animations.utils import fix_mp4, add_audio_to_video

# ✅ FastAPI app
app = FastAPI(
    title="🎬 Image Animation API with Audio",
    description="Generate animated videos from images using cinematic effects and custom audio.",
    version="2.1.0"
)

# ✅ Output folder setup
OUTDIR = "outputs"
os.makedirs(OUTDIR, exist_ok=True)
app.mount("/outputs", StaticFiles(directory=OUTDIR), name="outputs")


# ---- Health check ----
@app.head("/")
async def head_check():
    return Response(status_code=200)


# ---- Root endpoint ----
@app.get("/")
async def home():
    return {
        "message": "🎥 Animation API is running!",
        "available_animations": ["reveal_vertical_zoomout"],
        "example_request": "/process?image_url=https://yourimage.jpg&animation=reveal_vertical_zoomout&audio_url=https://youraudio.aac"
    }


# ---- Helper: Download image ----
async def fetch_image(url: str):
    """Download image from public URL."""
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


# ---- Animation runner ----
def run_animation_sync(img, out_path, animation, audio_url=None):
    """Run animation synchronously and optionally add audio."""
    try:
        if animation == "reveal_vertical_zoomout":
            duration, frames = animate_reveal_vertical_zoomout(img, out_path)
        else:
            raise ValueError(f"Invalid animation type: {animation}")

        # ✅ Re-encode for browser
        fix_mp4(out_path)

        # ✅ Add custom audio (if provided)
        if audio_url:
            out_with_audio = out_path.replace(".mp4", "_audio.mp4")
            added = add_audio_to_video(out_path, audio_url, out_with_audio)
            if added:
                os.replace(out_with_audio, out_path)
                print(f"[INFO] Audio added from {audio_url}")

        print(f"[INFO] Animation '{animation}' completed successfully → {out_path}")
        return duration, frames
    except Exception as e:
        print(f"[ERROR] Animation failed: {e}")
        raise


# ---- Main endpoint ----
@app.get("/process")
async def process(
    request: Request,
    image_url: str = Query(..., description="Public image URL"),
    animation: str = Query("reveal_vertical_zoomout", description="Animation type"),
    audio_url: str = Query(None, description="Optional audio URL (MP3, AAC, etc.)")
):
    """Download image → apply animation → attach custom audio (optional)."""
    img = await fetch_image(image_url)
    if img is None:
        return {"error": "❌ Image download failed or invalid URL"}

    out_path = os.path.join(OUTDIR, f"anim_{uuid.uuid4().hex}.mp4")

    # ✅ Run in background thread
    try:
        loop = asyncio.get_event_loop()
        duration, frames = await loop.run_in_executor(
            None, lambda: run_animation_sync(img, out_path, animation, audio_url)
        )
    except Exception as e:
        return {"error": f"❌ Animation processing failed: {str(e)}"}

    # ✅ Wait for output file
    timeout = 30
    for _ in range(timeout):
        if os.path.exists(out_path) and os.path.getsize(out_path) > 5000:
            break
        await asyncio.sleep(1)

    if not os.path.exists(out_path):
        return {"error": "⚠️ Video generation failed or file missing."}

    base_url = str(request.base_url).rstrip("/")
    video_url = f"{base_url}/outputs/{os.path.basename(out_path)}"

    print(f"[SUCCESS] Video ready at: {video_url}")

    return {
        "status": "✅ Success",
        "animation": animation,
        "audio_attached": bool(audio_url),
        "duration_seconds": duration,
        "frames_written": frames,
        "video_url": video_url,
    }


# ---- Startup Event ----
@app.on_event("startup")
async def startup_event():
    print("🚀 Initializing Animation API...")
    await asyncio.sleep(5)
    print("✅ Ready to process requests.")


# ---- Run locally ----
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=10000, reload=False)
