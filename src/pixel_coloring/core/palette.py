"""Stable display order; stored color IDs and painting data stay unchanged."""

import random

import numpy as np


def spread_palette(palette, painting_id, columns=5):
    remaining = list(range(len(palette)))
    random.Random(painting_id).shuffle(remaining)
    colors = palette.astype(np.float32)
    order = []
    while remaining:
        # Bound the work even for imported levels with thousands of colors.
        candidates = remaining[:64]
        neighbors = order[-1:]
        if len(order) >= columns:
            neighbors = neighbors + [order[-columns]]
        chosen = 0
        if neighbors:
            differences = colors[candidates, None] - colors[neighbors]
            distances = (differences * differences).sum(axis=2).min(axis=1)
            chosen = int(distances.argmax())
        order.append(remaining[chosen])
        remaining[chosen] = remaining[-1]
        remaining.pop()
    return tuple(order)
