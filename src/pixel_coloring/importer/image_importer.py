import uuid

import numpy as np
from PIL import Image, ImageOps

from ..core.painting import Painting


def validate_dimensions(width, height):
    if width > 1920 or height > 1080:
        raise ValueError(f"Resim en fazla 1920 × 1080 piksel olabilir. Seçilen resim: {width} × {height}.")


def automatic_color_count(width, height):
    """Interpolate the collection's pixel/color ranges, capped at 60 colors."""
    cells = width * height
    ranges = (
        (1500, 6000, 10, 15), (6000, 14000, 15, 20),
        (14000, 28000, 20, 25), (28000, 45000, 25, 30),
        (45000, 70000, 30, 35), (70000, 120000, 35, 40),
        (120000, 2073600, 40, 60),
    )
    for low, high, minimum, maximum in ranges:
        if cells <= high:
            fraction = max(0, cells - low) / (high - low)
            return minimum + int(fraction * (maximum - minimum) + 0.5)
    return 60


def import_image(path, colors=None):
    if colors is not None and not 2 <= colors <= 256:
        raise ValueError("Renk sayısı geçersiz")
    with Image.open(path) as source:
        width, height = source.size
        if source.getexif().get(274) in (5, 6, 7, 8):
            width, height = height, width
        validate_dimensions(width, height)
        if colors is None:
            colors = automatic_color_count(width, height)
        source = ImageOps.exif_transpose(source)
        rgba = source.convert("RGBA")
        rgb = Image.new("RGB", rgba.size, "#FFFFFF")
        rgb.paste(rgba, mask=rgba.getchannel("A"))
        quantized = rgb.quantize(colors=colors, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        raw = np.asarray(quantized)
        used, target = np.unique(raw, return_inverse=True)
        palette = np.array(quantized.getpalette(), dtype=np.uint8).reshape(-1, 3)[used]
        return Painting(str(uuid.uuid4()), path.stem, palette, target.reshape(raw.shape), "İçe aktarılan")
