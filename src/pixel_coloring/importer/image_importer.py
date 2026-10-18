import uuid

from PIL import Image, ImageOps

from ..core.painting import Painting
from .quantization import quantize_image


def validate_dimensions(width, height):
    if width < 1 or height < 1:
        raise ValueError('Resim boyutları sıfırdan büyük olmalı.')
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


def load_image(path):
    """Orient the source and composite transparency before any resizing."""
    with Image.open(path) as source:
        source = ImageOps.exif_transpose(source)
        rgba = source.convert('RGBA')
        rgb = Image.new('RGB', rgba.size, '#FFFFFF')
        rgb.paste(rgba, mask=rgba.getchannel('A'))
        return rgb


def convert_image(image, title, colors=None, size=None):
    if colors is not None and not 2 <= colors <= 256:
        raise ValueError("Renk sayısı geçersiz")
    width, height = size or image.size
    validate_dimensions(width, height)
    if (width, height) != image.size:
        image = image.resize((width, height), Image.Resampling.LANCZOS)
    if colors is None:
        colors = automatic_color_count(width, height)
    palette, target = quantize_image(image, colors)
    return Painting(str(uuid.uuid4()), title, palette, target, 'İçe aktarılan')


def import_image(path, colors=None, size=None):
    return convert_image(load_image(path), path.stem, colors, size)
