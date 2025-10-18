import cv2
import numpy as np
from .utils import get_video_duration

def animate_reveal_vertical_zoomout(image, out_path, fps=24):
    height, width = image.shape[:2]
    total_duration = 4  # seconds
    frames = int(fps * total_duration)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (width, height))

    for f in range(frames):
        t = f / frames

        # -----------------------------
        # Phase 1: Vertical Reveal (0 → 0.5)
        # -----------------------------
        if t < 0.5:
            progress = t / 0.5
            eased = progress ** 2  # smooth acceleration
            reveal_h = int(height * eased)

            animated = np.zeros_like(image)
            animated[:reveal_h, :] = image[:reveal_h, :]

        # -----------------------------
        # Phase 2: Zoom Out Beyond Canvas (0.5 → 1.0)
        # -----------------------------
        else:
            progress = (t - 0.5) / 0.5
            eased = (1 - np.cos(progress * np.pi)) / 2
            zoom_factor = np.interp(eased, [0, 1], [1.0, 0.3])  # smaller at end

            new_w = max(1, int(width * zoom_factor))
            new_h = max(1, int(height * zoom_factor))
            zoomed = cv2.resize(image, (new_w, new_h))

            # Move downward as it zooms out
            y_offset = int(height * 0.1 * progress)
            x1 = (width - new_w) // 2
            y1 = (height - new_h) // 2 + y_offset

            canvas = np.zeros_like(image)

            # Clip coordinates to stay inside canvas
            x1_clip, y1_clip = max(0, x1), max(0, y1)
            x2_clip, y2_clip = min(width, x1 + new_w), min(height, y1 + new_h)

            # Compute corresponding source region (safe slicing)
            src_x1 = max(0, -x1)
            src_y1 = max(0, -y1)
            src_x2 = src_x1 + (x2_clip - x1_clip)
            src_y2 = src_y1 + (y2_clip - y1_clip)

            # ✅ Ensure shapes match perfectly
            if (y2_clip > y1_clip) and (x2_clip > x1_clip):
                canvas[y1_clip:y2_clip, x1_clip:x2_clip] = zoomed[src_y1:src_y2, src_x1:src_x2]

            animated = canvas

        writer.write(animated)

    writer.release()
    return get_video_duration(out_path), frames
