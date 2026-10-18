from .paint_engine import PaintingEngine
from .palette import spread_palette


class GameSession:
    def __init__(self, painting, selected=None, view_state=None):
        self.painting = painting
        self.engine = PaintingEngine(painting, record_history=False)
        self.view_state = view_state
        self.palette_order = spread_palette(painting.palette, painting.id)
        self.color_numbers = {color: index + 1 for index, color in enumerate(self.palette_order)}
        if selected is None or not 0 <= selected < len(painting.palette):
            self.selected = self.next_unfinished_color()
            if self.selected is None:
                self.selected = self.palette_order[0]
        else:
            self.selected = selected
            if painting.counts[selected] >= painting.totals[selected]:
                following = self.next_unfinished_color(after=selected)
                if following is not None:
                    self.selected = following
        self.elapsed_base = 0.0
        self.revision = 0
        self.saved_revision = -1

    def next_unfinished_color(self, after=None):
        """Follow the numbered display order, wrapping past completed colors."""
        start = 0 if after is None else self.color_numbers[after] % len(self.palette_order)
        p = self.painting
        for offset in range(len(self.palette_order)):
            color = self.palette_order[(start + offset) % len(self.palette_order)]
            if p.counts[color] < p.totals[color]:
                return color
        return None

    @property
    def elapsed(self):
        return 0.0

    def changed(self):
        self.revision += 1
