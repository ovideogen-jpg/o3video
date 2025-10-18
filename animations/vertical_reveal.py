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


def animate_reveal_vertical_multi(user_image, out_path, fps=24):
    """
    5-second video:
      • Background image fixed.
      • Same user image placed in 3 positions (top-left, center, bottom-right).
      • Each with vertical reveal animation.
      • Zoom completely removed.
    """
    # ---- Load fixed background ----
    bg_img = load_image_from_url(BACKGROUND_URL)
    if bg_img is None:
        raise ValueError("Failed to load background image.")

    bg_h, bg_w = bg_img.shape[:2]

    # ---- Prepare three scaled user images ----
    small_img = cv2.resize(user_image, (bg_w // 3, bg_h // 3))
    medium_img = cv2.resize(user_image, (bg_w // 2, bg_h // 2))
    large_img = cv2.resize(user_image, (int(bg_w * 0.7), int(bg_h * 0.7)))

    # ---- Output video writer ----
    total_duration = 5  # seconds
    frames = int(fps * total_duration)
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (bg_w, bg_h))

    # ---- Positions for 3 placements ----
    placements = [
        (int(bg_w * 0.05), int(bg_h * 0.05), small_img),   # top-left
        (int((bg_w - medium_img.shape[1]) / 2),
         int((bg_h - medium_img.shape[0]) / 2), medium_img),  # center
        (int(bg_w - large_img.shape[1] - bg_w * 0.05),
         int(bg_h - large_img.shape[0] - bg_h * 0.05), large_img)  # bottom-right
    ]

    # ---- Frame loop ----
    for f in range(frames):
        t = f / frames
        frame = bg_img.copy()

        # Reveal progress (first half = animate in, then hold)
        progress = min(t / 0.5, 1.0)
        eased = progress ** 2

        for (x, y, img) in placements:
            img_h, img_w = img.shape[:2]
            reveal_h = int(img_h * eased)

            revealed = np.zeros_like(img)
            revealed[:reveal_h, :] = img[:reveal_h, :]

            # Overlay revealed portion
            y2 = min(y + img_h, bg_h)
            x2 = min(x + img_w, bg_w)
            roi_y1 = max(0, y)
            roi_x1 = max(0, x)
            roi_y2 = roi_y1 + (y2 - y)
            roi_x2 = roi_x1 + (x2 - x)

            frame[roi_y1:roi_y2, roi_x1:roi_x2] = cv2.addWeighted(
                frame[roi_y1:roi_y2, roi_x1:roi_x2], 0.2,
                revealed[:roi_y2 - roi_y1, :roi_x2 - roi_x1], 0.8, 0
            )

        writer.write(frame)

    writer.release()
    print(f"[INFO] Video created successfully → {out_path}")
    return get_video_duration(out_path), frames
