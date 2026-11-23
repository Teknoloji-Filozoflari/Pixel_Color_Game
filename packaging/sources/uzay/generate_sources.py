"""Generate Uzay source PNGs: reuse accepted AI previews, fill the rest procedurally.

Procedural scenes are drawn at a low pixel grid then nearest-neighbor upscaled to
~1448×1086 (4:3) so the later .pcolor conversion keeps flat, connected color areas.
"""

from __future__ import annotations

import json
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PREVIEW_DIR = Path(
    "/cursor/stores/bc-8bf5c8a7-dcae-4c5b-a5ef-c31a5dc1f404/media/uzay-previews"
)
SOURCE_W, SOURCE_H = 1448, 1086

PREVIEW_MAP = {
    "001-ay.png": "uzay-t1-01-ay.jpg",
    "002-roket.png": "uzay-t1-02-roket.jpg",
    "003-gezegen.png": "uzay-t1-03-gezegen.jpg",
    "014-astronot.png": "uzay-t2-01-astronot.jpg",
    "015-uydu.png": "uzay-t2-02-uydu.jpg",
    "016-ufo.png": "uzay-t2-03-ufo.jpg",
    "027-dunya.png": "uzay-t3-01-dunya.jpg",
    "028-mars.png": "uzay-t3-02-mars.jpg",
    "029-istasyon.png": "uzay-t3-03-istasyon.jpg",
    "040-kuyrukluyildiz.png": "uzay-t4-01-kuyrukluyildiz.jpg",
    "041-ay-inis.png": "uzay-t4-02-ay-inis.jpg",
    "042-bulutsu.png": "uzay-t4-03-bulutsu.jpg",
    "053-saturn.png": "uzay-t5-01-saturn.jpg",
    "054-asteroit-alani.png": "uzay-t5-02-asteroit.jpg",
    "055-yabanci-gezegen.png": "uzay-t5-03-yabanci-gezegen.jpg",
    "066-hangar.png": "uzay-t6-01-hangar.jpg",
    "067-cift-yildiz.png": "uzay-t6-02-cift-yildiz.jpg",
    "068-europa.png": "uzay-t6-03-europa.jpg",
    "079-galaksi.png": "uzay-t7-01-galaksi.jpg",
    "080-yorunge-sehir.png": "uzay-t7-02-yorunge-sehir.jpg",
    "081-derin-uzay.png": "uzay-t7-03-derin-uzay.jpg",
}


def grid_for_tier(tier: int) -> tuple[int, int]:
    # Coarser grids for easy tiers → readable after quantization.
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


def starfield(draw: ImageDraw.ImageDraw, w: int, h: int, rng: random.Random, n: int, colors):
    for _ in range(n):
        x, y = rng.randrange(w), rng.randrange(h)
        c = colors[rng.randrange(len(colors))]
        draw.point((x, y), fill=c)
        if rng.random() < 0.15:
            draw.point((x + 1, y), fill=c)
            draw.point((x, y + 1), fill=c)
            draw.point((x - 1, y), fill=c)
            draw.point((x, y - 1), fill=c)


def circle(draw, cx, cy, r, fill, outline=None):
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill, outline=outline)


def banded_planet(draw, cx, cy, r, bands, rng):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if (x - cx) ** 2 + (y - cy) ** 2 <= r * r:
                t = (y - (cy - r)) / max(1, 2 * r)
                idx = min(len(bands) - 1, int(t * len(bands)))
                draw.point((x, y), fill=bands[idx])


def scene_for(item: dict) -> Image.Image:
    tier = item["tier"]
    slug = item["slug"]
    w, h = grid_for_tier(tier)
    rng = random.Random(hash((item["id"], slug, tier)) & 0xFFFFFFFF)
    img = Image.new("RGB", (w, h), (8, 12, 28))
    draw = ImageDraw.Draw(img)
    starfield(draw, w, h, rng, 8 + tier * 10, [(220, 230, 255), (255, 240, 180), (180, 200, 255)])

    cx, cy = w // 2, h // 2

    def rocket(x, y, scale=1.0):
        s = max(1, int(8 * scale))
        draw.polygon([(x, y - 2 * s), (x - s, y), (x + s, y)], fill=(220, 60, 50))
        draw.rectangle((x - s // 2, y, x + s // 2, y + 2 * s), fill=(240, 240, 245))
        draw.rectangle((x - s, y + 2 * s, x - s // 2, y + 3 * s), fill=(200, 50, 40))
        draw.rectangle((x + s // 2, y + 2 * s, x + s, y + 3 * s), fill=(200, 50, 40))
        draw.ellipse((x - s // 3, y + s // 2, x + s // 3, y + s), fill=(80, 140, 220))
        draw.polygon(
            [(x - s // 3, y + 3 * s), (x + s // 3, y + 3 * s), (x, y + 4 * s)],
            fill=(255, 180, 40),
        )

    def ship(x, y, scale=1.0, color=(180, 190, 200)):
        s = max(2, int(10 * scale))
        draw.polygon(
            [(x - 2 * s, y), (x + 2 * s, y - s // 2), (x + 2 * s, y + s // 2)],
            fill=color,
        )
        draw.rectangle((x - 2 * s, y - s // 3, x - s, y + s // 3), fill=(60, 180, 255))

    # Scene family by slug keywords / tier defaults
    if slug in ("ay", "dolunay", "hilal"):
        circle(draw, cx + 8, cy, min(w, h) // 3, (240, 220, 140))
        if slug != "dolunay":
            circle(draw, cx + 18, cy - 4, min(w, h) // 4, (8, 12, 28))
    elif slug in ("roket", "roket-firlatma"):
        rocket(cx, cy - 4, 1.2 if tier > 2 else 1.0)
        if slug == "roket-firlatma":
            draw.rectangle((0, h - 8, w, h), fill=(60, 70, 80))
            draw.rectangle((cx - 6, h - 18, cx + 6, h - 8), fill=(120, 120, 130))
    elif slug in ("gezegen", "dunya-top", "dunya", "venus", "merkur", "phobos"):
        colors = {
            "gezegen": [(40, 90, 160), (60, 140, 180), (200, 220, 230)],
            "dunya-top": [(30, 90, 180), (50, 140, 70), (220, 230, 240)],
            "dunya": [(20, 70, 160), (40, 120, 60), (230, 240, 250)],
            "venus": [(210, 170, 90), (190, 140, 70), (240, 210, 140)],
            "merkur": [(120, 110, 100), (90, 80, 70), (160, 150, 140)],
            "phobos": [(100, 90, 85), (70, 65, 60), (140, 130, 120)],
        }[slug]
        r = min(w, h) // 3 + tier
        banded_planet(draw, cx, cy, r, colors * 3, rng)
        if slug == "gezegen":
            draw.ellipse((cx - r - 8, cy - 4, cx + r + 8, cy + 4), outline=(180, 220, 255))
    elif slug == "yildiz":
        for i, col in enumerate([(255, 240, 160), (255, 220, 80), (255, 180, 40)]):
            r = 18 - i * 5
            circle(draw, cx, cy, r, col)
        for ang in range(0, 360, 45):
            rad = math.radians(ang)
            draw.line(
                (cx, cy, cx + int(math.cos(rad) * 28), cy + int(math.sin(rad) * 28)),
                fill=(255, 230, 120),
                width=2,
            )
    elif slug in ("asteroit", "asteroit-alani", "kale"):
        for _ in range(4 + tier * 2):
            x, y = rng.randrange(w), rng.randrange(h)
            r = rng.randint(2, 6 + tier)
            circle(draw, x, y, r, (90 + rng.randrange(40), 70, 60))
        if slug == "kale":
            draw.rectangle((cx - 20, cy - 10, cx + 20, cy + 18), fill=(140, 150, 160))
            draw.rectangle((cx - 8, cy - 22, cx + 8, cy - 10), fill=(100, 200, 255))
        if slug == "asteroit-alani":
            ship(cx, cy, 0.8)
    elif slug in ("kask", "astronot"):
        circle(draw, cx, cy - 4, 18, (230, 230, 240))
        circle(draw, cx, cy - 4, 12, (40, 80, 140))
        circle(draw, cx - 3, cy - 7, 3, (200, 220, 255))
        if slug == "astronot":
            draw.rectangle((cx - 14, cy + 12, cx + 14, cy + 28), fill=(220, 220, 230))
    elif slug in ("teleskop", "teleskop-dizisi", "hubble"):
        draw.rectangle((cx - 4, cy - 20, cx + 4, cy + 20), fill=(160, 170, 180))
        circle(draw, cx, cy - 8, 10, (80, 90, 100))
        circle(draw, cx, cy - 8, 6, (40, 60, 120))
        if slug == "teleskop-dizisi":
            for dx in (-30, 30):
                draw.rectangle((cx + dx - 3, cy - 12, cx + dx + 3, cy + 12), fill=(150, 160, 170))
    elif slug in ("kuyruklu", "kuyrukluyildiz", "komet-surusu"):
        n = 1 if slug != "komet-surusu" else 4
        for i in range(n):
            x = 20 + i * 20
            y = 20 + i * 12
            circle(draw, x, y, 4, (220, 240, 255))
            draw.polygon([(x, y), (x - 30, y + 8), (x - 28, y - 4)], fill=(180, 80, 200))
        if slug == "kuyrukluyildiz":
            banded_planet(draw, w - 30, h - 30, 22, [(80, 40, 120), (140, 80, 180), (60, 30, 90)], rng)
    elif slug in ("uydu-cana", "uydu"):
        draw.ellipse((cx - 16, cy - 10, cx + 4, cy + 10), outline=(200, 210, 220), width=2)
        draw.rectangle((cx + 2, cy - 4, cx + 18, cy + 4), fill=(160, 170, 180))
        if slug == "uydu":
            draw.rectangle((cx - 28, cy - 2, cx - 16, cy + 2), fill=(40, 100, 200))
            draw.rectangle((cx + 18, cy - 2, cx + 30, cy + 2), fill=(40, 100, 200))
            draw.arc((10, h - 40, w - 10, h + 40), 200, 340, fill=(40, 120, 200), width=3)
    elif slug == "yildiz-kaymasi":
        draw.line((10, 20, cx, cy), fill=(255, 240, 180), width=2)
        circle(draw, cx, cy, 3, (255, 255, 220))
    elif slug in ("uzayli", "alien-craft", "ana-gemi"):
        circle(draw, cx, cy, 10 if slug == "uzayli" else 18, (80, 220, 120))
        if slug != "uzayli":
            draw.ellipse((cx - 28, cy - 6, cx + 28, cy + 10), fill=(120, 140, 160))
            for i in range(-2, 3):
                circle(draw, cx + i * 10, cy + 8, 2, (80, 255, 200))
    elif slug == "ufo":
        draw.ellipse((cx - 28, cy - 8, cx + 28, cy + 8), fill=(180, 190, 200))
        circle(draw, cx, cy - 8, 10, (140, 220, 255))
        draw.polygon([(cx - 10, cy + 8), (cx + 10, cy + 8), (cx, cy + 28)], fill=(80, 255, 220))
        draw.rectangle((0, h - 16, w, h), fill=(90, 95, 100))
    elif slug in ("mekik", "mekik-inis"):
        ship(cx, cy, 1.3, (220, 220, 230))
        if slug == "mekik-inis":
            draw.rectangle((0, h - 20, w, h), fill=(70, 110, 70))
    elif slug in ("gezgin", "mars", "mars-kanyon", "mars-harabe", "terraforming"):
        draw.rectangle((0, h // 2, w, h), fill=(180, 90, 50))
        for _ in range(20):
            draw.point((rng.randrange(w), rng.randrange(h // 2, h)), fill=(140, 60, 30))
        draw.rectangle((0, 0, w, h // 2), fill=(230, 150, 110))
        if slug in ("gezgin", "mars"):
            draw.rectangle((cx - 10, cy, cx + 10, cy + 8), fill=(40, 40, 45))
            for dx in (-8, 8):
                circle(draw, cx + dx, cy + 10, 3, (20, 20, 25))
        if slug == "mars-harabe":
            draw.rectangle((cx - 18, cy - 8, cx + 18, cy + 12), fill=(120, 80, 60))
        if slug == "terraforming":
            draw.ellipse((cx - 20, cy - 20, cx + 20, cy), fill=(60, 140, 200))
    elif slug in ("kapsul", "ay-inis"):
        draw.rectangle((0, h - 22, w, h), fill=(120, 120, 130))
        for _ in range(12):
            circle(draw, rng.randrange(w), h - rng.randint(4, 18), rng.randint(2, 5), (90, 90, 100))
        draw.polygon([(cx, cy - 18), (cx - 14, cy + 8), (cx + 14, cy + 8)], fill=(200, 200, 210))
        draw.rectangle((cx - 10, cy + 8, cx + 10, cy + 18), fill=(180, 140, 60))
        circle(draw, w - 24, 24, 14, (40, 100, 180))
    elif slug in ("gunes-panel",):
        draw.rectangle((cx - 30, cy - 8, cx - 8, cy + 8), fill=(30, 80, 180))
        draw.rectangle((cx + 8, cy - 8, cx + 30, cy + 8), fill=(30, 80, 180))
        draw.rectangle((cx - 6, cy - 6, cx + 6, cy + 6), fill=(180, 180, 190))
    elif slug in ("tether",):
        circle(draw, cx - 20, cy, 10, (230, 230, 240))
        draw.line((cx - 10, cy, cx + 30, cy + 10), fill=(200, 200, 210), width=1)
        draw.rectangle((cx + 28, cy + 4, cx + 40, cy + 16), fill=(160, 170, 180))
    elif slug in ("sonde",):
        ship(cx, cy, 0.7, (200, 180, 100))
        draw.line((cx, cy, cx + 20, cy - 15), fill=(180, 180, 190))
        circle(draw, cx + 22, cy - 16, 4, (220, 220, 230))
    elif slug in ("buz-kiyisi", "buz-ayi", "europa"):
        draw.rectangle((0, h // 2, w, h), fill=(180, 210, 230))
        for x in range(0, w, 8):
            draw.line((x, h // 2, x + 4, h), fill=(140, 180, 210))
        if slug == "europa":
            banded_planet(draw, 30, 28, 22, [(200, 140, 80), (160, 100, 50), (220, 180, 120)], rng)
            for x in (cx - 20, cx, cx + 20):
                draw.polygon([(x, h // 2), (x - 4, 20), (x + 4, 20)], fill=(230, 245, 255))
    elif slug in ("istasyon", "dock", "halka-istasyon", "yörünge-halka", "yorunge-halka"):
        draw.rectangle((cx - 30, cy - 4, cx + 30, cy + 4), fill=(200, 200, 210))
        for dx in (-24, -8, 8, 24):
            draw.rectangle((cx + dx - 4, cy - 10, cx + dx + 4, cy + 10), fill=(40, 100, 200))
        circle(draw, cx, cy, 6, (230, 230, 240))
        if "halka" in slug or slug == "halka-istasyon":
            draw.ellipse((cx - 35, cy - 18, cx + 35, cy + 18), outline=(180, 190, 200), width=2)
        draw.arc((10, h - 35, w - 10, h + 40), 200, 340, fill=(40, 120, 200), width=4)
    elif slug in ("ay-us", "kubbe", "ay-metropol"):
        draw.rectangle((0, h - 24, w, h), fill=(130, 130, 140))
        circle(draw, cx, cy + 4, 18, (160, 200, 230))
        draw.rectangle((cx - 20, cy + 4, cx + 20, cy + 20), fill=(180, 180, 190))
        if slug == "ay-metropol":
            for i in range(-2, 3):
                draw.rectangle((cx + i * 12 - 4, cy - 10, cx + i * 12 + 4, cy + 8), fill=(100, 180, 255))
    elif slug in ("sera",):
        draw.polygon([(cx - 24, cy + 10), (cx, cy - 16), (cx + 24, cy + 10)], fill=(80, 200, 120))
        draw.rectangle((cx - 20, cy + 10, cx + 20, cy + 18), fill=(160, 170, 180))
    elif slug in ("maden",):
        circle(draw, cx, cy, 22, (100, 90, 80))
        draw.rectangle((cx - 6, cy - 6, cx + 6, cy + 6), fill=(255, 180, 40))
        ship(cx + 28, cy - 16, 0.5)
    elif slug == "elevator":
        draw.line((cx, 4, cx, h - 4), fill=(200, 200, 210), width=2)
        draw.rectangle((cx - 8, cy - 8, cx + 8, cy + 8), fill=(160, 170, 190))
        draw.arc((5, h - 30, w - 5, h + 50), 210, 330, fill=(40, 100, 180), width=3)
    elif slug in ("firtina", "gunes-patlama", "plazma"):
        circle(draw, w - 20, 20, 18, (255, 200, 60))
        for i in range(8):
            ang = math.radians(rng.randrange(360))
            draw.line(
                (w - 20, 20, w - 20 + int(math.cos(ang) * 40), 20 + int(math.sin(ang) * 40)),
                fill=(255, 120, 40),
                width=2,
            )
        ship(cx - 10, cy + 10, 0.7)
    elif slug in ("bulutsu", "sutunlar", "derin-uzay", "galaksi-kenari", "kosmik-ag", "filo-bulutsu", "supernova", "quazar"):
        for i in range(6 + tier):
            x0, y0 = rng.randrange(w), rng.randrange(h)
            col = [(180, 40, 160), (40, 180, 180), (255, 120, 40), (120, 60, 200)][i % 4]
            circle(draw, x0, y0, rng.randint(8, 20), col)
        if slug == "galaksi" or "galaksi" in slug:
            for a in range(0, 360, 8):
                rad = math.radians(a)
                rr = 10 + a / 12
                circle(draw, cx + int(math.cos(rad) * rr), cy + int(math.sin(rad) * rr), 2, (255, 180, 80))
        if slug in ("filo-bulutsu", "filo"):
            for i in range(5):
                ship(20 + i * 15, cy + i * 3, 0.4 + i * 0.05)
        if slug == "quazar":
            circle(draw, cx, cy, 8, (255, 255, 220))
            draw.rectangle((cx - 2, 0, cx + 2, h), fill=(200, 220, 255))
    elif slug in ("jupiter", "saturn", "saturn-yaklas"):
        bands = [(180, 140, 90), (200, 160, 110), (160, 110, 70), (220, 180, 130)]
        r = min(w, h) // 3 + 4
        banded_planet(draw, cx, cy, r, bands * 2, rng)
        if "saturn" in slug:
            draw.ellipse((cx - r - 12, cy - 6, cx + r + 12, cy + 6), outline=(220, 220, 240), width=2)
            for i, rr in enumerate((6, 10, 14)):
                circle(draw, cx - r - 10, 16 + i * 12, 4, (180, 180, 190))
    elif slug in ("kara-delik",):
        circle(draw, cx, cy, 14, (5, 5, 10))
        draw.ellipse((cx - 28, cy - 8, cx + 28, cy + 8), outline=(255, 160, 60), width=3)
        draw.ellipse((cx - 34, cy - 10, cx + 34, cy + 10), outline=(255, 100, 40), width=1)
    elif slug in ("takimyildiz",):
        pts = [(20, 30), (40, 20), (60, 35), (50, 50), (25, 55)]
        for a, b in zip(pts, pts[1:]):
            draw.line((a, b), fill=(200, 210, 255))
        for p in pts:
            circle(draw, p[0], p[1], 2, (255, 255, 220))
    elif slug in ("yanardag-ay",):
        draw.rectangle((0, h // 2, w, h), fill=(80, 70, 70))
        draw.polygon([(cx - 20, h // 2), (cx, cy - 10), (cx + 20, h // 2)], fill=(100, 80, 70))
        draw.polygon([(cx - 4, cy - 10), (cx + 4, cy - 10), (cx, cy - 28)], fill=(255, 100, 40))
    elif slug in ("yabanci-gezegen", "uzayli-harabe", "kristal-magara"):
        draw.rectangle((0, 0, w, h // 2), fill=(120, 60, 160))
        draw.rectangle((0, h // 2, w, h), fill=(40, 120, 100))
        circle(draw, 20, 18, 8, (255, 180, 60))
        circle(draw, 40, 22, 5, (255, 220, 120))
        draw.rectangle((cx - 6, cy - 30, cx + 6, cy + 10), fill=(60, 40, 30))
        circle(draw, cx, cy - 28, 16, (40, 220, 180))
        if slug == "uzayli-harabe":
            draw.rectangle((cx - 24, cy + 4, cx + 24, cy + 18), fill=(100, 90, 120))
        if slug == "kristal-magara":
            for i in range(5):
                draw.polygon(
                    [(20 + i * 20, h - 5), (25 + i * 20, h - 30), (30 + i * 20, h - 5)],
                    fill=(120, 200, 255),
                )
    elif slug in ("cift-gezegen", "cift-yildiz"):
        circle(draw, cx - 18, cy, 16, (255, 160, 60) if "yildiz" in slug else (80, 140, 200))
        circle(draw, cx + 20, cy + 4, 12, (80, 140, 255) if "yildiz" in slug else (200, 100, 80))
        if slug == "cift-yildiz":
            draw.rectangle((cx - 4, cy + 20, cx + 30, cy + 26), fill=(160, 170, 180))
            circle(draw, cx + 14, cy + 22, 5, (100, 200, 255))
    elif slug in ("hangar", "tersane"):
        draw.rectangle((0, 0, w, h), fill=(40, 45, 55))
        draw.rectangle((10, 10, w - 10, h - 10), fill=(55, 60, 70))
        draw.rectangle((20, 20, w - 20, h // 2), fill=(8, 12, 28))
        starfield(draw, w, h // 2, rng, 30, [(220, 230, 255)])
        for i in range(3):
            ship(30 + i * 28, h - 25, 0.6)
        draw.rectangle((8, h - 14, w - 8, h - 4), fill=(200, 180, 40))
    elif slug in ("dyson", "megayapi", "warp-agi", "solucan"):
        circle(draw, cx, cy, 12, (255, 200, 80))
        for a in range(0, 360, 12):
            rad = math.radians(a)
            x = cx + int(math.cos(rad) * 28)
            y = cy + int(math.sin(rad) * 18)
            circle(draw, x, y, 2, (180, 190, 200))
        if slug == "solucan":
            draw.ellipse((cx - 20, cy - 12, cx + 20, cy + 12), outline=(120, 80, 255), width=3)
        if slug == "warp-agi":
            for dx, dy in ((-30, -20), (30, -15), (-25, 20), (28, 18)):
                circle(draw, cx + dx, cy + dy, 4, (100, 200, 255))
                draw.line((cx, cy, cx + dx, cy + dy), fill=(80, 160, 220))
    elif slug in ("galaksi",):
        for a in range(0, 720, 6):
            rad = math.radians(a)
            rr = 4 + a / 18
            col = (255, 180, 80) if a % 18 < 9 else (200, 80, 180)
            circle(draw, cx + int(math.cos(rad) * rr / 3), cy + int(math.sin(rad) * rr / 4), 2, col)
        for i in range(6):
            ship(10 + i * 12, h - 20 - i, 0.35)
    elif slug in ("yorunge-sehir", "gezegen-sehir"):
        banded_planet(draw, cx, cy, 28, [(20, 80, 160), (40, 120, 70), (30, 40, 80)], rng)
        draw.ellipse((cx - 40, cy - 12, cx + 40, cy + 12), outline=(200, 210, 220), width=2)
        draw.ellipse((cx - 48, cy - 16, cx + 48, cy + 16), outline=(100, 180, 255), width=1)
        for a in range(0, 360, 40):
            rad = math.radians(a)
            circle(draw, cx + int(math.cos(rad) * 40), cy + int(math.sin(rad) * 12), 2, (255, 200, 80))
    elif slug in ("coklu-sistem",):
        circle(draw, 20, 20, 10, (255, 200, 60))
        for i, (px, py, r, col) in enumerate(
            [(50, 40, 8, (80, 140, 200)), (70, 70, 6, (200, 100, 80)), (40, 80, 5, (160, 160, 180))]
        ):
            circle(draw, px, py, r, col)
    elif slug in ("galaktik-cekirdek",):
        for r, col in ((30, (255, 220, 120)), (20, (255, 160, 60)), (10, (255, 255, 220))):
            circle(draw, cx, cy, r, col)
        for a in range(0, 360, 10):
            rad = math.radians(a)
            draw.point((cx + int(math.cos(rad) * 40), cy + int(math.sin(rad) * 25)), fill=(255, 100, 180))
    elif slug in ("gemisi", "katedral", "canli-asteroit"):
        draw.polygon([(cx - 30, cy + 20), (cx, cy - 25), (cx + 30, cy + 20)], fill=(180, 190, 210))
        draw.rectangle((cx - 8, cy - 5, cx + 8, cy + 15), fill=(100, 200, 255))
        if slug == "katedral":
            draw.polygon([(cx - 6, cy - 25), (cx, cy - 40), (cx + 6, cy - 25)], fill=(220, 230, 240))
        if slug == "canli-asteroit":
            circle(draw, cx, cy, 22, (90, 80, 70))
            for i in range(6):
                circle(draw, cx - 15 + i * 6, cy - 5, 2, (80, 255, 180))
    else:
        # Fallback distinctive scene
        banded_planet(draw, cx, cy, 18 + tier, [(40, 80, 160), (80, 40, 120), (200, 180, 80)], rng)
        ship(cx - 25, cy + 15, 0.6 + tier * 0.05)

    # Extra ships / detail for higher tiers
    if tier >= 5 and slug not in ("hangar", "tersane"):
        for i in range(tier - 4):
            ship(10 + i * 14, h - 12 - i * 2, 0.35)

    return upscale(img)


def copy_preview(src_name: str, dest: Path) -> None:
    src = PREVIEW_DIR / src_name
    with Image.open(src) as image:
        rgb = image.convert("RGB")
        # Fit into 4:3 canvas
        fitted = Image.new("RGB", (SOURCE_W, SOURCE_H), (8, 12, 28))
        scale = min(SOURCE_W / rgb.width, SOURCE_H / rgb.height)
        nw, nh = max(1, round(rgb.width * scale)), max(1, round(rgb.height * scale))
        resized = rgb.resize((nw, nh), Image.Resampling.BOX)
        fitted.paste(resized, ((SOURCE_W - nw) // 2, (SOURCE_H - nh) // 2))
        fitted.save(dest, format="PNG", optimize=True)


def main() -> None:
    items = json.loads((OUT / "91-gorsel-envanteri.json").read_text(encoding="utf-8"))
    assert len(items) == 91
    for item in items:
        dest = OUT / item["file"]
        preview = PREVIEW_MAP.get(item["file"])
        if preview and (PREVIEW_DIR / preview).is_file():
            copy_preview(preview, dest)
            kind = "preview"
        else:
            scene_for(item).save(dest, format="PNG", optimize=True)
            kind = "procedural"
        print(f"{item['id']}: {dest.name} ({kind})")
    print(f"Wrote {len(items)} sources to {OUT}")


if __name__ == "__main__":
    main()
