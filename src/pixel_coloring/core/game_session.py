from .paint_engine import PaintingEngine


class GameSession:
    def __init__(self, painting):
        self.painting = painting
        self.engine = PaintingEngine(painting, record_history=False)
        remaining = painting.totals - painting.counts
        self.selected = next((i for i, n in enumerate(remaining) if n), 0)
        self.elapsed_base = 0.0
        self.revision = 0
        self.saved_revision = -1

    @property
    def elapsed(self):
        return 0.0

    def changed(self):
        self.revision += 1
