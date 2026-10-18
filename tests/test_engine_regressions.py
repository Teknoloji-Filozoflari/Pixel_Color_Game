from collections import deque

import numpy as np
import pytest

from pixel_coloring.core.paint_engine import PaintingEngine, PaintResult, line_cells
from pixel_coloring.core.painting import Painting


@pytest.mark.parametrize('record_history', [False, True])
def test_flood_fill_matches_four_connected_reference_and_preserves_counts(record_history):
    random = np.random.default_rng(42)
    target = random.integers(0, 2, (20, 30))
    painting = Painting('fill', 'Test', np.array([[10, 20, 30], [100, 110, 120]]), target)
    original = random.random(target.shape) < .15
    original[10, 15] = False
    painting.restore(original)
    selected = int(target[10, 15])
    expected = set()
    pending = deque([(15, 10)])
    while pending:
        x, y = pending.popleft()
        if not (0 <= x < painting.width and 0 <= y < painting.height):
            continue
        if (x, y) in expected or original[y, x] or target[y, x] != selected:
            continue
        expected.add((x, y))
        pending.extend([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)])
    engine = PaintingEngine(painting, record_history=record_history)
    result, indices = engine.fill_region(15, 10, selected)
    assert result == PaintResult.CORRECT
    assert set(indices.tolist()) == {y * painting.width + x for x, y in expected}
    mask = original.copy()
    for x, y in expected:
        mask[y, x] = True
    assert np.array_equal(painting.painted_mask, mask)
    assert np.array_equal(painting.counts, np.bincount(target[mask], minlength=2))
    if record_history:
        engine.undo()
        assert np.array_equal(painting.painted_mask, original)
        engine.redo()
        assert np.array_equal(painting.painted_mask, mask)
    else:
        assert not engine.undo_stack


def test_fast_brush_interpolation_has_no_gaps_in_any_direction():
    for end in [(8, 3), (3, 8), (-8, 3), (3, -8), (-8, -3), (-3, -8), (0, 0)]:
        cells = list(line_cells((0, 0), end))
        assert cells[0] == (0, 0) and cells[-1] == end
        assert len(cells) == max(abs(end[0]), abs(end[1])) + 1
        assert len(cells) == len(set(cells))
        assert all(max(abs(x - a), abs(y - b)) == 1
                   for (x, y), (a, b) in zip(cells, cells[1:]))
