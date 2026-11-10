from enum import Enum, auto

import numpy as np

from .painting import Painting


class PaintResult(Enum):
    CORRECT = auto()
    WRONG = auto()
    ALREADY_PAINTED = auto()
    OUT_OF_BOUNDS = auto()


class PaintingEngine:
    def __init__(self, painting: Painting):
        self.painting = painting
        self.stroke_changed = False

    def paint_cell(self, x, y, selected_color_id):
        p = self.painting
        if not (0 <= x < p.width and 0 <= y < p.height):
            return PaintResult.OUT_OF_BOUNDS
        if p.painted_mask[y, x]:
            return PaintResult.ALREADY_PAINTED
        if p.target_map[y, x] != selected_color_id:
            return PaintResult.WRONG
        p.painted_mask[y, x] = True
        p.counts[selected_color_id] += 1
        self.stroke_changed = True
        return PaintResult.CORRECT

    def end_stroke(self):
        if not self.stroke_changed:
            return False
        self.stroke_changed = False
        return True

    def fill_region(self, x, y, selected_color_id):
        """Paint one four-connected unpainted region.

        Scanline runs keep the stack compact, even for multi-million-cell areas.
        Already painted cells are boundaries; diagonal contact does not connect areas.
        """
        self.end_stroke()
        p = self.painting
        empty = np.empty(0, dtype=np.uint32)
        if not (0 <= x < p.width and 0 <= y < p.height):
            return PaintResult.OUT_OF_BOUNDS, empty
        if p.painted_mask[y, x]:
            return PaintResult.ALREADY_PAINTED, empty
        if p.target_map[y, x] != selected_color_id:
            return PaintResult.WRONG, empty
        # Byte searches scan runs in C without allocating NumPy arrays per boundary.
        # Only rows touched by this connected component are materialized.
        rows = {}

        def row_data(ry):
            if ry not in rows:
                rows[ry] = bytearray(
                    ((p.target_map[ry] == selected_color_id) & ~p.painted_mask[ry]).tobytes()
                )
            return rows[ry]

        pending = [(x, y)]
        runs = []
        while pending:
            sx, sy = pending.pop()
            row = row_data(sy)
            if not row[sx]:
                continue
            left = row.rfind(b'\x00', 0, sx) + 1
            right = row.find(b'\x00', sx)
            if right < 0:
                right = p.width
            row[left:right] = b'\x00' * (right - left)
            runs.append(np.arange(sy * p.width + left, sy * p.width + right, dtype=np.uint32))
            for ny in (sy - 1, sy + 1):
                if 0 <= ny < p.height:
                    neighbor = row_data(ny)
                    start = neighbor.find(b'\x01', left, right)
                    while start >= 0:
                        pending.append((start, ny))
                        end = neighbor.find(b'\x00', start, right)
                        if end < 0:
                            break
                        start = neighbor.find(b'\x01', end, right)
        indices = np.concatenate(runs)
        p.painted_mask.ravel()[indices] = True
        p.counts[selected_color_id] += len(indices)
        return PaintResult.CORRECT, indices


def line_cells(start, end):
    """Bresenham interpolation prevents gaps during fast mouse strokes."""
    x, y = start
    ex, ey = end
    dx, dy = abs(ex - x), -abs(ey - y)
    sx, sy = (1 if x < ex else -1), (1 if y < ey else -1)
    error = dx + dy
    while True:
        yield x, y
        if x == ex and y == ey:
            break
        double = error * 2
        if double >= dy:
            error += dy
            x += sx
        if double <= dx:
            error += dx
            y += sy
