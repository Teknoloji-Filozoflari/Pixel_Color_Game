import math
from dataclasses import dataclass


@dataclass
class Camera:
    zoom: float = 12.0
    pan_x: float = 0.0
    pan_y: float = 0.0
    viewport_width: int = 800
    viewport_height: int = 600
    min_zoom: float = 0.05
    max_zoom: float = 48.0

    def view_bounds(self):
        """At painting scale, expose only a whole number of cells."""
        if self.zoom < 1:
            return 0.0, 0.0, float(self.viewport_width), float(self.viewport_height)
        width = math.floor(self.viewport_width / self.zoom) * self.zoom
        height = math.floor(self.viewport_height / self.zoom) * self.zoom
        return (self.viewport_width - width) / 2, (self.viewport_height - height) / 2, width, height

    def constrain(self, width, height):
        left, top, view_width, view_height = self.view_bounds()
        def bound(offset, image, viewport, origin):
            if image <= viewport:
                return origin + (viewport - image) / 2
            offset -= origin
            if self.zoom >= 1:
                offset = round(offset / self.zoom) * self.zoom
            return origin + min(0, max(viewport - image, offset))
        self.pan_x = bound(self.pan_x, width * self.zoom, view_width, left)
        self.pan_y = bound(self.pan_y, height * self.zoom, view_height, top)

    def screen_to_cell(self, x, y):
        left, top, width, height = self.view_bounds()
        if not (left <= x < left + width and top <= y < top + height):
            return -1, -1
        return math.floor((x - self.pan_x) / self.zoom), math.floor((y - self.pan_y) / self.zoom)

    def cell_to_screen(self, x, y):
        return self.pan_x + x * self.zoom, self.pan_y + y * self.zoom

    def zoom_at(self, x, y, factor):
        logical_x, logical_y = (x - self.pan_x) / self.zoom, (y - self.pan_y) / self.zoom
        self.zoom = max(self.min_zoom, min(self.max_zoom, self.zoom * factor))
        self.pan_x, self.pan_y = x - logical_x * self.zoom, y - logical_y * self.zoom

    def fit(self, width, height):
        self.zoom = max(
            self.min_zoom,
            min(self.max_zoom, min((self.viewport_width - 64) / width, (self.viewport_height - 64) / height)),
        )
        self.pan_x = (self.viewport_width - width * self.zoom) / 2
        self.pan_y = (self.viewport_height - height * self.zoom) / 2

    def visible_cell_rect(self, width, height):
        left, top, vw, vh = self.view_bounds()
        x0 = math.floor((left - self.pan_x) / self.zoom + 1e-9)
        y0 = math.floor((top - self.pan_y) / self.zoom + 1e-9)
        x1 = math.ceil((left + vw - self.pan_x) / self.zoom - 1e-9)
        y1 = math.ceil((top + vh - self.pan_y) / self.zoom - 1e-9)
        return max(0, x0), max(0, y0), min(width, x1), min(height, y1)
