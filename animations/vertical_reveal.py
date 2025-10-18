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

def add_white_border(image, border_width=10):
    """Add white border around image."""
    h, w = image.shape[:2]
    bordered = cv2.copyMakeBorder(
        image, 
        border_width, border_width, border_width, border_width,
        cv2.BORDER_CONSTANT, 
        value=(255, 255, 255)
    )
    return bordered

def animate_collage_tapestry(user_image, out_path, fps=24):
    """
    Create a 6-second travel tapestry video:
      - 4 copies of user's image arranged in collage style
      - Each with white border
      - Gentle animation (subtle movement/tilt effect)
    """
    bg_img = load_image_from_url(BACKGROUND_URL)
    if bg_img is None:
        raise ValueError("Failed to load background image.")
    
    bg_h, bg_w = bg_img.shape[:2]
    total_duration = 6
    frames = int(fps * total_duration)
    
    # Resize user image (portrait-like aspect)
    img_w, img_h = int(bg_w * 0.25), int(bg_h * 0.35)
    small_img = cv2.resize(user_image, (img_w, img_h))
    
    # Add white border to each copy
    border_width = 8
    bordered_img = add_white_border(small_img, border_width)
    bordered_h, bordered_w = bordered_img.shape[:2]
    
    # Collage positions (top-left, top-right, bottom-left, bottom-right)
    positions = [
        (int(bg_w * 0.08), int(bg_h * 0.08)),    # top-left
        (int(bg_w * 0.60), int(bg_h * 0.05)),    # top-right
        (int(bg_w * 0.05), int(bg_h * 0.55)),    # bottom-left
        (int(bg_w * 0.58), int(bg_h * 0.58)),    # bottom-right
    ]
    
    # Video writer setup
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(out_path, fourcc, fps, (bg_w, bg_h))
    
    for f in range(frames):
        t = f / fps
        frame = bg_img.copy()
        
        for i, (base_x, base_y) in enumerate(positions):
            # Gentle subtle movement (minimal animation)
            offset_x = int(3 * math.sin(t * 1.5 + i * 0.5))
            offset_y = int(2 * math.cos(t * 1.2 + i * 0.7))
            
            img_x = base_x + offset_x
            img_y = base_y + offset_y
            
            # Boundary check
            y2 = min(img_y + bordered_h, bg_h)
            x2 = min(img_x + bordered_w, bg_w)
            
            # Ensure positive coordinates
            if img_x >= 0 and img_y >= 0 and y2 > img_y and x2 > img_x:
                # Blend image with background
                overlay = frame[img_y:y2, img_x:x2]
                blended = cv2.addWeighted(
                    overlay, 0.15, 
                    bordered_img[:y2 - img_y, :x2 - img_x], 0.85, 
                    0
                )
                frame[img_y:y2, img_x:x2] = blended
        
        writer.write(frame)
    
    writer.release()
    print(f"[INFO] Collage video created successfully → {out_path}")
    return get_video_duration(out_path), frames
