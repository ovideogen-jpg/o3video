import cv2
import subprocess
import os

def get_video_duration(out_path):
    cap = cv2.VideoCapture(out_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps_val = cap.get(cv2.CAP_PROP_FPS)
    cap.release()
    duration = total_frames / fps_val if fps_val > 0 else 0
    return duration

def fix_mp4(out_path):
    fixed_path = out_path.replace(".mp4", "_fixed.mp4")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", out_path, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", fixed_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        os.replace(fixed_path, out_path)
        print("[INFO] MP4 re-encoded for browser compatibility")
    except Exception as e:
        print("[ERROR] ffmpeg failed:", e)
