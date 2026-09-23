import logging
import time
from concurrent.futures import ThreadPoolExecutor

import numpy as np

log = logging.getLogger(__name__)


class SaveManager:
    """Snapshot on GUI thread, ordered database writes on one worker."""

    def __init__(self, database):
        self.database = database
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="autosave")
        self.pending = []

    def save(self, session):
        p = session.painting
        snapshot = (
            p.id,
            p.progress * 100,
            p.painted_count,
            0,
            0,
            1,
            np.packbits(p.painted_mask).tobytes(),
            session.selected,
        )
        future = self.executor.submit(self._write, snapshot)
        self.pending.append(future)
        return future

    def _write(self, snapshot):
        started = time.perf_counter()
        self.database.save(snapshot)
        log.debug("Save %.1f ms", (time.perf_counter() - started) * 1000)

    def poll(self):
        done = [f for f in self.pending if f.done()]
        self.pending = [f for f in self.pending if not f.done()]
        for f in done:
            f.result()
        return len(done)

    def close(self):
        self.flush()
        self.executor.shutdown(wait=True)

    def flush(self):
        pending, self.pending = self.pending, []
        first_error = None
        for future in pending:
            try:
                future.result()
            except Exception as exc:
                first_error = first_error or exc
        if first_error:
            raise first_error
