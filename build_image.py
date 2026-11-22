"""Render the entry image: one strawberry, macro, glossy, dripping-fresh.

A single ripe strawberry fills the frame against a dark moody
background: scarlet flesh with a soft radial light, pale achenes in
curved rows, a fresh green calyx, water droplets and a hard specular
gloss. Everything is drawn procedurally with numpy + Pillow; no
external assets, no network. Output is 1024x1024 PNG, well under 1 MiB.

Run:  python3 build_image.py   (writes entry.png next to this file)
"""

import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

W = H = 1024
random.seed(20261122)
np.random.seed(20261122)

CX, TOP, BOT = 512, 268, 948  # body centre-x, top and tip of the berry
HALF_W = 292                   # max half width of the body


def body_half_width(s: float) -> float:
    """Half width of the berry at normalised height s (0 top, 1 tip)."""
    # Wide shoulders, long taper to a rounded tip.
    base = math.sin(math.pi * (0.12 + 0.88 * s)) ** 0.62
    shoulder = 1.0 - 0.22 * math.exp(-((s - 0.18) ** 2) / 0.02)
    tip = 1.0 - 0.55 * max(0.0, s - 0.82) ** 2 * 6.0
    # Narrow the flat top: shoulders slope in toward the calyx.
    top_taper = 0.62 + 0.38 * min(max((s - 0.02) / 0.16, 0.0), 1.0)
    return HALF_W * base * shoulder * max(tip, 0.12) * top_taper


def body_outline() -> list:
    """Polygon points of the berry outline, clockwise from top centre."""
    pts = []
    n = 140
    for i in range(n + 1):
        s = i / n
        y = TOP + s * (BOT - TOP)
        hw = body_half_width(s)
        # Slight dip at the top centre where the calyx sits.
        dip = 26 * math.exp(-((s) ** 2) / 0.004) if s < 0.12 else 0
        pts.append((CX - hw, y + dip))
    for i in range(n, -1, -1):
        s = i / n
        y = TOP + s * (BOT - TOP)
        hw = body_half_width(s)
        dip = 26 * math.exp(-((s) ** 2) / 0.004) if s < 0.12 else 0
        pts.append((CX + hw, y + dip))
    return pts


def background() -> Image.Image:
    """Dark green-charcoal gradient with soft warm bokeh and vignette."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    t = yy / H
    top = np.array([16, 26, 18], dtype=np.float32)
    bot = np.array([7, 12, 9], dtype=np.float32)
    arr = top[None, None, :] * (1 - t)[..., None] + bot[None, None, :] * t[..., None]
    img = Image.fromarray(arr.astype(np.uint8), "RGB").convert("RGBA")
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    for (bx, by, br, col, al) in [
        (180, 180, 90, (120, 160, 90), 26),
        (880, 150, 70, (190, 150, 60), 22),
        (920, 830, 110, (90, 130, 70), 20),
        (120, 860, 80, (150, 120, 50), 18),
        (512, 90, 130, (70, 110, 60), 16),
    ]:
        gd.ellipse([bx - br, by - br, bx + br, by + br], fill=col + (al,))
    glow = glow.filter(ImageFilter.GaussianBlur(38))
    img.alpha_composite(glow)
    # Vignette: darken the corners.
    vig = Image.new("L", (W, H), 0)
    vd = ImageDraw.Draw(vig)
    vd.ellipse([-260, -260, W + 260, H + 260], fill=255)
    vig = vig.filter(ImageFilter.GaussianBlur(180))
    black = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    img = Image.composite(img, black, vig.point(lambda v: 255 - int(0.42 * (255 - v))))
    return img.convert("RGB")


def berry_body() -> Image.Image:
    """The red flesh: radial light, edge darkening, fine grain, streaks."""
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).polygon(body_outline(), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(1.6))
    m = np.asarray(mask, dtype=np.float32) / 255.0

    # Normalised position inside the berry (approx: distance from centre).
    dx = (xx - (CX - 120)) / 620.0
    dy = (yy - (TOP + 190)) / 700.0
    r = np.sqrt(dx * dx + dy * dy)
    light = np.clip(1.0 - r * 1.15, 0, 1) ** 1.6

    # Base reds: bright scarlet where lit, deep crimson in shadow.
    lit = np.array([255, 74, 56], dtype=np.float32)
    mid = np.array([214, 28, 38], dtype=np.float32)
    dark = np.array([122, 12, 26], dtype=np.float32)
    col = mid[None, None, :] * (1 - light)[..., None] + lit[None, None, :] * light[..., None]
    # Deepen toward the lower right and the rim.
    edge = np.clip((r - 0.55) * 2.2, 0, 1)
    col = col * (1 - 0.45 * edge[..., None]) + dark[None, None, :] * (0.45 * edge[..., None])
    # Warm bottom glow, cool top sheen.
    col[..., 0] += 14 * np.clip(1 - yy / H, 0, 1) * m
    # Fine organic grain.
    grain = np.random.normal(0, 1, (H, W)).astype(np.float32)
    grain = np.asarray(Image.fromarray(((grain - grain.min()) / (grain.ptp()) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), dtype=np.float32)
    col += (grain[..., None] - 128) * 0.10
    # Faint vertical fibre streaks.
    streak = np.sin(xx * 0.11 + np.sin(yy * 0.02) * 6.0) * 5.0
    col += streak[..., None]

    arr = np.clip(col, 0, 255).astype(np.uint8)
    img = Image.fromarray(arr, "RGB").convert("RGBA")
    img.putalpha(Image.fromarray((m * 255).astype(np.uint8), "L"))
    return img


def seeds_layer() -> Image.Image:
    """Pale achenes in curved rows, each with a soft shadow pit."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rows = 9
    for ri in range(rows):
        s = 0.12 + 0.78 * ri / (rows - 1)
        y = TOP + s * (BOT - TOP)
        hw = body_half_width(s) * 0.88
        n = max(3, int(hw / 62))
        for ci in range(-n, n + 1):
            fx = ci / max(n, 1)
            x = CX + fx * hw + (12 if ri % 2 else -12) * (1 - abs(fx))
            if abs(x - CX) > hw:
                continue
            depth = 1 - abs(fx) * 0.45          # seeds shrink toward the rim
            rx, ry = 7 * depth, 10 * depth
            ang = math.degrees(math.atan2(x - CX, 260)) * 0.6
            # Shadow pit, then the small golden seed sunk into it.
            d.ellipse([x - rx - 1, y - ry + 2, x + rx + 3, y + ry + 4],
                      fill=(96, 10, 20, 170))
            d.ellipse([x - rx, y - ry, x + rx, y + ry], fill=(232, 201, 120, 255))
            d.ellipse([x - rx * 0.45, y - ry * 0.55, x + rx * 0.1, y - ry * 0.05],
                      fill=(252, 238, 180, 255))
    return layer.filter(ImageFilter.GaussianBlur(0.6))


def calyx_layer() -> Image.Image:
    """Fresh green star leaves + stem at the top of the berry."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy = CX, TOP + 6
    leaves = [
        (-120, -30, 0.92), (-70, -58, 1.0), (-15, -70, 1.05),
        (45, -68, 1.02), (100, -52, 0.96), (140, -26, 0.88),
        (-150, 4, 0.78), (150, 6, 0.78),
    ]
    for dx, dy, sc in leaves:
        tip = (cx + dx * 1.15 * sc, cy + dy * 1.35 * sc)
        base_l = (cx + dx * 0.28 - 30 * sc, cy + dy * 0.28 + 12)
        base_r = (cx + dx * 0.28 + 30 * sc, cy + dy * 0.28 + 12)
        mid_l = (cx + dx * 0.85 - 16 * sc, cy + dy * 0.85)
        mid_r = (cx + dx * 0.85 + 16 * sc, cy + dy * 0.85)
        d.polygon([base_l, mid_l, tip, mid_r, base_r], fill=(38, 102, 44, 255))
        d.line([cx, cy, tip[0], tip[1]], fill=(22, 66, 30, 255), width=3)
    # Centre cap + stem.
    d.ellipse([cx - 52, cy - 26, cx + 52, cy + 26], fill=(58, 140, 62, 255))
    d.ellipse([cx - 30, cy - 34, cx + 30, cy - 2], fill=(110, 190, 96, 255))
    d.polygon([(cx - 13, cy - 30), (cx + 13, cy - 30), (cx + 20, cy - 118),
               (cx - 6, cy - 118)], fill=(58, 122, 52, 255))
    d.line([(cx + 4, cy - 32), (cx + 8, cy - 112)], fill=(96, 170, 84, 255), width=4)
    return layer


def gloss_layer() -> Image.Image:
    """Hard specular gloss upper-left + thin rim light on the left edge."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.ellipse([CX - 300, TOP + 40, CX - 40, TOP + 330], fill=(255, 255, 255, 55))
    d.ellipse([CX - 250, TOP + 90, CX - 120, TOP + 240], fill=(255, 255, 255, 80))
    layer = layer.filter(ImageFilter.GaussianBlur(26))
    # Rim light: a soft bright arc hugging the left shoulder.
    rim = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd = ImageDraw.Draw(rim)
    pts = []
    for i in range(61):
        s = 0.06 + 0.5 * i / 60
        y = TOP + s * (BOT - TOP)
        pts.append((CX - body_half_width(s) + 6, y))
    rd.line(pts, fill=(255, 210, 190, 170), width=7)
    rim = rim.filter(ImageFilter.GaussianBlur(6))
    layer.alpha_composite(rim)
    return layer


def droplets_layer() -> Image.Image:
    """Water droplets on the flesh: bead, rim, specular dot."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    spots = []
    for _ in range(12):
        s = random.uniform(0.14, 0.7)
        y = TOP + s * (BOT - TOP)
        hw = body_half_width(s) * 0.82
        x = CX + random.uniform(-hw, hw)
        r = random.uniform(5, 12) * (1.15 - abs(x - CX) / (hw + 1) * 0.4)
        spots.append((x, y, r))
    for x, y, r in spots:
        d.ellipse([x - r, y - r, x + r, y + r], fill=(210, 228, 238, 46))
        d.ellipse([x - r, y - r, x + r, y + r], outline=(255, 255, 255, 90), width=1)
        d.ellipse([x - r * 0.45, y - r * 0.5, x - r * 0.05, y - r * 0.1],
                  fill=(255, 255, 255, 190))
    return layer.filter(ImageFilter.GaussianBlur(0.5))


def main() -> None:
    img = background()
    img = img.convert("RGBA")
    img.alpha_composite(berry_body())
    img.alpha_composite(seeds_layer())
    img.alpha_composite(calyx_layer())
    img.alpha_composite(gloss_layer())
    img.alpha_composite(droplets_layer())
    out = img.convert("RGB")
    out = ImageEnhance.Color(out).enhance(1.12)
    out = ImageEnhance.Contrast(out).enhance(1.06)
    out.save("entry.png", optimize=True)
    print("wrote entry.png", out.size)


if __name__ == "__main__":
    main()
