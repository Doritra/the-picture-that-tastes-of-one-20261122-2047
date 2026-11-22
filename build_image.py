"""Draw one ripe strawberry, macro, glossy, on a dark moody background.

Fully procedural: numpy for gradients/shading, Pillow for drawing.
No external assets, no network. Output: entry.png (1024x1024).
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W = H = 1024
rng = np.random.default_rng(7)

# ---------------------------------------------------------------- background
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
# dark radial backdrop, slightly warm behind the berry
dx = (xx - 512) / 512.0
dy = (yy - 470) / 512.0
r2 = dx * dx + dy * dy
glow = np.exp(-r2 * 2.2)                      # warm halo behind fruit
base = np.zeros((H, W, 3), np.float32)
base[..., 0] = 14 + 46 * glow                  # deep maroon-black
base[..., 1] = 10 + 12 * glow
base[..., 2] = 12 + 16 * glow
# gentle top light falloff
base *= (0.92 + 0.10 * np.exp(-((yy - 120) ** 2) / (2 * 420.0 ** 2)))[..., None]

# ---------------------------------------------------------------- berry body
# Profile: wide shoulders at top, tapering to a soft point at the bottom.
y0, y1 = 285.0, 965.0


def half_width(t):
    t = np.clip(t, 0.0, 1.0)
    w = 358.0 * np.sqrt(np.clip(1.0 - t ** 2.6, 0.0, 1.0)) * (1.0 - 0.12 * t)
    # rounded shoulder cap: narrow smoothly toward the flat-ish top
    cap = np.where(t < 0.10,
                   0.42 + 0.58 * np.sqrt(np.clip(1.0 - (1.0 - t / 0.10) ** 2, 0, 1)),
                   1.0)
    return w * cap


def centre_x(t):
    return 512.0 + 14.0 * np.sin(t * 2.4) - 6.0 * t


t_grid = (yy - y0) / (y1 - y0)
in_y = (yy >= y0) & (yy <= y1)
hw = half_width(np.clip(t_grid, 0, 1))
cx = centre_x(np.clip(t_grid, 0, 1))
body = in_y & (np.abs(xx - cx) <= hw)
# soften the outline a touch
mask = Image.fromarray((body * 255).astype(np.uint8)).filter(
    ImageFilter.GaussianBlur(1.2))
mask_f = np.asarray(mask, np.float32) / 255.0

# distance from outline -> edge darkening (fresnel-like rim)
edge = Image.fromarray((body * 255).astype(np.uint8)).filter(
    ImageFilter.GaussianBlur(26))
edge_f = np.asarray(edge, np.float32) / 255.0
rim = np.clip(edge_f, 0, 1)  # 1 deep inside, 0 outside

# radial light from upper-left (stronger, juicier highlight)
lx, ly = 390.0, 240.0
ld = np.sqrt((xx - lx) ** 2 + (yy - ly) ** 2) / 900.0
light = np.exp(-ld * ld * 2.0)
light = 0.30 + 1.05 * light
# vertical shading: brighter shoulders, darker toward the tip
vert = 1.0 - 0.45 * np.clip(t_grid, 0, 1) ** 1.6
# cool shadow on the right side
side = 0.82 + 0.28 * np.clip((cx - xx) / 360.0, -1, 1)

shade = light * vert * side * (0.45 + 0.55 * rim)
# red palette: highlight salmon -> ripe crimson -> deep wine
hi = np.array([255, 122, 102], np.float32)
mid = np.array([224, 32, 48], np.float32)
lo = np.array([122, 8, 24], np.float32)
s = np.clip(shade, 0, 1.25)[..., None]
berry = np.where(s > 0.62,
                 mid + (hi - mid) * np.clip((s - 0.62) / 0.63, 0, 1),
                 lo + (mid - lo) * np.clip(s / 0.62, 0, 1))
# faint vertical ribbing (real strawberries have subtle ridges)
rib = 1.0 + 0.05 * np.sin((xx - cx) * 0.055) * np.sin(t_grid * 9.0)
berry *= rib[..., None]

img_arr = base * (1 - mask_f[..., None]) + berry * mask_f[..., None]
img = Image.fromarray(np.clip(img_arr, 0, 255).astype(np.uint8), "RGB")
draw = ImageDraw.Draw(img, "RGBA")

# ---------------------------------------------------------------- seeds
# golden achenes in curving rows that follow the body contour
def seed_pos(row_t, frac):
    hw_r = half_width(row_t)
    cx_r = centre_x(row_t)
    x = cx_r + frac * hw_r * 0.92
    y = y0 + row_t * (y1 - y0)
    return x, y

rows = np.arange(0.08, 0.97, 0.075)
for ri, rt in enumerate(rows):
    n = int(5 + 5 * (1 - rt))  # fewer seeds near the tip
    off = 0.5 if ri % 2 else 0.0
    for k in range(n):
        frac = -0.86 + (k + off) * (1.72 / max(n - 1, 1))
        if abs(frac) > 0.90:
            continue
        x, y = seed_pos(rt, frac)
        # seed size shrinks toward the tip, with a little organic jitter
        sc = (1.0 - 0.35 * rt) * float(rng.uniform(0.85, 1.1))
        # tilt follows the contour slope
        tilt = math.degrees(math.atan2(frac * 160, 300))
        w, h = 8.0 * sc, 12.5 * sc
        # soft pit shadow under the seed
        draw.ellipse([x - w, y - h * 0.7 + 3, x + w, y + h * 0.7 + 3],
                     fill=(90, 5, 12, 80))
        # golden seed, deeper and less cartoon-bright
        draw.ellipse([x - w, y - h, x + w, y + h],
                     fill=(228, 172, 62, 255), outline=(140, 88, 18, 255),
                     width=1)
        # tiny highlight dot
        draw.ellipse([x - w * 0.45, y - h * 0.62, x - w * 0.05, y - h * 0.22],
                     fill=(255, 226, 160, 255))

# ---------------------------------------------------------------- calyx leaves
leaf_base = (512, 298)
# back layer: darker, offset angles, slightly longer for depth
for ang_deg, length in [(-115, 165), (-70, 145), (-25, 135),
                        (25, 135), (70, 145), (115, 165)]:
    a = math.radians(ang_deg - 90)
    tip = (leaf_base[0] + length * 1.15 * math.cos(a),
           leaf_base[1] + length * math.sin(a) * 0.9 + 30)
    px, py = -math.sin(a), math.cos(a)
    wdt = 30
    p1 = (leaf_base[0] + px * wdt, leaf_base[1] + py * wdt)
    p2 = (leaf_base[0] - px * wdt, leaf_base[1] - py * wdt)
    mid1 = (leaf_base[0] * 0.45 + tip[0] * 0.55 + px * wdt * 0.9,
            leaf_base[1] * 0.45 + tip[1] * 0.55 + py * wdt * 0.9)
    mid2 = (leaf_base[0] * 0.45 + tip[0] * 0.55 - px * wdt * 0.9,
            leaf_base[1] * 0.45 + tip[1] * 0.55 - py * wdt * 0.9)
    draw.polygon([p1, mid1, tip, mid2, p2], fill=(28, 80, 30, 255))
leaflets = [(-135, 150), (-95, 130), (-50, 115), (0, 105),
            (50, 115), (95, 130), (135, 150)]
for ang_deg, length in leaflets:
    a = math.radians(ang_deg - 90)
    tip = (leaf_base[0] + length * 1.15 * math.cos(a),
           leaf_base[1] + length * math.sin(a) * 0.9 + 26)
    # leaf width perpendicular to its axis
    px, py = -math.sin(a), math.cos(a)
    wdt = 34 + 8 * math.sin(math.radians(ang_deg))
    p1 = (leaf_base[0] + px * wdt, leaf_base[1] + py * wdt)
    p2 = (leaf_base[0] - px * wdt, leaf_base[1] - py * wdt)
    mid1 = (leaf_base[0] * 0.45 + tip[0] * 0.55 + px * wdt * 0.9,
            leaf_base[1] * 0.45 + tip[1] * 0.55 + py * wdt * 0.9)
    mid2 = (leaf_base[0] * 0.45 + tip[0] * 0.55 - px * wdt * 0.9,
            leaf_base[1] * 0.45 + tip[1] * 0.55 - py * wdt * 0.9)
    draw.polygon([p1, mid1, tip, mid2, p2], fill=(38, 102, 38, 255))
    # centre vein, lighter green
    draw.line([leaf_base, tip], fill=(120, 185, 96, 255), width=3)
    # glossy edge on the upper side
    draw.line([p1, mid1], fill=(80, 155, 70, 255), width=2)
# small stem
draw.line([(512, 298), (514, 232)], fill=(62, 118, 50, 255), width=11)
draw.line([(512, 298), (514, 232)], fill=(104, 168, 84, 255), width=4)

# ---------------------------------------------------------------- gloss + drops
gloss = Image.new("RGBA", (W, H), (0, 0, 0, 0))
gd = ImageDraw.Draw(gloss)
gd.ellipse([300, 330, 560, 620], fill=(255, 255, 255, 60))
gd.ellipse([330, 360, 480, 520], fill=(255, 255, 255, 54))
gloss = gloss.filter(ImageFilter.GaussianBlur(22))
img = Image.alpha_composite(img.convert("RGBA"), gloss)
draw = ImageDraw.Draw(img, "RGBA")

# water droplets on the body
drops = [(430, 470, 13), (590, 430, 10), (660, 600, 15), (380, 640, 9),
         (520, 700, 12), (610, 800, 8), (450, 830, 11), (700, 470, 7),
         (350, 520, 8), (560, 560, 6), (480, 880, 9), (640, 700, 7)]
for x, y, r in drops:
    draw.ellipse([x - r, y - r, x + r, y + r],
                 fill=(255, 255, 255, 8), outline=(255, 255, 255, 42),
                 width=1)
    draw.ellipse([x - r * 0.55, y - r * 0.62, x - r * 0.05, y - r * 0.12],
                 fill=(255, 255, 255, 110))
    draw.arc([x - r * 0.8, y - r * 0.2, x + r * 0.8, y + r * 0.9],
             start=20, end=160, fill=(60, 0, 8, 55), width=2)

# ---------------------------------------------------------------- vignette + grain
# no per-pixel grain: it inflates the PNG far past the 1 MiB cap.
# A whisper of blur-free smoothness keeps the file small instead.
arr = np.asarray(img.convert("RGB")).astype(np.float32)
vig = 1.0 - 0.34 * np.clip(r2 - 0.25, 0, None) ** 1.4
arr *= vig[..., None]
out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGB")
out.save("entry.png", optimize=True)
print("saved entry.png", os.path.getsize("entry.png"), "bytes")
