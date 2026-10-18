"""Bounded, opt-in progress recording and atomic animated GIF export."""

import os
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

from ..rendering.progress_preview import ProgressPreview


class Timelapse:
    def __init__(self, painting, limit=180):
        if limit < 4:
            raise ValueError('At least four frames are required')
        self.painting = painting
        self.preview = None
        self.frames = []
        self.limit = limit
        self.active = False
        self.dirty = False
        self.stride = 1
        self.changes = 0

    def start(self):
        self.active = True
        self.capture(force=True)

    def changed(self):
        if self.active:
            self.dirty = True

    def pause(self):
        if self.active:
            self.capture(force=True)
        self.active = False

    def capture(self, force=False):
        if not force and (not self.active or not self.dirty):
            return
        self.dirty = False
        self.changes += 1
        if not force and self.changes % self.stride:
            return
        if self.preview is None:
            self.preview = ProgressPreview(self.painting, 320, 240)
        else:
            self.preview.refresh()
        pixels = self.preview.rgb
        if self.frames and np.array_equal(np.asarray(self.frames[-1]), pixels):
            return
        if len(self.frames) >= self.limit:
            self.frames = self.frames[::2]
            self.stride *= 2
        self.frames.append(Image.fromarray(pixels.copy()))


def export_gif(frames, destination):
    """Replace the destination only after Pillow has written a complete GIF."""
    if not frames:
        raise ValueError('Kaydedilecek kare yok.')
    path = Path(destination)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', suffix='.gif', dir=path.parent)
    os.close(fd)
    try:
        converted = [frame.quantize(colors=128, dither=Image.Dither.NONE) for frame in frames]
        converted[0].save(temporary, format='GIF', save_all=True, append_images=converted[1:],
                          duration=[90] * (len(converted) - 1) + [1200], loop=0, disposal=2)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)
    return path
