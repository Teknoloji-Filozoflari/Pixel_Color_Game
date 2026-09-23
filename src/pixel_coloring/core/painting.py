from dataclasses import dataclass, field

import numpy as np


@dataclass
class Painting:
    id: str
    title: str
    palette: np.ndarray
    target_map: np.ndarray
    category: str = "Diğer"
    author: str = "Piksel Atölyesi"
    painted_mask: np.ndarray = field(init=False)
    totals: np.ndarray = field(init=False)
    counts: np.ndarray = field(init=False)

    def __post_init__(self):
        p = np.asarray(self.palette)
        t = np.asarray(self.target_map)
        if p.ndim != 2 or p.shape[1] != 3 or not 1 <= len(p) <= 65535:
            raise ValueError("Geçersiz renk paleti")
        if not np.issubdtype(p.dtype, np.integer) or p.min() < 0 or p.max() > 255:
            raise ValueError("RGB değerleri 0–255 arasında olmalı")
        if t.ndim != 2 or not t.size:
            raise ValueError("Resim iki boyutlu ve boş olmayan bir piksel haritası olmalı")
        if not np.issubdtype(t.dtype, np.integer) or t.min() < 0 or t.max() >= len(p):
            raise ValueError("Resimde geçersiz renk numarası var")
        self.palette = np.array(p, dtype=np.uint8, copy=True)
        self.target_map = np.array(t, dtype=np.uint8 if len(p) <= 255 else np.uint16, copy=True)
        self.target_map.flags.writeable = False
        self.palette.flags.writeable = False
        self.painted_mask = np.zeros(t.shape, dtype=bool)
        self.totals = np.bincount(self.target_map.ravel(), minlength=len(p))
        self.counts = np.zeros(len(p), dtype=np.int64)

    @property
    def width(self):
        return self.target_map.shape[1]

    @property
    def height(self):
        return self.target_map.shape[0]

    @property
    def painted_count(self):
        return int(self.counts.sum())

    @property
    def progress(self):
        return self.painted_count / self.target_map.size

    def restore(self, mask):
        if mask.shape != self.target_map.shape or mask.dtype != bool:
            raise ValueError("Kayıt boyutu resimle eşleşmiyor")
        self.painted_mask[:] = mask
        self.counts[:] = np.bincount(self.target_map[mask], minlength=len(self.palette))
