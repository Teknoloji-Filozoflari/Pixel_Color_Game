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
        view_state = dict(session.view_state) if session.view_state is not None else None
        future = self.executor.submit(self._write, snapshot, view_state)
        self.pending.append(future)
        return future

    def _write(self, snapshot, view_state):
        started = time.perf_counter()
        if view_state is None:
            self.database.save(snapshot)
        else:
            self.database.save(snapshot, view_state=view_state)
        log.debug("Save %.1f ms", (time.perf_counter() - started) * 1000)

    def poll(self):
        done, waiting = [], []
        for future in self.pending:
            (done if future.done() else waiting).append(future)
        self.pending = waiting
        first_error = None
        for f in done:
            try:
                f.result()
            except Exception as exc:
                first_error = first_error or exc
        if first_error:
            raise first_error
        return len(done)

    def close(self):
        try:
            self.flush()
        finally:
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
