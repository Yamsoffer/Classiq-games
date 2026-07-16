import numpy as np, cv2
from PIL import Image

SRC = "/Users/yamsoffer/Downloads/ChatGPT Image Jul 15, 2026, 12_30_31 PM.png"
img = cv2.imread(SRC)                      # BGR
H, W = img.shape[:2]
print("src", W, H)

def cut(x0, y0, x1, y1, iters=8):
    """GrabCut inside the given rect (a bit of margin as sure-bg)."""
    sub = img[y0:y1, x0:x1]
    h, w = sub.shape[:2]
    mask = np.zeros((h, w), np.uint8)
    m = 14
    rect = (m, m, w - 2*m, h - 2*m)
    bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(sub, mask, rect, bgd, fgd, iters, cv2.GC_INIT_WITH_RECT)
    fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)

    # keep only the largest connected blob (drops stray bg specks)
    n, lbl, stats, _ = cv2.connectedComponentsWithStats(fg, 8)
    if n > 1:
        big = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
        fg = np.where(lbl == big, 255, 0).astype(np.uint8)

    # tidy + soft edge
    fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, np.ones((5,5), np.uint8))
    fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN,  np.ones((3,3), np.uint8))
    fg = cv2.GaussianBlur(fg, (0,0), 1.2)

    bgr = cv2.cvtColor(sub, cv2.COLOR_BGR2RGB)
    rgba = np.dstack([bgr, fg])

    # auto-crop to content
    ys, xs = np.where(fg > 8)
    py, px = 6, 6
    ry0, ry1 = max(0, ys.min()-py), min(h, ys.max()+py)
    rx0, rx1 = max(0, xs.min()-px), min(w, xs.max()+px)
    return Image.fromarray(rgba[ry0:ry1, rx0:rx1], "RGBA")

# Left pose (running / leaping) and right pose (arms-up jump)
leap = cut(70,  40, 770,  980)
air  = cut(770, 40, 1500, 980)
leap.save("/Users/yamsoffer/Classiq-games/Albert/albert-leap.png")
air.save("/Users/yamsoffer/Classiq-games/Albert/albert-air.png")
print("leap", leap.size, "air", air.size)
