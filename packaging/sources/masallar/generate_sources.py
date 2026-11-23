"""Generate Masallar source PNGs: reuse approved AI previews, fill rest procedurally.

Procedural scenes drawn at a low pixel grid then nearest-neighbor upscaled to
~1448×1086 (4:3) so .pcolor conversion keeps flat, connected color areas.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parent
STORE_SOURCES = Path(
    "/cursor/stores/bc-8bf5c8a7-dcae-4c5b-a5ef-c31a5dc1f404/media/masallar-sources"
)
PREVIEW_DIR = Path(
    "/cursor/stores/bc-8bf5c8a7-dcae-4c5b-a5ef-c31a5dc1f404/media/masallar-previews"
)
SOURCE_W, SOURCE_H = 1448, 1086

PREVIEW_MAP = {
    "001-tac.png": "masallar-t1-01-tac.jpg",
    "002-sihirli-lamba.png": "masallar-t1-02-sihirli-lamba.jpg",
    "003-cam-ayakkabi.png": "masallar-t1-03-cam-ayakkabi.jpg",
    "014-peri.png": "masallar-t2-01-peri.jpg",
    "015-kurbaga-prens.png": "masallar-t2-02-kurbaga-prens.jpg",
    "016-kurt.png": "masallar-t2-03-kurt.jpg",
    "027-orman-kulubesi.png": "masallar-t3-01-orman-kulubesi.jpg",
    "028-kule.png": "masallar-t3-02-kule.jpg",
    "029-denizkizi.png": "masallar-t3-03-denizkizi.jpg",
    "040-ejderha.png": "masallar-t4-01-ejderha.jpg",
    "041-cadi.png": "masallar-t4-02-cadi.jpg",
    "042-savasci.png": "masallar-t4-03-savasci.jpg",
    "053-buyulu-orman.png": "masallar-t5-01-buyulu-orman.jpg",
    "054-ucan-hali.png": "masallar-t5-02-ucan-hali.jpg",
    "055-peri-sarayi.png": "masallar-t5-03-peri-sarayi.jpg",
    "066-keloglan.png": "masallar-t6-01-keloglan.jpg",
    "067-nasreddin.png": "masallar-t6-02-nasreddin.jpg",
    "068-alibaba.png": "masallar-t6-03-alibaba.jpg",
    "079-ejderha-savasi.png": "masallar-t7-01-ejderha-savasi.jpg",
    "080-efsane-krallik.png": "masallar-t7-02-efsane-krallik.jpg",
    "081-binbir-gece.png": "masallar-t7-03-binbir-gece.jpg",
}


def grid_for_tier(tier: int) -> tuple[int, int]:
    return {
        1: (80, 60),
        2: (100, 75),
        3: (120, 90),
        4: (140, 105),
        5: (160, 120),
        6: (180, 135),
        7: (200, 150),
    }[tier]


def upscale(img: Image.Image) -> Image.Image:
    return img.resize((SOURCE_W, SOURCE_H), Image.Resampling.NEAREST)


def fold_preview(preview_name: str) -> Image.Image:
    path = PREVIEW_DIR / preview_name
    with Image.open(path) as image:
        rgb = image.convert("RGB")
        # Cover 4:3 canvas with nearest-neighbor feel via BOX then NEAREST.
        fitted = rgb.resize((SOURCE_W, SOURCE_H), Image.Resampling.BOX)
        return fitted


def sky(draw, w, h, top, bottom, horizon=None):
    horizon = horizon if horizon is not None else h * 2 // 3
    for y in range(horizon):
        t = y / max(1, horizon - 1)
        c = tuple(int(top[i] * (1 - t) + bottom[i] * t) for i in range(3))
        draw.line((0, y, w, y), fill=c)
    return horizon


def ground(draw, w, h, y0, colors):
    for y in range(y0, h):
        t = (y - y0) / max(1, h - y0 - 1)
        c = tuple(int(colors[0][i] * (1 - t) + colors[1][i] * t) for i in range(3))
        draw.line((0, y, w, y), fill=c)


def oval(draw, cx, cy, rx, ry, fill, outline=None):
    draw.ellipse((cx - rx, cy - ry, cx + rx, cy + ry), fill=fill, outline=outline)


def rect(draw, x, y, ww, hh, fill):
    draw.rectangle((x, y, x + ww - 1, y + hh - 1), fill=fill)


def triangle(draw, pts, fill):
    draw.polygon(pts, fill=fill)


def sparkles(draw, w, h, rng, n, colors):
    for _ in range(n):
        x, y = rng.randrange(w), rng.randrange(h)
        c = colors[rng.randrange(len(colors))]
        draw.point((x, y), fill=c)
        if rng.random() < 0.35:
            draw.point((x + 1, y), fill=c)
            draw.point((x - 1, y), fill=c)
            draw.point((x, y + 1), fill=c)
            draw.point((x, y - 1), fill=c)


def tree(draw, x, y, trunk_h, canopy_r, trunk=(90, 55, 30), leaf=(40, 120, 55)):
    rect(draw, x - 2, y - trunk_h, 4, trunk_h, trunk)
    oval(draw, x, y - trunk_h - canopy_r // 2, canopy_r, canopy_r, leaf)


def person(draw, cx, cy, scale, clothes, skin=(235, 190, 150), hair=(60, 40, 30)):
    s = scale
    oval(draw, cx, cy - 10 * s, 4 * s, 4 * s, skin)  # head
    oval(draw, cx, cy - 12 * s, 5 * s, 3 * s, hair)  # hair
    rect(draw, cx - 4 * s, cy - 6 * s, 8 * s, 10 * s, clothes)  # torso
    rect(draw, cx - 4 * s, cy + 4 * s, 3 * s, 7 * s, (50, 40, 35))  # legs
    rect(draw, cx + 1 * s, cy + 4 * s, 3 * s, 7 * s, (50, 40, 35))


def castle(draw, x, y, ww, hh, wall=(180, 170, 160), roof=(140, 50, 50)):
    rect(draw, x, y, ww, hh, wall)
    for i in range(0, ww, 6):
        rect(draw, x + i, y - 4, 3, 4, wall)
    # towers
    rect(draw, x - 6, y + 4, 10, hh - 4, wall)
    rect(draw, x + ww - 4, y + 4, 10, hh - 4, wall)
    triangle(draw, [(x - 8, y + 4), (x - 1, y - 10), (x + 6, y + 4)], roof)
    triangle(draw, [(x + ww - 6, y + 4), (x + ww + 1, y - 10), (x + ww + 8, y + 4)], roof)
    # door/windows
    rect(draw, x + ww // 2 - 3, y + hh - 14, 6, 14, (60, 40, 30))
    rect(draw, x + 6, y + 10, 4, 5, (220, 210, 120))
    rect(draw, x + ww - 12, y + 10, 4, 5, (220, 210, 120))


def dragon(draw, cx, cy, scale, body=(50, 130, 70), wing=(40, 100, 60)):
    s = scale
    oval(draw, cx, cy, 14 * s, 8 * s, body)
    oval(draw, cx + 12 * s, cy - 4 * s, 6 * s, 5 * s, body)  # head
    triangle(draw, [(cx + 16 * s, cy - 6 * s), (cx + 22 * s, cy - 2 * s), (cx + 16 * s, cy)], (200, 80, 60))
    # wing
    triangle(
        draw,
        [(cx - 2 * s, cy - 2 * s), (cx - 18 * s, cy - 16 * s), (cx + 6 * s, cy - 4 * s)],
        wing,
    )
    rect(draw, cx - 12 * s, cy + 4 * s, 3 * s, 8 * s, body)
    rect(draw, cx + 4 * s, cy + 4 * s, 3 * s, 8 * s, body)


def render_scene(item: dict) -> Image.Image:
    tier = item["tier"]
    slug = item["slug"]
    w, h = grid_for_tier(tier)
    rng = random.Random(hash((item["id"], slug, tier)) & 0xFFFFFFFF)
    img = Image.new("RGB", (w, h), (30, 40, 60))
    draw = ImageDraw.Draw(img)
    cx, cy = w // 2, h // 2

    # ---- Tier-aware backgrounds + subject by slug family ----
    if slug in ("tac", "buyulu-yuzuk", "altin-anahtar", "sihir-asasi", "buyulu-ayna",
                "zehirli-elma", "buyulu-kitap", "kristal-top", "buyulu-kese",
                "peri-toz", "altin-yumurta", "sihirli-lamba", "cam-ayakkabi"):
        sky(draw, w, h, (180, 150, 220), (240, 220, 255), h)
        sparkles(draw, w, h, rng, 12 + tier * 3, [(255, 255, 220), (255, 230, 150), (255, 255, 255)])
        if "yuzuk" in slug:
            oval(draw, cx, cy, 16, 16, (220, 180, 40), (160, 120, 20))
            oval(draw, cx, cy, 10, 10, (180, 150, 220))
            oval(draw, cx, cy - 2, 4, 5, (80, 160, 220))
        elif "anahtar" in slug:
            oval(draw, cx - 8, cy, 8, 8, (220, 180, 40))
            rect(draw, cx - 2, cy - 2, 22, 4, (220, 180, 40))
            rect(draw, cx + 14, cy - 2, 3, 8, (220, 180, 40))
            rect(draw, cx + 18, cy - 2, 3, 6, (220, 180, 40))
        elif "asa" in slug:
            rect(draw, cx - 2, cy - 22, 4, 44, (140, 90, 40))
            oval(draw, cx, cy - 24, 7, 7, (120, 220, 255))
            sparkles(draw, w, h // 2, rng, 10, [(180, 255, 255)])
        elif "ayna" in slug:
            oval(draw, cx, cy, 14, 18, (200, 180, 60))
            oval(draw, cx, cy, 10, 14, (160, 210, 230))
        elif "elma" in slug:
            oval(draw, cx, cy + 2, 12, 12, (180, 30, 40))
            rect(draw, cx - 1, cy - 12, 2, 6, (80, 50, 20))
            oval(draw, cx + 4, cy - 10, 5, 3, (40, 130, 50))
        elif "kitap" in slug:
            rect(draw, cx - 14, cy - 10, 28, 22, (120, 40, 40))
            rect(draw, cx - 12, cy - 8, 24, 18, (240, 230, 200))
            for i in range(3):
                draw.line((cx - 8, cy - 4 + i * 5, cx + 8, cy - 4 + i * 5), fill=(180, 160, 120))
        elif "kristal" in slug:
            oval(draw, cx, cy, 12, 12, (140, 200, 240))
            oval(draw, cx - 3, cy - 3, 4, 4, (220, 250, 255))
        elif "kese" in slug:
            oval(draw, cx, cy + 2, 12, 10, (140, 90, 40))
            rect(draw, cx - 4, cy - 10, 8, 8, (160, 110, 50))
            oval(draw, cx, cy - 2, 3, 3, (220, 180, 40))
        elif "toz" in slug:
            oval(draw, cx, cy + 4, 10, 12, (180, 120, 220))
            rect(draw, cx - 4, cy - 10, 8, 6, (200, 180, 80))
            sparkles(draw, w, h, rng, 20, [(255, 200, 255), (255, 255, 200)])
        elif "yumurta" in slug:
            oval(draw, cx, cy, 12, 16, (240, 200, 60))
            oval(draw, cx - 3, cy - 4, 4, 5, (255, 240, 150))
        elif "lamba" in slug:
            oval(draw, cx, cy + 2, 14, 10, (180, 140, 40))
            rect(draw, cx + 8, cy - 2, 10, 4, (180, 140, 40))
            oval(draw, cx - 2, cy - 8, 5, 4, (200, 160, 50))
        elif "ayakkabi" in slug:
            oval(draw, cx, cy + 4, 16, 8, (180, 230, 255))
            rect(draw, cx - 14, cy - 4, 8, 10, (180, 230, 255))
        else:  # tac fallback
            rect(draw, cx - 16, cy, 32, 8, (220, 180, 40))
            for dx in (-12, -4, 4, 12):
                triangle(draw, [(cx + dx - 4, cy), (cx + dx, cy - 12), (cx + dx + 4, cy)], (220, 180, 40))
            oval(draw, cx, cy + 2, 3, 3, (160, 60, 200))

    elif slug in ("peri", "kurbaga-prens", "kurt", "beyaz-tavsan", "baykus", "tekboynuz",
                  "cin", "cuce", "kugu", "tilki", "anka-yavru", "ejderha-yavru", "gulyabani"):
        hz = sky(draw, w, h, (120, 180, 230), (200, 230, 255))
        ground(draw, w, h, hz, [(70, 140, 60), (50, 100, 40)])
        for i in range(3 + tier // 2):
            tree(draw, 10 + i * (w // 5), hz + 2, 18 + rng.randint(0, 8), 10 + rng.randint(0, 4))
        if slug == "kurbaga-prens":
            oval(draw, cx, cy + 6, 14, 10, (60, 150, 70))
            oval(draw, cx - 6, cy - 2, 4, 4, (80, 180, 90))
            oval(draw, cx + 6, cy - 2, 4, 4, (80, 180, 90))
            rect(draw, cx - 6, cy - 10, 12, 5, (220, 180, 40))
        elif slug == "kurt":
            oval(draw, cx, cy, 16, 10, (120, 110, 100))
            oval(draw, cx + 12, cy - 4, 8, 7, (120, 110, 100))
            triangle(draw, [(cx + 8, cy - 10), (cx + 12, cy - 18), (cx + 16, cy - 10)], (120, 110, 100))
        elif slug == "beyaz-tavsan":
            oval(draw, cx, cy + 4, 10, 12, (245, 245, 250))
            rect(draw, cx - 6, cy - 16, 3, 14, (245, 245, 250))
            rect(draw, cx + 3, cy - 16, 3, 14, (245, 245, 250))
            oval(draw, cx + 2, cy + 2, 3, 3, (255, 180, 180))
        elif slug == "baykus":
            oval(draw, cx, cy, 12, 14, (140, 100, 60))
            oval(draw, cx - 4, cy - 4, 4, 4, (240, 220, 100))
            oval(draw, cx + 4, cy - 4, 4, 4, (240, 220, 100))
            triangle(draw, [(cx - 2, cy + 2), (cx + 2, cy + 2), (cx, cy + 8)], (220, 140, 40))
        elif slug == "tekboynuz":
            oval(draw, cx, cy + 4, 16, 10, (250, 245, 255))
            oval(draw, cx + 12, cy - 2, 8, 7, (250, 245, 255))
            triangle(draw, [(cx + 12, cy - 8), (cx + 14, cy - 22), (cx + 16, cy - 8)], (220, 200, 255))
            sparkles(draw, w, h, rng, 15, [(255, 255, 255), (230, 210, 255)])
        elif slug == "cin":
            oval(draw, cx, cy - 4, 10, 12, (80, 180, 160))
            oval(draw, cx, cy - 14, 7, 7, (235, 190, 150))
            triangle(draw, [(cx - 8, cy + 8), (cx + 8, cy + 8), (cx, cy + 28)], (60, 140, 130))
            sparkles(draw, w, h, rng, 12, [(120, 255, 220)])
        elif slug == "cuce":
            person(draw, cx, cy, 1, (160, 50, 50))
            triangle(draw, [(cx - 6, cy - 14), (cx, cy - 26), (cx + 6, cy - 14)], (40, 100, 50))
        elif slug == "kugu":
            oval(draw, cx, cy + 4, 14, 8, (250, 250, 255))
            rect(draw, cx + 10, cy - 10, 3, 14, (250, 250, 255))
            oval(draw, cx + 12, cy - 12, 4, 4, (250, 250, 255))
            triangle(draw, [(cx + 16, cy - 12), (cx + 22, cy - 10), (cx + 16, cy - 8)], (240, 160, 40))
        elif slug == "tilki":
            oval(draw, cx, cy, 14, 8, (200, 110, 40))
            oval(draw, cx + 10, cy - 4, 7, 6, (200, 110, 40))
            triangle(draw, [(cx - 12, cy), (cx - 22, cy + 4), (cx - 10, cy + 6)], (200, 110, 40))
        elif "anka" in slug:
            oval(draw, cx, cy, 12, 8, (220, 80, 40))
            triangle(draw, [(cx - 4, cy - 4), (cx - 18, cy - 16), (cx + 2, cy - 6)], (255, 160, 40))
            triangle(draw, [(cx + 4, cy - 4), (cx + 18, cy - 16), (cx - 2, cy - 6)], (255, 120, 40))
        elif "ejderha-yavru" in slug:
            dragon(draw, cx, cy, 1, (80, 160, 90), (60, 130, 70))
        elif slug == "gulyabani":
            oval(draw, cx, cy, 14, 16, (100, 140, 70))
            oval(draw, cx - 4, cy - 4, 3, 3, (240, 240, 80))
            oval(draw, cx + 4, cy - 4, 3, 3, (240, 240, 80))
        else:  # peri
            person(draw, cx, cy, 1, (200, 160, 220), hair=(240, 220, 120))
            triangle(draw, [(cx - 6, cy - 2), (cx - 18, cy - 10), (cx - 4, cy + 6)], (200, 240, 255))
            triangle(draw, [(cx + 6, cy - 2), (cx + 18, cy - 10), (cx + 4, cy + 6)], (200, 240, 255))
            sparkles(draw, w, h, rng, 14, [(255, 255, 200)])

    elif slug in ("orman-kulubesi", "kule", "denizkizi", "buyulu-kopru", "degirmen",
                  "gizli-bahce", "magara", "buyulu-gol", "tas-kapi", "orman-yolu",
                  "peri-halka", "dilekkuyusu", "cam-kosk"):
        if slug == "denizkizi":
            hz = sky(draw, w, h, (255, 160, 100), (80, 120, 200))
            ground(draw, w, h, hz, [(30, 90, 160), (10, 50, 100)])
            oval(draw, cx, cy - 4, 8, 8, (235, 190, 150))
            rect(draw, cx - 5, cy + 2, 10, 8, (220, 120, 140))
            triangle(draw, [(cx - 6, cy + 10), (cx + 6, cy + 10), (cx, cy + 24)], (40, 160, 140))
            for i in range(4):
                oval(draw, 8 + i * 12, h - 8, 10, 4, (200, 180, 140))
        elif slug == "magara":
            hz = sky(draw, w, h, (60, 50, 80), (120, 100, 90))
            ground(draw, w, h, hz, [(90, 70, 50), (60, 45, 30)])
            oval(draw, cx, cy + 4, 28, 24, (40, 30, 25))
            oval(draw, cx, cy + 6, 18, 16, (20, 15, 12))
            sparkles(draw, w, h, rng, 8, [(220, 180, 40)])
        elif slug == "buyulu-gol":
            hz = sky(draw, w, h, (100, 160, 220), (200, 230, 255))
            ground(draw, w, h, hz - 4, [(40, 100, 160), (20, 70, 120)])
            for i in range(5):
                tree(draw, 6 + i * (w // 5), hz - 2, 16, 9, leaf=(30, 100 + i * 8, 50))
            sparkles(draw, w, h // 2, rng, 10, [(200, 255, 255)])
        elif slug == "degirmen":
            hz = sky(draw, w, h, (140, 190, 240), (230, 240, 255))
            ground(draw, w, h, hz, [(120, 170, 70), (90, 130, 50)])
            rect(draw, cx - 10, cy - 4, 20, 28, (200, 180, 140))
            triangle(draw, [(cx - 12, cy - 4), (cx, cy - 22), (cx + 12, cy - 4)], (160, 60, 50))
            for ang in range(4):
                dx = [12, 0, -12, 0][ang]
                dy = [0, 12, 0, -12][ang]
                draw.line((cx, cy, cx + dx, cy + dy - 8), fill=(180, 160, 120), width=3)
        elif slug == "buyulu-kopru":
            hz = sky(draw, w, h, (120, 170, 230), (210, 230, 255))
            ground(draw, w, h, hz + 10, [(50, 100, 160), (30, 70, 120)])
            for x in range(8, w - 8, 6):
                y = hz - 8 - abs(x - cx) // 3
                rect(draw, x, y, 5, hz + 12 - y, (140, 130, 120))
        elif slug == "gizli-bahce":
            hz = sky(draw, w, h, (160, 200, 240), (230, 250, 255))
            ground(draw, w, h, hz, [(60, 140, 70), (40, 100, 50)])
            rect(draw, 10, hz - 30, w - 20, 8, (150, 140, 130))
            for i in range(8):
                oval(draw, 16 + i * 10, hz - 6, 4, 4,
                     [(220, 60, 80), (240, 180, 40), (180, 80, 200)][i % 3])
        elif slug == "tas-kapi":
            hz = sky(draw, w, h, (100, 120, 160), (180, 190, 210))
            ground(draw, w, h, hz, [(90, 80, 70), (60, 50, 40)])
            rect(draw, cx - 18, cy - 20, 36, 40, (130, 120, 110))
            oval(draw, cx, cy + 4, 10, 16, (30, 25, 20))
            sparkles(draw, w, h // 2, rng, 8, [(180, 220, 255)])
        elif slug == "orman-yolu":
            hz = sky(draw, w, h, (90, 140, 100), (160, 200, 140))
            ground(draw, w, h, hz - 10, [(80, 60, 40), (60, 45, 30)])
            for i in range(6):
                tree(draw, 4 + i * (w // 6), hz, 20 + (i % 3) * 4, 11)
            # path taper
            for y in range(hz, h):
                half = 4 + (y - hz)
                draw.line((cx - half, y, cx + half, y), fill=(150, 120, 70))
        elif slug == "peri-halka":
            hz = sky(draw, w, h, (140, 100, 180), (220, 180, 240))
            ground(draw, w, h, hz, [(50, 120, 60), (30, 90, 40)])
            for i in range(12):
                a = i / 12 * math.pi * 2
                oval(draw, int(cx + 18 * math.cos(a)), int(cy + 10 * math.sin(a)), 4, 3, (180, 80, 200))
            sparkles(draw, w, h, rng, 16, [(255, 220, 255)])
        elif slug == "dilekkuyusu":
            hz = sky(draw, w, h, (130, 180, 230), (220, 240, 255))
            ground(draw, w, h, hz, [(70, 130, 60), (50, 100, 40)])
            oval(draw, cx, cy + 6, 18, 10, (120, 110, 100))
            oval(draw, cx, cy + 6, 12, 6, (40, 80, 140))
            rect(draw, cx - 2, cy - 16, 4, 20, (140, 100, 60))
        elif slug == "cam-kosk":
            hz = sky(draw, w, h, (180, 210, 255), (240, 250, 255))
            ground(draw, w, h, hz, [(100, 180, 120), (70, 140, 90)])
            rect(draw, cx - 16, cy - 8, 32, 30, (180, 230, 255))
            triangle(draw, [(cx - 18, cy - 8), (cx, cy - 26), (cx + 18, cy - 8)], (140, 200, 240))
            for i in range(3):
                rect(draw, cx - 10 + i * 8, cy + 4, 5, 8, (220, 250, 255))
        elif slug == "kule":
            hz = sky(draw, w, h, (140, 180, 230), (220, 235, 255))
            ground(draw, w, h, hz, [(80, 140, 70), (50, 100, 40)])
            rect(draw, cx - 10, cy - 30, 20, 50, (160, 150, 140))
            triangle(draw, [(cx - 12, cy - 30), (cx, cy - 48), (cx + 12, cy - 30)], (140, 50, 50))
            rect(draw, cx - 3, cy - 20, 6, 6, (220, 210, 120))
            draw.line((cx, cy - 18, cx + 16, hz), fill=(240, 220, 120), width=2)
        else:  # orman-kulubesi
            hz = sky(draw, w, h, (80, 100, 140), (180, 140, 100))
            ground(draw, w, h, hz, [(40, 90, 50), (30, 60, 35)])
            for i in range(5):
                tree(draw, 6 + i * (w // 5), hz, 22, 12)
            rect(draw, cx - 16, cy, 32, 22, (120, 80, 40))
            triangle(draw, [(cx - 18, cy), (cx, cy - 16), (cx + 18, cy)], (80, 50, 30))
            rect(draw, cx - 4, cy + 8, 8, 14, (60, 40, 20))
            rect(draw, cx + 6, cy + 4, 6, 6, (240, 200, 80))

    elif slug in ("ejderha", "cadi", "savasci", "prenses", "prens", "buyucu",
                  "cizmeli-kedi", "pamuk-prenses", "kirmizi-baslik", "cin-cikis",
                  "anka", "grifon", "deniz-canavari"):
        hz = sky(draw, w, h, (90, 120, 180), (200, 210, 230))
        ground(draw, w, h, hz, [(70, 110, 55), (45, 80, 40)])
        if slug == "ejderha":
            dragon(draw, cx - 4, cy, 2)
        elif slug == "cadi":
            person(draw, cx, cy, 2, (90, 40, 120), hair=(40, 30, 30))
            triangle(draw, [(cx - 10, cy - 28), (cx, cy - 48), (cx + 10, cy - 28)], (60, 30, 90))
            oval(draw, cx + 16, cy + 8, 12, 8, (30, 30, 30))
            oval(draw, cx + 16, cy + 6, 8, 5, (80, 200, 80))
        elif slug == "savasci":
            person(draw, cx, cy, 2, (160, 160, 170), hair=(80, 60, 40))
            rect(draw, cx + 10, cy - 8, 3, 24, (180, 180, 190))
            triangle(draw, [(cx + 10, cy - 12), (cx + 16, cy - 6), (cx + 10, cy - 4)], (200, 200, 210))
            oval(draw, cx - 12, cy, 8, 10, (140, 90, 40))
        elif slug == "prenses":
            person(draw, cx, cy, 2, (200, 80, 140), hair=(220, 180, 60))
            triangle(draw, [(cx - 10, cy + 4), (cx + 10, cy + 4), (cx, cy + 22)], (220, 100, 160))
            rect(draw, cx - 6, cy - 30, 12, 5, (220, 180, 40))
        elif slug == "prens":
            person(draw, cx - 8, cy - 4, 2, (40, 80, 160))
            oval(draw, cx + 10, cy + 8, 16, 10, (120, 80, 40))
            oval(draw, cx + 20, cy, 8, 7, (120, 80, 40))
        elif slug == "buyucu":
            person(draw, cx, cy, 2, (50, 60, 140), hair=(230, 230, 240))
            triangle(draw, [(cx - 10, cy - 28), (cx, cy - 50), (cx + 10, cy - 28)], (40, 50, 120))
            rect(draw, cx + 12, cy - 6, 3, 28, (140, 100, 50))
            oval(draw, cx + 14, cy - 10, 5, 5, (120, 220, 255))
        elif slug == "cizmeli-kedi":
            oval(draw, cx, cy, 12, 10, (240, 150, 40))
            oval(draw, cx + 8, cy - 6, 7, 6, (240, 150, 40))
            rect(draw, cx - 8, cy + 8, 5, 8, (40, 40, 80))
            rect(draw, cx + 2, cy + 8, 5, 8, (40, 40, 80))
            triangle(draw, [(cx - 4, cy - 14), (cx, cy - 24), (cx + 4, cy - 14)], (160, 40, 40))
        elif slug == "pamuk-prenses":
            person(draw, cx, cy, 2, (40, 40, 50), hair=(20, 15, 15))
            triangle(draw, [(cx - 10, cy + 2), (cx + 10, cy + 2), (cx, cy + 20)], (200, 40, 50))
            oval(draw, cx + 14, cy + 6, 5, 5, (200, 40, 40))
        elif slug == "kirmizi-baslik":
            person(draw, cx, cy, 2, (200, 40, 40))
            triangle(draw, [(cx - 10, cy - 26), (cx, cy - 40), (cx + 10, cy - 26)], (200, 40, 40))
            oval(draw, cx + 14, cy + 4, 6, 6, (140, 90, 40))
        elif slug == "cin-cikis":
            oval(draw, cx, cy + 16, 14, 8, (180, 140, 40))
            oval(draw, cx, cy - 10, 12, 14, (60, 180, 160))
            oval(draw, cx, cy - 22, 7, 7, (235, 190, 150))
            sparkles(draw, w, h, rng, 18, [(100, 255, 220)])
        elif slug == "anka":
            oval(draw, cx, cy, 16, 10, (220, 60, 40))
            for side in (-1, 1):
                triangle(
                    draw,
                    [(cx, cy), (cx + side * 28, cy - 20), (cx + side * 8, cy + 4)],
                    (255, 140, 40),
                )
            sparkles(draw, w, h, rng, 12, [(255, 200, 80)])
        elif slug == "grifon":
            oval(draw, cx, cy, 16, 10, (180, 140, 60))
            oval(draw, cx + 12, cy - 6, 8, 8, (200, 160, 70))
            triangle(draw, [(cx - 4, cy - 4), (cx - 24, cy - 18), (cx + 4, cy - 2)], (160, 120, 50))
        else:  # deniz-canavari
            hz2 = sky(draw, w, h, (40, 80, 140), (20, 40, 80))
            ground(draw, w, h, hz2, [(20, 60, 120), (10, 30, 70)])
            oval(draw, cx, cy + 6, 28, 12, (40, 120, 90))
            oval(draw, cx + 20, cy - 4, 10, 10, (40, 120, 90))
            for i in range(3):
                oval(draw, cx - 10 + i * 10, cy - 8 - i * 2, 4, 8, (30, 100, 70))

    elif slug in ("buyulu-orman", "ucan-hali", "peri-sarayi", "buyulu-kale", "gol-kalesi",
                  "orman-tapinak", "yuzer-ada", "yeralti-saray", "buz-sarayi", "ates-dagi",
                  "sisli-vadi", "kopru-kent", "yildiz-kule"):
        if slug == "buyulu-orman":
            hz = sky(draw, w, h, (30, 40, 80), (60, 80, 120))
            ground(draw, w, h, hz, [(20, 60, 40), (15, 40, 30)])
            for i in range(8):
                tree(draw, 4 + i * (w // 8), hz, 24 + (i % 4) * 5, 12 + (i % 3) * 2,
                     leaf=(20, 80 + i * 5, 70))
            for i in range(10):
                oval(draw, rng.randrange(w), hz - 4 + rng.randrange(20), 3, 2, (80, 220, 160))
            sparkles(draw, w, h, rng, 20, [(160, 255, 200), (200, 180, 255)])
        elif slug == "ucan-hali":
            hz = sky(draw, w, h, (255, 180, 80), (120, 160, 220))
            ground(draw, w, h, hz + 10, [(210, 170, 90), (180, 130, 60)])
            for i in range(4):
                oval(draw, 20 + i * 20, hz + 4, 10, 6, (160, 100, 50))
            rect(draw, cx - 20, cy - 4, 40, 14, (180, 40, 50))
            for i in range(5):
                draw.line((cx - 18 + i * 8, cy - 2, cx - 18 + i * 8, cy + 8), fill=(220, 180, 40))
            person(draw, cx, cy - 10, 1, (40, 60, 120))
        elif slug == "peri-sarayi":
            hz = sky(draw, w, h, (200, 160, 255), (255, 230, 250))
            ground(draw, w, h, hz, [(100, 200, 160), (60, 150, 120)])
            castle(draw, cx - 30, cy - 10, 60, 40, wall=(230, 220, 255), roof=(255, 150, 200))
            sparkles(draw, w, h, rng, 24, [(255, 255, 255), (255, 200, 255)])
        elif slug == "buyulu-kale":
            hz = sky(draw, w, h, (100, 140, 200), (220, 230, 245))
            ground(draw, w, h, hz, [(70, 120, 60), (50, 90, 40)])
            castle(draw, cx - 36, cy - 8, 72, 48)
        elif slug == "gol-kalesi":
            hz = sky(draw, w, h, (120, 170, 220), (200, 230, 255))
            ground(draw, w, h, hz, [(30, 90, 150), (15, 50, 100)])
            castle(draw, cx - 28, cy - 6, 56, 36, wall=(170, 175, 185))
        elif slug == "orman-tapinak":
            hz = sky(draw, w, h, (80, 120, 90), (160, 190, 140))
            ground(draw, w, h, hz, [(50, 100, 50), (30, 70, 35)])
            for i in range(4):
                tree(draw, 8 + i * (w // 4), hz, 28, 14)
            rect(draw, cx - 20, cy, 40, 24, (160, 150, 120))
            for i in range(3):
                rect(draw, cx - 14 + i * 12, cy - 16, 6, 16, (160, 150, 120))
        elif slug == "yuzer-ada":
            hz = sky(draw, w, h, (60, 100, 200), (180, 210, 255))
            for y in range(hz, h):
                draw.line((0, y, w, y), fill=(100, 160, 220))
            oval(draw, cx, cy, 36, 14, (80, 140, 60))
            oval(draw, cx, cy + 10, 30, 8, (60, 50, 40))
            tree(draw, cx - 10, cy, 16, 10)
            rect(draw, cx + 8, cy - 8, 12, 14, (180, 170, 160))
        elif slug == "yeralti-saray":
            for y in range(h):
                draw.line((0, y, w, y), fill=(40, 30, 50))
            castle(draw, cx - 32, cy - 4, 64, 42, wall=(100, 80, 120), roof=(160, 60, 160))
            sparkles(draw, w, h, rng, 25, [(200, 150, 255), (255, 220, 100)])
        elif slug == "buz-sarayi":
            hz = sky(draw, w, h, (180, 220, 255), (240, 250, 255))
            ground(draw, w, h, hz, [(200, 230, 250), (160, 200, 240)])
            castle(draw, cx - 34, cy - 6, 68, 44, wall=(200, 240, 255), roof=(140, 200, 255))
        elif slug == "ates-dagi":
            hz = sky(draw, w, h, (40, 20, 30), (120, 40, 20))
            ground(draw, w, h, hz, [(60, 40, 30), (30, 20, 15)])
            triangle(draw, [(10, hz + 10), (cx, 8), (w - 10, hz + 10)], (80, 50, 40))
            triangle(draw, [(cx - 16, 30), (cx, 4), (cx + 16, 30)], (255, 120, 40))
            oval(draw, cx, 20, 10, 6, (255, 200, 80))
        elif slug == "sisli-vadi":
            hz = sky(draw, w, h, (140, 150, 170), (200, 205, 210))
            ground(draw, w, h, hz, [(70, 90, 70), (50, 70, 50)])
            for i in range(5):
                oval(draw, 10 + i * 18, hz - 6 - i, 20, 6, (210, 215, 220))
            castle(draw, cx - 20, cy + 4, 40, 24, wall=(120, 125, 130))
        elif slug == "kopru-kent":
            hz = sky(draw, w, h, (100, 150, 210), (210, 230, 255))
            ground(draw, w, h, hz + 8, [(40, 90, 150), (20, 50, 100)])
            for i in range(5):
                rect(draw, 8 + i * 18, hz - 18 - (i % 3) * 6, 14, 24 + (i % 3) * 6, (160, 150, 140))
            for x in range(6, w - 6, 5):
                rect(draw, x, hz - abs(x - cx) // 4, 4, 10 + abs(x - cx) // 4, (130, 120, 110))
        else:  # yildiz-kule
            hz = sky(draw, w, h, (20, 20, 50), (60, 40, 100))
            ground(draw, w, h, hz, [(40, 30, 50), (20, 15, 30)])
            sparkles(draw, w, hz, rng, 30, [(255, 255, 220), (200, 200, 255)])
            rect(draw, cx - 8, cy - 40, 16, 60, (100, 90, 140))
            triangle(draw, [(cx - 10, cy - 40), (cx, cy - 58), (cx + 10, cy - 40)], (220, 180, 80))
            oval(draw, cx, cy - 50, 4, 4, (255, 240, 120))

    elif slug in ("keloglan", "nasreddin", "alibaba", "dede-korkut", "tepegoz",
                  "asik-garip", "kirk-haramiler", "simbad", "alaaddin-saray",
                  "gul-bultul", "karagoz", "yedi-basli", "dev-kule"):
        hz = sky(draw, w, h, (140, 180, 230), (230, 240, 255))
        ground(draw, w, h, hz, [(120, 160, 70), (90, 120, 50)])
        if slug == "keloglan":
            person(draw, cx, cy, 2, (80, 120, 60), hair=(235, 210, 170), skin=(235, 190, 150))
            # bald: overwrite hair with skin oval
            oval(draw, cx, cy - 24, 8, 6, (235, 190, 150))
            oval(draw, cx + 14, cy + 4, 7, 7, (140, 100, 50))
        elif slug == "nasreddin":
            person(draw, cx - 4, cy - 6, 2, (40, 120, 60))
            oval(draw, cx - 4, cy - 30, 10, 6, (240, 240, 245))  # turban
            oval(draw, cx + 12, cy + 8, 16, 10, (120, 110, 100))  # donkey
            oval(draw, cx + 24, cy + 2, 8, 7, (120, 110, 100))
        elif slug == "alibaba":
            hz = sky(draw, w, h, (255, 200, 100), (180, 140, 80))
            ground(draw, w, h, hz, [(200, 170, 100), (160, 120, 60)])
            oval(draw, cx, cy + 4, 30, 24, (90, 70, 50))
            oval(draw, cx, cy + 6, 18, 16, (30, 20, 15))
            for i in range(8):
                oval(draw, cx - 10 + (i % 4) * 6, cy + 2 + (i // 4) * 5, 3, 3, (220, 180, 40))
        elif slug == "dede-korkut":
            person(draw, cx, cy, 2, (100, 70, 40), hair=(220, 220, 220))
            oval(draw, cx, cy - 30, 9, 5, (180, 140, 80))
            rect(draw, cx + 12, cy - 4, 3, 20, (120, 80, 40))
        elif slug == "tepegoz":
            person(draw, cx, cy, 3, (100, 110, 80), skin=(160, 150, 100), hair=(60, 50, 40))
            oval(draw, cx, cy - 36, 5, 5, (220, 40, 40))  # single eye
        elif slug == "asik-garip":
            person(draw, cx, cy, 2, (80, 50, 30))
            oval(draw, cx + 14, cy + 2, 8, 10, (140, 90, 40))  # saz body
            rect(draw, cx + 18, cy - 14, 2, 16, (140, 90, 40))
        elif slug == "kirk-haramiler":
            for i in range(5):
                person(draw, 20 + i * 18, cy + (i % 2) * 4, 1, (60, 40, 40))
            oval(draw, w - 30, cy + 4, 16, 14, (50, 40, 30))
        elif slug == "simbad":
            hz = sky(draw, w, h, (100, 160, 220), (200, 230, 255))
            ground(draw, w, h, hz, [(20, 80, 140), (10, 40, 90)])
            # ship
            oval(draw, cx, cy + 10, 36, 10, (120, 80, 40))
            rect(draw, cx - 2, cy - 18, 4, 28, (100, 70, 30))
            triangle(draw, [(cx, cy - 18), (cx + 22, cy - 4), (cx, cy + 2)], (240, 240, 245))
        elif slug == "alaaddin-saray":
            hz = sky(draw, w, h, (255, 180, 90), (120, 160, 220))
            ground(draw, w, h, hz, [(210, 170, 90), (170, 120, 60)])
            castle(draw, cx - 40, cy - 6, 80, 50, wall=(220, 200, 140), roof=(180, 60, 60))
            oval(draw, cx, cy - 20, 16, 10, (200, 160, 80))  # dome
        elif slug == "gul-bultul":
            oval(draw, cx - 8, cy + 4, 10, 12, (200, 40, 60))
            rect(draw, cx - 9, cy - 10, 3, 10, (40, 120, 40))
            oval(draw, cx + 12, cy - 6, 8, 5, (40, 40, 40))
            triangle(draw, [(cx + 8, cy - 8), (cx + 2, cy - 14), (cx + 10, cy - 4)], (30, 30, 30))
        elif slug == "karagoz":
            # stylized silhouette figures
            for dx, color in ((-16, (20, 20, 20)), (16, (180, 40, 40))):
                person(draw, cx + dx, cy, 2, color, skin=color, hair=color)
            rect(draw, 4, 4, w - 8, 6, (80, 40, 40))  # screen frame top
        elif slug == "yedi-basli":
            oval(draw, cx, cy + 8, 22, 12, (60, 120, 70))
            for i in range(7):
                hx = cx - 24 + i * 8
                oval(draw, hx, cy - 10 - (i % 3) * 4, 5, 6, (60, 120, 70))
                triangle(draw, [(hx - 2, cy - 14), (hx, cy - 22), (hx + 2, cy - 14)], (200, 60, 40))
        else:  # dev-kule
            person(draw, cx - 20, hz - 20, 4, (100, 90, 80))
            rect(draw, cx + 10, cy - 30, 24, 55, (150, 140, 130))
            triangle(draw, [(cx + 8, cy - 30), (cx + 22, cy - 50), (cx + 36, cy - 30)], (120, 40, 40))

    else:
        # Tier 7 epics + fallback panoramas
        if slug == "ejderha-savasi":
            hz = sky(draw, w, h, (80, 40, 60), (200, 120, 60))
            ground(draw, w, h, hz, [(70, 90, 50), (40, 60, 30)])
            dragon(draw, cx + 20, cy - 6, 2, (80, 40, 100), (60, 30, 80))
            person(draw, cx - 24, cy + 4, 2, (180, 180, 190))
            rect(draw, cx - 14, cy - 10, 3, 22, (200, 200, 210))
            castle(draw, 8, hz - 28, 28, 28)
        elif slug == "efsane-krallik":
            hz = sky(draw, w, h, (255, 160, 80), (100, 140, 200))
            ground(draw, w, h, hz, [(60, 120, 60), (40, 90, 40)])
            castle(draw, cx - 50, cy - 10, 100, 55)
            for i in range(6):
                rect(draw, 6 + i * 14, hz - 10, 10, 12, (140, 130, 120))
        elif slug == "binbir-gece":
            hz = sky(draw, w, h, (20, 20, 60), (60, 40, 100))
            ground(draw, w, h, hz, [(40, 30, 50), (25, 20, 35)])
            sparkles(draw, w, hz, rng, 35, [(255, 255, 220)])
            oval(draw, 16, 16, 10, 10, (240, 220, 100))  # moon
            for i in range(6):
                bx = 8 + i * 18
                rect(draw, bx, hz - 20 - (i % 3) * 8, 14, 24 + (i % 3) * 8, (100, 70, 120))
                oval(draw, bx + 7, hz - 26 - (i % 3) * 8, 8, 6, (160, 100, 60))
            rect(draw, cx - 16, cy - 8, 32, 10, (180, 40, 50))  # carpet
        elif slug == "troya-ati":
            hz = sky(draw, w, h, (180, 150, 100), (220, 200, 160))
            ground(draw, w, h, hz, [(140, 120, 80), (100, 80, 50)])
            # horse silhouette
            oval(draw, cx, cy, 28, 16, (100, 70, 40))
            oval(draw, cx + 24, cy - 8, 12, 10, (100, 70, 40))
            rect(draw, cx - 20, cy + 10, 5, 16, (100, 70, 40))
            rect(draw, cx + 8, cy + 10, 5, 16, (100, 70, 40))
            rect(draw, 4, hz - 24, w - 8, 8, (120, 110, 100))  # walls
        elif slug == "anka-yuvasi":
            hz = sky(draw, w, h, (40, 20, 60), (200, 80, 40))
            ground(draw, w, h, hz, [(80, 50, 40), (50, 30, 25)])
            triangle(draw, [(20, hz), (cx, 10), (w - 20, hz)], (90, 60, 45))
            oval(draw, cx, cy - 10, 20, 12, (220, 60, 40))
            for side in (-1, 1):
                triangle(draw, [(cx, cy - 10), (cx + side * 30, cy - 28), (cx + side * 6, cy)], (255, 140, 40))
            sparkles(draw, w, h, rng, 20, [(255, 200, 80)])
        elif slug == "buyulu-savas":
            hz = sky(draw, w, h, (60, 30, 80), (160, 60, 40))
            ground(draw, w, h, hz, [(50, 70, 40), (30, 50, 30)])
            for i in range(4):
                person(draw, 16 + i * 16, cy + 4, 1, (160, 160, 170))
            dragon(draw, cx + 30, cy - 4, 2, (100, 40, 120))
            sparkles(draw, w, h // 2, rng, 15, [(120, 200, 255), (255, 120, 80)])
        elif slug == "efsane-liman":
            hz = sky(draw, w, h, (255, 160, 80), (80, 120, 180))
            ground(draw, w, h, hz, [(20, 70, 130), (10, 40, 80)])
            for i in range(3):
                oval(draw, 20 + i * 30, cy + 8, 18, 6, (120, 80, 40))
                rect(draw, 20 + i * 30, cy - 10, 3, 18, (100, 70, 30))
            for i in range(4):
                rect(draw, w - 40 + (i % 2) * 12, hz - 18 - i * 4, 10, 16, (150, 140, 130))
        elif slug == "peri-diyari":
            hz = sky(draw, w, h, (160, 100, 220), (255, 200, 240))
            ground(draw, w, h, hz, [(80, 180, 140), (50, 140, 100)])
            castle(draw, cx - 40, cy - 8, 80, 48, wall=(240, 220, 255), roof=(255, 120, 180))
            for i in range(8):
                oval(draw, 8 + i * 14, hz - 4, 4, 3, (220, 100, 200))
            sparkles(draw, w, h, rng, 30, [(255, 255, 255), (255, 200, 255)])
        elif slug == "karanlik-kale":
            hz = sky(draw, w, h, (20, 15, 30), (50, 30, 50))
            ground(draw, w, h, hz, [(30, 25, 30), (15, 10, 15)])
            castle(draw, cx - 45, cy - 8, 90, 55, wall=(50, 45, 55), roof=(30, 20, 40))
            sparkles(draw, w, hz, rng, 12, [(180, 80, 80)])
        elif slug == "altin-sehir":
            hz = sky(draw, w, h, (255, 200, 80), (255, 240, 180))
            ground(draw, w, h, hz, [(200, 160, 60), (160, 120, 40)])
            for i in range(7):
                rect(draw, 6 + i * 16, hz - 16 - (i % 4) * 8, 12, 20 + (i % 4) * 8, (220, 180, 60))
                oval(draw, 12 + i * 16, hz - 22 - (i % 4) * 8, 7, 5, (240, 200, 80))
            sparkles(draw, w, h, rng, 20, [(255, 255, 200)])
        elif slug == "efsane-dag":
            hz = sky(draw, w, h, (80, 120, 200), (220, 230, 255))
            ground(draw, w, h, hz, [(60, 100, 50), (40, 70, 35)])
            triangle(draw, [(5, hz + 5), (cx - 20, 12), (cx + 40, hz + 5)], (100, 110, 120))
            triangle(draw, [(cx - 40, hz + 5), (cx + 30, 20), (w - 5, hz + 5)], (120, 130, 140))
            triangle(draw, [(cx - 10, 30), (cx - 20, 12), (cx + 5, 30)], (240, 245, 255))
            rect(draw, cx - 6, hz - 20, 12, 20, (150, 140, 130))
        elif slug == "buyulu-ada":
            hz = sky(draw, w, h, (100, 180, 255), (220, 240, 255))
            for y in range(hz - 5, h):
                draw.line((0, y, w, y), fill=(40, 120, 180))
            oval(draw, cx, cy + 6, 50, 18, (70, 150, 70))
            tree(draw, cx - 16, cy + 2, 20, 12)
            tree(draw, cx + 10, cy + 4, 16, 10)
            rect(draw, cx - 4, cy - 6, 14, 14, (180, 160, 120))
            sparkles(draw, w, hz, rng, 12, [(255, 255, 200)])
        else:  # son-efsane
            hz = sky(draw, w, h, (40, 20, 80), (255, 120, 60))
            ground(draw, w, h, hz, [(50, 80, 40), (30, 50, 25)])
            castle(draw, cx - 48, cy - 12, 96, 58, wall=(160, 150, 170), roof=(120, 40, 60))
            dragon(draw, 30, cy - 20, 1)
            person(draw, w - 30, cy + 4, 2, (200, 180, 80))
            sparkles(draw, w, h, rng, 28, [(255, 220, 120), (200, 180, 255)])

    return upscale(img)


def main() -> None:
    items = json.loads((OUT / "91-gorsel-envanteri.json").read_text(encoding="utf-8"))
    STORE_SOURCES.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for item in items:
        name = item["file"]
        if name in PREVIEW_MAP:
            img = fold_preview(PREVIEW_MAP[name])
        else:
            img = render_scene(item)
        dest_store = STORE_SOURCES / name
        dest_pkg = OUT / name
        img.save(dest_store, format="PNG", optimize=True)
        img.save(dest_pkg, format="PNG", optimize=True)
        written.append(name)
    digests = [hashlib.md5((STORE_SOURCES / n).read_bytes()).hexdigest() for n in written]
    assert len(set(digests)) == 91, f"duplicate md5: {len(set(digests))}"
    print(f"Wrote {len(written)} PNGs to {STORE_SOURCES} and {OUT}")


if __name__ == "__main__":
    main()
