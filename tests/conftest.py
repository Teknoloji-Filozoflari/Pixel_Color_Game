import os

import pytest


@pytest.fixture(scope='session')
def app():
    """Keep one QApplication alive through every UI test and its worker cleanup."""
    os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
    from PySide6.QtCore import QEvent
    from PySide6.QtWidgets import QApplication

    from pixel_coloring.ui.theme import apply_theme

    application = QApplication.instance() or QApplication([])
    apply_theme(application)
    yield application
    for widget in application.topLevelWidgets():
        if widget.isVisible():
            widget.close()
        widget.deleteLater()
    application.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    application.processEvents()
