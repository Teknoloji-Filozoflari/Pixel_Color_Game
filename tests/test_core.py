import numpy as np

from pixel_coloring.core.paint_engine import PaintResult, PaintingEngine
from pixel_coloring.core.painting import Painting


def test_correct_color_paints_cell():
    painting = Painting(
        "test", "Test", np.array([[255, 0, 0], [0, 0, 255]], dtype=np.uint8),
        np.array([[0, 1], [1, 0]], dtype=np.uint8), "Test",
    )
    engine = PaintingEngine(painting)

    assert engine.paint_cell(0, 0, 0) is PaintResult.CORRECT
    assert painting.painted_mask[0, 0]


def test_wrong_color_does_not_paint_cell():
    painting = Painting(
        "test", "Test", np.array([[255, 0, 0], [0, 0, 255]], dtype=np.uint8),
        np.array([[0, 1], [1, 0]], dtype=np.uint8), "Test",
    )
    engine = PaintingEngine(painting)

    assert engine.paint_cell(0, 0, 1) is PaintResult.WRONG
    assert not painting.painted_mask[0, 0]
