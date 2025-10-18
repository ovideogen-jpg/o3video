import cv2
import numpy as np
import requests
from .utils import get_video_duration

# Background image URL (fixed)
BACKGROUND_URL = "https://res.cloudinary.com/dvsubaggj/image/upload/v1760535077/qftfyjnaghpu2b57rj6q.jpg"

def load_image_from_url(url):
    """Download image from URL and return OpenCV image."""
    try:
        resp = requests.get(url, timeout=10)
        arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"[ERROR] Could not load image: {e}")
        return None


def animate_reveal_vertical_zoomout(user_image, out_path, fps=24):
    """
    Creates a 5-second video:
    - Background image fixed.
    - User image animated with cinematic reveal + zoom-out effect.
    """
    # Load the fixed background
    bg_img = load_image_from_url(BACKGROUND_URL)
    if bg_img is None:
        raise ValueError("Failed to load background image.")

    # Match background and user image sizes
    bg_h, bg_w = bg_img.shape[:2]
    user_image = cv2.resize(user_image, (bg_w, bg_h))

    # Prepare video writer
    total_duration = 5  # seconds
    frames = int(fps * total_duration)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (bg_w, bg_h))

    for f in range(frames):
        t = f / frames

        # ---- Background stays constant ----
        frame = bg_img.copy()

        # ---- User image animation (same as before, zoom + reveal) ----
        if t < 0.5:
            progress = t / 0.5
            eased = progress ** 2
            reveal_h = int(bg_h * eased)
            overlay = np.zeros_like(user_image)
            overlay[:reveal_h, :] = user_image[:reveal_h, :]
        else:
            progress = (t - 0.5) / 0.5
            eased = (1 - np.cos(progress * np.pi)) / 2
            zoom_factor = np.interp(eased, [0, 1], [1.0, 0.4])  # zoom-out
            new_w = max(1, int(bg_w * zoom_factor))
            new_h = max(1, int(bg_h * zoom_factor))
            zoomed = cv2.resize(user_image, (new_w, new_h))

            x1 = (bg_w - new_w) // 2
            y1 = (bg_h - new_h) // 2 + int(bg_h * 0.05 * progress)
            overlay = np.zeros_like(user_image)

            x1_clip, y1_clip = max(0, x1), max(0, y1)
            x2_clip, y2_clip = min(bg_w, x1 + new_w), min(bg_h, y1 + new_h)
            src_x1, src_y1 = max(0, -x1), max(0, -y1)
            src_x2 = src_x1 + (x2_clip - x1_clip)
            src_y2 = src_y1 + (y2_clip - y1_clip)

            if (y2_clip > y1_clip) and (x2_clip > x1_clip):
                overlay[y1_clip:y2_clip, x1_clip:x2_clip] = zoomed[src_y1:src_y2, src_x1:src_x2]

        # ---- Combine overlay (user image) on top of background ----
        alpha = 0.8  # smooth blending
        combined = cv2.addWeighted(frame, 1 - alpha, overlay, alpha, 0)

        writer.write(combined)

    writer.release()
    print(f"[INFO] Video created successfully → {out_path}")
    return get_video_duration(out_path), frames
