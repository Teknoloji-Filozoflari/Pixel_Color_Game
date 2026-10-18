from concurrent.futures import Future
from unittest.mock import Mock

import numpy as np
import pytest

from pixel_coloring.core.game_session import GameSession
from pixel_coloring.core.painting import Painting
from pixel_coloring.persistence.save_manager import SaveManager


def test_poll_cannot_lose_a_write_finishing_between_checks():
    class FinishingFuture(Future):
        def done(self):
            if not super().done():
                self.set_exception(OSError('disk full'))
                return False
            return True

    saver = SaveManager(None)
    future = FinishingFuture()
    saver.pending.append(future)
    try:
        assert saver.poll() == 0
        assert saver.pending == [future]
        with pytest.raises(OSError, match='disk full'):
            saver.poll()
    finally:
        saver.close()


def test_poll_consumes_every_completed_write_before_reporting_failure():
    saver = SaveManager(None)
    first = Mock(done=Mock(return_value=True), result=Mock(side_effect=OSError('disk full')))
    second = Mock(done=Mock(return_value=True), result=Mock(side_effect=OSError('write failed')))
    saver.pending = [first, second]
    try:
        with pytest.raises(OSError, match='disk full'):
            saver.poll()
        first.result.assert_called_once()
        second.result.assert_called_once()
        assert saver.pending == []
    finally:
        saver.close()


def test_close_stops_worker_even_if_pending_save_failed():
    saver = SaveManager(None)
    future = Future()
    future.set_exception(OSError('disk full'))
    saver.pending.append(future)
    with pytest.raises(OSError, match='disk full'):
        saver.close()
    with pytest.raises(RuntimeError, match='shutdown'):
        saver.executor.submit(lambda: None)


def test_queued_snapshot_is_not_changed_by_further_painting():
    painting = Painting('snapshot', 'Test', np.array([[10, 20, 30], [40, 50, 60]]),
                        np.array([[0, 1], [1, 0]]))
    session = GameSession(painting, selected=0)
    session.engine.paint_cell(0, 0, 0)
    database = Mock()
    saver = SaveManager(database)
    try:
        saver.save(session)
        session.engine.paint_cell(1, 1, 0)
        session.selected = 1
        saver.flush()
        snapshot = database.save.call_args.args[0]
        assert snapshot[2] == 1
        assert snapshot[-1] == 0
        assert np.unpackbits(np.frombuffer(snapshot[6], dtype=np.uint8), count=4).tolist() == [1, 0, 0, 0]
    finally:
        saver.close()


def test_queued_view_is_independent_of_later_camera_changes():
    painting = Painting('view-snapshot', 'Test', np.array([[10, 20, 30]]), np.zeros((2, 2), dtype=np.uint8))
    session = GameSession(painting)
    session.view_state = dict(zoom=16, center_x=1, center_y=1, width=2, height=2)
    database = Mock()
    saver = SaveManager(database)
    try:
        saver.save(session)
        session.view_state['zoom'] = 48
        saver.flush()
        assert database.save.call_args.kwargs['view_state']['zoom'] == 16
    finally:
        saver.close()
