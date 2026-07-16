import os
import numpy as np
import cv2
from PIL import Image, ImageFilter

SRC = "/Users/yamsoffer/Classiq-games/Albert/אלברט.jpeg"
OUT = "/Users/yamsoffer/Classiq-games/assets/geek.png"

img = cv2.imread(SRC)            # BGR
H, W = img.shape[:2]

GC_BGD, GC_FGD, GC_PR_BGD, GC_PR_FGD = 0, 1, 2, 3
mask = np.full((H, W), GC_PR_BGD, np.uint8)
def rect(x0, y0, x1, y1, val):
    mask[max(0,y0):min(H,y1), max(0,x0):min(W,x1)] = val

# Probable-foreground: whole character bounding box
rect(205, 12, 802, 772, GC_PR_FGD)

# Definite background — outer frame + text + the empty zones around the silhouette
rect(0, 0, 190, H, GC_BGD)          # far left
rect(815, 0, W, H, GC_BGD)          # far right
rect(0, 0, W, 8, GC_BGD)            # top
rect(0, 777, W, H, GC_BGD)          # bottom
rect(28, 24, 315, 224, GC_BGD)      # "5. CORPORATE GEEK ..." text
rect(645, 8, 802, 772, GC_BGD)      # whole right column (past the elbow/shoe)
rect(180, 468, 405, 772, GC_BGD)    # lower-left: below laptop, left of legs
rect(180, 8, 350, 285, GC_BGD)      # upper-left: left of head / above laptop

# Definite foreground cores
rect(430, 90, 545, 205, GC_FGD)     # face/head
rect(430, 300, 565, 580, GC_FGD)    # torso + jeans
rect(430, 600, 560, 740, GC_FGD)    # legs
rect(245, 305, 345, 362, GC_FGD)    # laptop
rect(300, 375, 340, 405, GC_FGD)    # holding fingers
rect(360, 385, 430, 435, GC_FGD)    # silver wrist/forearm

bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
cv2.grabCut(img, mask, None, bgd, fgd, 8, cv2.GC_INIT_WITH_MASK)
fg = np.where((mask == GC_FGD) | (mask == GC_PR_FGD), 255, 0).astype(np.uint8)

# Cleanup
k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
fg = cv2.morphologyEx(fg, cv2.MORPH_CLOSE, k, iterations=2)
fg = cv2.morphologyEx(fg, cv2.MORPH_OPEN, k, iterations=1)

# Largest connected component only
n, labels, stats, _ = cv2.connectedComponentsWithStats((fg > 0).astype(np.uint8), 8)
if n > 1:
    biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    fg = np.where(labels == biggest, 255, 0).astype(np.uint8)

alpha = np.asarray(Image.fromarray(fg).filter(ImageFilter.GaussianBlur(0.8)))
rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
out = Image.fromarray(np.dstack([rgb, alpha]))

ys, xs = np.where(fg > 40)
pad = 12
y0, y1 = max(ys.min()-pad, 0), min(ys.max()+pad, H-1)
x0, x1 = max(xs.min()-pad, 0), min(xs.max()+pad, W-1)
out = out.crop((x0, y0, x1+1, y1+1))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
out.save(OUT)
print("saved", OUT, out.size)
