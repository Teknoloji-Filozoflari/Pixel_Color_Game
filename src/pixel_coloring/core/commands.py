from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PaintCommand:
    """Only the newly painted flat cell indices; no full image snapshots."""

    indices: np.ndarray

    @property
    def nbytes(self):
        return self.indices.nbytes
