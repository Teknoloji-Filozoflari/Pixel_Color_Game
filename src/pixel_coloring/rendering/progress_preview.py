"""Small progress raster: every source cell contributes, without full-size RGB copies."""

import math

import numpy as np


class ProgressPreview:
    def __init__(self, painting, width=230, height=160):
        self.painting = painting
        self.stride = max(1, math.ceil(max(painting.width / width, painting.height / height)))
        self.rgb = np.zeros(
            (math.ceil(painting.height / self.stride), math.ceil(painting.width / self.stride), 3),
            dtype=np.uint8,
        )
        palette = painting.palette.astype(np.uint16)
        gray = (palette[:, 0] * 54 + palette[:, 1] * 183 + palette[:, 2] * 19) // 256
        gray = (gray * 3 // 4 + 32).astype(np.uint8)
        self.gray_palette = np.repeat(gray[:, None], 3, axis=1)
        self.refresh()

    def remaining_cells(self):
        """Any unpainted source pixel must survive minimap downsampling."""
        p, s = self.painting, self.stride
        result = np.zeros(self.rgb.shape[:2], dtype=bool)
        starts = np.arange(0, p.width, s)
        for by in range(result.shape[0]):
            row = (~p.painted_mask[by * s:min(p.height, (by + 1) * s)]).any(axis=0)
            result[by] = np.logical_or.reduceat(row, starts)
        return result

    def refresh(self, bounds=None):
        p, s = self.painting, self.stride
        x0, y0, x1, y1 = bounds or (0, 0, p.width, p.height)
        bx0, by0 = max(0, x0 // s), max(0, y0 // s)
        bx1, by1 = min(self.rgb.shape[1], math.ceil(x1 / s)), min(self.rgb.shape[0], math.ceil(y1 / s))
        if bx0 >= bx1 or by0 >= by1:
            return
        left, right = bx0 * s, min(p.width, bx1 * s)
        starts = np.arange(0, right - left, s)
        widths = np.minimum(s, right - left - starts)
        for by in range(by0, by1):
            top, bottom = by * s, min(p.height, (by + 1) * s)
            target = p.target_map[top:bottom, left:right]
            mask = p.painted_mask[top:bottom, left:right]
            colors = self.gray_palette[target].copy()
            colors[mask] = p.palette[target[mask]]
            sums = np.add.reduceat(colors.sum(axis=0, dtype=np.uint64), starts, axis=0)
            self.rgb[by, bx0:bx1] = sums // (widths * (bottom - top))[:, None]
