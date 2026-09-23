import time

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ..core.paint_engine import PaintResult, line_cells
from .camera import Camera
from .pointer import painting_pointer
from .tile_cache import TILE_SIZE, TileCache


class Canvas(QWidget):
    changed = Signal()
    stroke_finished = Signal()
    camera_changed = Signal()
    color_picked = Signal(int)
    region_changed = Signal(int, int, int, int)

    def __init__(self, session, settings, debug=False):
        super().__init__()
        self.session = session
        self.settings = settings
        self.debug = debug
        self.camera = Camera()
        self.cache = TileCache(session.painting)
        self.cache.selected = session.selected
        self.cache.highlight = settings.get("highlight", 0.75)
        self.cache.highlight_color = settings.get("highlight_color", (0, 255, 0))
        self.setMinimumSize(320, 280)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.dragging = False
        self.fill_mode = False
        self.panning = False
        self.last_cell = None
        self.last_pos = QPointF()
        self.hover = None
        self.wrong = None
        self.first_resize = True
        self.painting_cursor = painting_pointer()
        self.setCursor(self.painting_cursor)

    def select(self, selected):
        self.finish_stroke()
        self.session.selected = selected
        self.cache.selected = selected
        self.cache.clear()
        self.update()

    def fit(self):
        p = self.session.painting
        self.camera.fit(p.width, p.height)
        self.constrain_camera()
        self.update()
        self.camera_changed.emit()

    def constrain_camera(self):
        p = self.session.painting
        self.camera.constrain(p.width, p.height)

    def pan_view(self, dx, dy):
        """Move the viewing position in screen pixels, independent of zoom."""
        self.finish_stroke()
        self.camera.pan_x -= dx
        self.camera.pan_y -= dy
        self.constrain_camera()
        self.hover = None
        self.update()
        self.camera_changed.emit()

    def fill_at(self, pos):
        x, y = self.camera.screen_to_cell(pos.x(), pos.y())
        self.fill_cell(x, y)

    def fill_cell(self, x, y):
        result, indices = self.session.engine.fill_region(x, y, self.session.selected)
        if result == PaintResult.CORRECT:
            self.cache.invalidate_indices(indices)
            p = self.session.painting
            xs = indices % p.width
            self.region_changed.emit(
                int(xs.min()),
                int(indices.min() // p.width),
                int(xs.max()) + 1,
                int(indices.max() // p.width) + 1,
            )
            self.session.changed()
            self.changed.emit()
            self.stroke_finished.emit()
        elif result == PaintResult.WRONG and self.settings.get("feedback", True):
            self.wrong = x, y
            QTimer.singleShot(220, self.clear_wrong)
        self.update()

    def resizeEvent(self, event):
        self.camera.viewport_width, self.camera.viewport_height = self.width(), self.height()
        if self.first_resize:
            self.fit()
            self.first_resize = False
        self.constrain_camera()
        self.camera_changed.emit()
        super().resizeEvent(event)

    def paintEvent(self, event):
        started = time.perf_counter()
        q = QPainter(self)
        q.fillRect(self.rect(), QColor("#1B2027"))
        c, p = self.camera, self.session.painting
        q.setClipRect(QRectF(*c.view_bounds()))
        q.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, c.zoom < 1)
        x0, y0, x1, y1 = c.visible_cell_rect(p.width, p.height)
        if x0 < x1 and y0 < y1:
            for ty in range(y0 // TILE_SIZE, (y1 - 1) // TILE_SIZE + 1):
                for tx in range(x0 // TILE_SIZE, (x1 - 1) // TILE_SIZE + 1):
                    tile = self.cache.get(tx, ty)
                    sx, sy = c.cell_to_screen(tx * TILE_SIZE, ty * TILE_SIZE)
                    q.drawImage(QRectF(sx, sy, tile.width() * c.zoom, tile.height() * c.zoom), tile)
            if self.settings.get("grid", True) and c.zoom >= 9:
                q.setPen(QPen(QColor(35, 39, 46, int(255 * self.settings.get("grid_opacity", 0.22))), 1))
                left, top = c.cell_to_screen(x0, y0)
                right, bottom = c.cell_to_screen(x1, y1)
                for x in range(x0, x1 + 1):
                    sx, _ = c.cell_to_screen(x, 0)
                    q.drawLine(QPointF(sx, top), QPointF(sx, bottom))
                for y in range(y0, y1 + 1):
                    _, sy = c.cell_to_screen(0, y)
                    q.drawLine(QPointF(left, sy), QPointF(right, sy))
            if self.settings.get("numbers", True) and c.zoom >= 18:
                font = QFont("Noto Sans")
                font.setPixelSize(int(min(15, c.zoom * 0.43)))
                q.setFont(font)
                q.setPen(QColor("#51555C"))
                for y in range(y0, y1):
                    for x in range(x0, x1):
                        if not p.painted_mask[y, x]:
                            sx, sy = c.cell_to_screen(x, y)
                            q.drawText(
                                QRectF(sx, sy, c.zoom, c.zoom),
                                Qt.AlignmentFlag.AlignCenter,
                                str(int(p.target_map[y, x]) + 1),
                            )
        if self.debug:
            q.setPen(QColor("#FFFFFF"))
            q.drawText(
                12,
                22,
                f"{(time.perf_counter() - started) * 1000:.1f} ms  | "
                f"tiles {len(self.cache.tiles)}  | {self.cache.bytes / 1048576:.1f} MB  | "
                f"zoom {c.zoom:.2f} | cell {self.hover}",
            )
        q.end()

    def wheelEvent(self, event):
        self.finish_stroke()
        pos = event.position()
        p = self.session.painting
        cover = max(self.width() / p.width, self.height() / p.height)
        contain = min(self.width() / p.width, self.height() / p.height)
        delta = event.angleDelta().y()
        current = self.camera.zoom
        self.camera.max_zoom = max(self.camera.max_zoom, cover)
        if delta < 0 and current <= cover * (1 + 1e-9):
            # One step below the edge-clamped view reveals the whole image.
            target = min(current, contain)
        elif delta:
            target = max(cover, current * 1.2 ** (delta / 120))
        else:
            target = current
        self.camera.zoom_at(pos.x(), pos.y(), target / current)
        self.constrain_camera()
        self.update()
        self.camera_changed.emit()
        event.accept()

    def mousePressEvent(self, event):
        self.setFocus()
        self.last_pos = event.position()
        if event.button() == Qt.MouseButton.RightButton:
            self.finish_stroke()
            x, y = self.camera.screen_to_cell(event.position().x(), event.position().y())
            p = self.session.painting
            if 0 <= x < p.width and 0 <= y < p.height:
                self.color_picked.emit(int(p.target_map[y, x]))
        elif event.button() == Qt.MouseButton.MiddleButton:
            self.panning = True
            self.pan_anchor = (event.position(), self.camera.pan_x, self.camera.pan_y)
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
        elif event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.last_cell = None
            if self.fill_mode:
                self.fill_drag_at(event.position())
            else:
                self.paint_at(event.position())

    def mouseMoveEvent(self, event):
        pos = event.position()
        self.hover = self.camera.screen_to_cell(pos.x(), pos.y())
        if self.panning:
            start, pan_x, pan_y = self.pan_anchor
            delta = pos - start
            self.camera.pan_x = pan_x + delta.x()
            self.camera.pan_y = pan_y + delta.y()
            self.constrain_camera()
            self.camera_changed.emit()
        elif self.dragging:
            if self.fill_mode:
                self.fill_drag_at(pos)
            else:
                self.paint_at(pos)
        self.last_pos = pos
        self.update()

    def fill_drag_at(self, pos):
        cell = self.camera.screen_to_cell(pos.x(), pos.y())
        if cell == (-1, -1):
            self.last_cell = None
            return
        if cell == self.last_cell:
            return
        for x, y in line_cells(self.last_cell or cell, cell):
            if not self.dragging:
                break
            self.fill_cell(x, y)
        if self.dragging:
            self.last_cell = cell

    def paint_at(self, pos):
        cell = self.camera.screen_to_cell(pos.x(), pos.y())
        if cell == (-1, -1):
            self.last_cell = None
            return
        if cell == self.last_cell:
            return
        any_changed = False
        dirty_x0 = dirty_y0 = float("inf")
        dirty_x1 = dirty_y1 = -1
        for x, y in line_cells(self.last_cell or cell, cell):
            result = self.session.engine.paint_cell(x, y, self.session.selected)
            if result == PaintResult.CORRECT:
                self.cache.invalidate(x, y)
                any_changed = True
                dirty_x0, dirty_y0 = min(dirty_x0, x), min(dirty_y0, y)
                dirty_x1, dirty_y1 = max(dirty_x1, x + 1), max(dirty_y1, y + 1)
            elif result == PaintResult.WRONG and self.settings.get("feedback", True):
                self.wrong = x, y
                QTimer.singleShot(220, self.clear_wrong)
        self.last_cell = cell
        if any_changed:
            self.region_changed.emit(dirty_x0, dirty_y0, dirty_x1, dirty_y1)
            self.session.changed()
            self.changed.emit()
        self.update()

    def clear_wrong(self):
        self.wrong = None
        self.update()

    def finish_stroke(self):
        self.dragging = False
        self.last_cell = None
        if self.session.engine.end_stroke():
            self.stroke_finished.emit()

    def mouseReleaseEvent(self, event):
        self.finish_stroke()
        self.panning = False
        self.setCursor(self.painting_cursor)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.finish_stroke()
            self.panning = False
            self.setCursor(self.painting_cursor)
        else:
            super().keyPressEvent(event)

    def focusOutEvent(self, event):
        self.finish_stroke()
        self.panning = False
        self.setCursor(self.painting_cursor)
        super().focusOutEvent(event)

    def leaveEvent(self, event):
        self.hover = None
        self.update()
