import cv2
import numpy as np
import requests
from .utils import get_video_duration

BACKGROUND_URL = "https://res.cloudinary.com/dvsubaggj/image/upload/v1760535077/qftfyjnaghpu2b57rj6q.jpg"

def load_image_from_url(url):
    try:
        resp = requests.get(url, timeout=10)
        arr = np.asarray(bytearray(resp.content), dtype=np.uint8)
        return cv2.imdecode(arr, cv2.IMREAD_COLOR)
    except Exception as e:
        print(f"[ERROR] Could not load image: {e}")
        return None


def animate_reveal_vertical_multi(user_image, out_path, fps=24):
    """
    Creates a 5-second video that mimics the reference timing:
      0-2s   → top-left reveal
      2-3.5s → center reveal
      3.5-5s → bottom-right reveal
    Each image stays fixed once fully revealed.
    """
    bg_img = load_image_from_url(BACKGROUND_URL)
    if bg_img is None:
        raise ValueError("Failed to load background image.")

    bg_h, bg_w = bg_img.shape[:2]
    total_duration = 5
    frames = int(fps * total_duration)

    # prepare scaled user images
    small_img  = cv2.resize(user_image, (bg_w // 3, bg_h // 3))
    medium_img = cv2.resize(user_image, (bg_w // 2, bg_h // 2))
    large_img  = cv2.resize(user_image, (int(bg_w * 0.7), int(bg_h * 0.7)))

    placements = [
        {"pos": (int(bg_w*0.05), int(bg_h*0.05)), "img": small_img,  "start":0.0, "end":2.0},
        {"pos": (int((bg_w - medium_img.shape[1]) / 2),
                 int((bg_h - medium_img.shape[0]) / 2)),
         "img": medium_img, "start":2.0, "end":3.5},
        {"pos": (int(bg_w - large_img.shape[1] - bg_w*0.05),
                 int(bg_h - large_img.shape[0] - bg_h*0.05)),
         "img": large_img,  "start":3.5, "end":5.0},
    ]

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (bg_w, bg_h))

    for f in range(frames):
        t = f / fps  # current time in seconds
        frame = bg_img.copy()

        for p in placements:
            x, y = p["pos"]
            img = p["img"]
            img_h, img_w = img.shape[:2]

            if t < p["start"]:
                continue  # not yet visible

            # compute reveal progress only during its time window
            if p["start"] <= t < p["end"]:
                phase_t = (t - p["start"]) / (p["end"] - p["start"])
                eased = phase_t ** 2
            else:
                eased = 1.0  # fully revealed after its window

            reveal_h = int(img_h * eased)
            revealed = np.zeros_like(img)
            revealed[:reveal_h, :] = img[:reveal_h, :]

            y2 = min(y + img_h, bg_h)
            x2 = min(x + img_w, bg_w)
            roi_y1, roi_x1 = y, x
            roi_y2, roi_x2 = y2, x2

            frame[roi_y1:roi_y2, roi_x1:roi_x2] = cv2.addWeighted(
                frame[roi_y1:roi_y2, roi_x1:roi_x2], 0.2,
                revealed[:roi_y2 - roi_y1, :roi_x2 - roi_x1], 0.8, 0
            )

        writer.write(frame)

    writer.release()
    print(f"[INFO] Video created successfully → {out_path}")
    return get_video_duration(out_path), frames
