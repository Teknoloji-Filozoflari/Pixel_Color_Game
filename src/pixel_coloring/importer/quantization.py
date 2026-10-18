"""Perceptual, deterministic palettes without dithering or extra dependencies.

Oklab transforms: https://bottosson.github.io/posts/oklab/ (public-domain formulas).
Training uses a bounded RGB histogram; final assignments use every original
pixel, not a resized thumbnail. Frequency tempering leaves room for accents.
"""

import numpy as np

_RGB_TO_LMS = np.array([
    [.4122214708, .5363325363, .0514459929],
    [.2119034982, .6806995451, .1073969566],
    [.0883024619, .2817188376, .6299787005],
], dtype=np.float32)
_LMS_TO_LAB = np.array([
    [.2104542553, .7936177850, -.0040720468],
    [1.9779984951, -2.4285922050, .4505937099],
    [.0259040371, .7827717662, -.8086757660],
], dtype=np.float32)


def rgb_to_oklab(rgb):
    values = np.asarray(rgb, dtype=np.float32) / 255
    linear = np.where(values <= .04045, values / 12.92, ((values + .055) / 1.055) ** 2.4)
    lms = np.einsum('...j,ij->...i', linear, _RGB_TO_LMS)
    return np.einsum('...j,ij->...i', np.cbrt(lms), _LMS_TO_LAB)


def oklab_to_rgb(lab):
    lightness, a, b = np.moveaxis(lab, -1, 0)
    long = (lightness + .3963377774 * a + .2158037573 * b) ** 3
    medium = (lightness - .1055613458 * a - .0638541728 * b) ** 3
    short = (lightness - .0894841775 * a - 1.2914855480 * b) ** 3
    linear = np.stack((
        4.0767416621 * long - 3.3077115913 * medium + .2309699292 * short,
        -1.2684380046 * long + 2.6097574011 * medium - .3413193965 * short,
        -.0041960863 * long - .7034186147 * medium + 1.7076147010 * short,
    ), axis=-1)
    linear = np.maximum(linear, 0)
    srgb = np.where(linear <= .0031308, 12.92 * linear, 1.055 * linear ** (1 / 2.4) - .055)
    return np.rint(np.clip(srgb, 0, 1) * 255).astype(np.uint8)


def _codes(rgb):
    values = rgb.astype(np.uint32)
    return (values[:, 0] << 16) | (values[:, 1] << 8) | values[:, 2]


def _histogram(pixels, colors):
    # At most 32,768 representatives, including even one-pixel accents.
    coarse = pixels.astype(np.uint16) >> 3
    bins = ((coarse[:, 0] << 10) | (coarse[:, 1] << 5) | coarse[:, 2]).astype(np.int32)
    counts = np.bincount(bins, minlength=32768)
    used = counts > 0
    if used.sum() < colors:
        # Near-monochrome images can have many meaningful shades in one bin.
        # There are fewer than colors * 512 unique RGB values in this case.
        keys, counts = np.unique(_codes(pixels), return_counts=True)
        rgb = np.stack((keys >> 16, (keys >> 8) & 255, keys & 255), axis=1)
        return rgb.astype(np.float32), counts
    means = np.stack([
        np.bincount(bins, weights=pixels[:, channel], minlength=32768)[used] / counts[used]
        for channel in range(3)
    ], axis=1)
    return means.astype(np.float32), counts[used]


def _nearest(points, centers):
    """Bound working memory even for full HD and 256-color imports."""
    labels = np.empty(len(points), dtype=np.int32)
    errors = np.empty(len(points), dtype=np.float32)
    for start in range(0, len(points), 4096):
        block = points[start:start + 4096]
        distances = (block[:, 0, None] - centers[:, 0]) ** 2
        distances += (block[:, 1, None] - centers[:, 1]) ** 2
        distances += (block[:, 2, None] - centers[:, 2]) ** 2
        nearest = distances.argmin(axis=1)
        labels[start:start + len(block)] = nearest
        errors[start:start + len(block)] = distances[np.arange(len(block)), nearest]
    return labels, errors


def _fit_palette(points, counts, colors):
    # Unlike population-only splits, distant accent colors get their own seeds.
    # Counts still matter; tempering only reduces dominance by large flat areas.
    weights = counts.astype(np.float64) ** .85
    centers = [points[counts.argmax()]]
    distances = np.full(len(points), np.inf, dtype=np.float32)
    for _ in range(1, min(colors, len(points))):
        distances = np.minimum(distances, ((points - centers[-1]) ** 2).sum(axis=1))
        centers.append(points[(distances * weights).argmax()])
    centers = np.array(centers)
    for _ in range(20):
        labels, errors = _nearest(points, centers)
        totals = np.bincount(labels, weights=weights, minlength=len(centers))
        occupied = totals > 0
        updated = centers.copy()
        for channel in range(3):
            sums = np.bincount(labels, weights=weights * points[:, channel], minlength=len(centers))
            updated[occupied, channel] = sums[occupied] / totals[occupied]
        for empty in np.flatnonzero(~occupied):
            worst = (errors * weights).argmax()
            updated[empty] = points[worst]
            errors[worst] = 0
        if np.max(np.abs(updated - centers)) < .0001:
            centers = updated
            break
        centers = updated
    return np.unique(oklab_to_rgb(centers), axis=0)


def quantize_image(image, colors):
    """Return a compact RGB palette and an exact-size, dither-free index map."""
    if not 2 <= colors <= 256:
        raise ValueError('Renk sayısı geçersiz')
    image = image.convert('RGB')
    pixels = np.asarray(image).reshape(-1, 3)
    existing = image.getcolors(maxcolors=colors)
    if existing is not None:
        palette = np.array(sorted(color for count, color in existing), dtype=np.uint8)
        target = np.searchsorted(_codes(palette), _codes(pixels)).astype(np.uint8)
    else:
        representatives, counts = _histogram(pixels, colors)
        palette = _fit_palette(rgb_to_oklab(representatives), counts, colors)
        centers = rgb_to_oklab(palette)
        target = np.empty(len(pixels), dtype=np.uint8)
        for start in range(0, len(pixels), 65536):
            block = rgb_to_oklab(pixels[start:start + 65536])
            target[start:start + len(block)] = _nearest(block, centers)[0]
        used, target = np.unique(target, return_inverse=True)
        palette = palette[used]
    return palette, target.reshape(image.height, image.width).astype(np.uint8)
