from collections import OrderedDict

import numpy as np
from PySide6.QtGui import QImage

TILE_SIZE = 256


def rgb_image(rgb):
    rgb = np.ascontiguousarray(rgb, dtype=np.uint8)
    h, w, _ = rgb.shape
    return QImage(rgb.data, w, h, rgb.strides[0], QImage.Format.Format_RGB888).copy()


class TileCache:
    def __init__(self, painting, max_bytes=64 * 1024 * 1024):
        self.painting = painting
        self.tiles = OrderedDict()
        self.max_bytes = max_bytes
        self.bytes = 0
        self.selected = 0
        self.highlight = 0.75
        self.highlight_color = (0, 255, 0)

    def clear(self):
        self.tiles.clear()
        self.bytes = 0

    def invalidate(self, x, y):
        old = self.tiles.pop((x // TILE_SIZE, y // TILE_SIZE), None)
        if old is not None:
            self.bytes -= old.sizeInBytes()

    def invalidate_indices(self, indices):
        p = self.painting
        keys = np.unique((indices // p.width // TILE_SIZE) * 65536 + indices % p.width // TILE_SIZE)
        for key in keys:
            self.invalidate(int(key % 65536) * TILE_SIZE, int(key // 65536) * TILE_SIZE)

    def get(self, tx, ty):
        key = tx, ty
        if key in self.tiles:
            self.tiles.move_to_end(key)
            return self.tiles[key]
        p = self.painting
        x, y = tx * TILE_SIZE, ty * TILE_SIZE
        target = p.target_map[y : y + TILE_SIZE, x : x + TILE_SIZE]
        mask = p.painted_mask[y : y + TILE_SIZE, x : x + TILE_SIZE]
        rgb = p.palette[target].copy()
        gray = (rgb.astype(np.float32).mean(axis=2) * 0.13 + 183).astype(np.uint8)
        rgb[~mask] = np.repeat(gray[:, :, None], 3, axis=2)[~mask]
        match = (target == self.selected) & ~mask
        strength = self.highlight
        rgb[match] = np.array(self.highlight_color) * strength + rgb[match] * (1 - strength)
        image = rgb_image(rgb)
        self.tiles[key] = image
        self.bytes += image.sizeInBytes()
        while self.bytes > self.max_bytes and len(self.tiles) > 1:
            _, old = self.tiles.popitem(last=False)
            self.bytes -= old.sizeInBytes()
        return image
