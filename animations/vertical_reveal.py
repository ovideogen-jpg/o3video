import cv2
import numpy as np
import requests
import math
from .utils import get_video_duration

# ✅ Background image (fixed)
BACKGROUND_URL = "https://res.cloudinary.com/dvsubaggj/image/upload/v1760535077/qftfyjnaghpu2b57rj6q.jpg"

def load_image_from_url(url):
    """Download image from URL and return OpenCV image."""
    try:
        resp = requests.get(url, timeout=10)
        arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"[ERROR] Could not load image: {e}")
        return None


def animate_reveal_vertical_multi(user_image, out_path, fps=24):
    """
    Create a 6-second video:
      - 4 copies of the user's image at different corners
      - Each moves gently with a 'hilne' animation
    """
    bg_img = load_image_from_url(BACKGROUND_URL)
    if bg_img is None:
        raise ValueError("Failed to load background image.")

    bg_h, bg_w = bg_img.shape[:2]
    total_duration = 6
    frames = int(fps * total_duration)

    # Resize user image (balanced size)
    small_img = cv2.resize(user_image, (bg_w // 3, bg_h // 3))

    # 4 placement positions (corners)
    positions = [
        (int(bg_w * 0.05), int(bg_h * 0.05)),   # top-left
        (int(bg_w * 0.60), int(bg_h * 0.05)),   # top-right
        (int(bg_w * 0.05), int(bg_h * 0.60)),   # bottom-left
        (int(bg_w * 0.60), int(bg_h * 0.60)),   # bottom-right
    ]

    # Video writer setup
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (bg_w, bg_h))

    for f in range(frames):
        t = f / fps
        frame = bg_img.copy()

        for i, (x, y) in enumerate(positions):
            # Gentle oscillation (hilna)
            offset_x = int(6 * math.sin(t * 2 + i))
            offset_y = int(6 * math.cos(t * 2 + i * 0.7))

            img_x = x + offset_x
            img_y = y + offset_y

            h, w = small_img.shape[:2]
            y2 = min(img_y + h, bg_h)
            x2 = min(img_x + w, bg_w)

            # Blend image with background
            overlay = frame[img_y:y2, img_x:x2]
            blended = cv2.addWeighted(overlay, 0.2, small_img[:y2 - img_y, :x2 - img_x], 0.8, 0)
            frame[img_y:y2, img_x:x2] = blended

        writer.write(frame)

    writer.release()
    print(f"[INFO] Video created successfully → {out_path}")
    return get_video_duration(out_path), frames
