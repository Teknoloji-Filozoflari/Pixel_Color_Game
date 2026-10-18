"""Sequential conversion keeps large batches from multiplying image memory."""

import uuid
from dataclasses import dataclass, field
from pathlib import Path

from .image_importer import convert_image, load_image, validate_dimensions
from .level_writer import read_level, write_level

EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp', '.pcolor'}


@dataclass
class BatchResult:
    imported: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    cancelled: bool = False


def folder_images(directory):
    return sorted((p for p in Path(directory).iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS),
                  key=lambda p: p.name.casefold())


def import_batch(paths, bounds, colors, destination, database, cancelled, progress):
    validate_dimensions(*bounds)
    result = BatchResult()
    for index, source in enumerate(paths):
        if cancelled.is_set():
            result.cancelled = True
            break
        path = Path(source)
        dest = None
        try:
            if path.suffix.lower() == '.pcolor':
                painting = read_level(path)
                validate_dimensions(painting.width, painting.height)
                painting.id = str(uuid.uuid4())
            else:
                image = load_image(path)
                scale = min(1, bounds[0] / image.width, bounds[1] / image.height)
                size = max(1, int(image.width * scale)), max(1, int(image.height * scale))
                painting = convert_image(image, path.stem, colors, size)
            dest = Path(destination) / (painting.id + '.pcolor')
            write_level(painting, dest)
            database.register(painting, dest)
            result.imported.append(painting.id)
        except Exception as exc:
            if dest is not None:
                dest.unlink(missing_ok=True)
            result.errors.append((path.name, str(exc)))
        progress.put((index + 1, path.name))
    return result
