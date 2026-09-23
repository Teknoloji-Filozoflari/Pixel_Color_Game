import argparse
import logging
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from queue import SimpleQueue, Empty
from time import perf_counter

from PySide6.QtCore import QStandardPaths, QTimer
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from .ui.startup import StartupScreen


def main():
    started = perf_counter()
    parser = argparse.ArgumentParser(description="Piksel Atölyesi")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--smoke-test", action="store_true")
    args = parser.parse_args()
    if sys.platform == "win32":
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PixelColoring.PikselAtolyesi")
    app = QApplication(sys.argv[:1])
    app.setApplicationName("PikselAtolyesi")
    app.setOrganizationName("PixelColoring")
    app.setWindowIcon(QIcon(str(Path(__file__).parent / "resources/icons/piksel-atolyesi.png")))
    splash = StartupScreen()
    splash.show()
    app.processEvents()
    from .ui.theme import apply_theme
    apply_theme(app)
    data_dir = args.data_dir or Path(
        QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    )
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "paintings").mkdir(exist_ok=True)
        logging.basicConfig(
            level=logging.DEBUG if args.debug else logging.INFO,
            format="%(asctime)s %(levelname)s %(name)s: %(message)s",
            handlers=[logging.FileHandler(data_dir / "game.log", encoding="utf-8"), logging.StreamHandler()],
        )
        updates = SimpleQueue()

        def prepare():
            from .persistence.database import Database
            from .services.samples import ensure_samples

            database = Database(data_dir / "progress.sqlite3")
            ensure_samples(data_dir / "paintings", database,
                           lambda done, total: updates.put((5 + 85 * done / max(total, 1),
                                                           f'Koleksiyon hazırlanıyor · {done} / {total}')))
            return database

        executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='startup')
        future = executor.submit(prepare)
        window = None
        timer = QTimer()

        def finish():
            nonlocal window
            try:
                while True:
                    value, message = updates.get_nowait()
                    splash.set_progress(value, message)
            except Empty:
                pass
            if not future.done():
                return
            timer.stop()
            try:
                database = future.result()
                splash.set_progress(95, 'Atölye açılıyor…')
                app.processEvents()
                from .ui.main_window import MainWindow
                window = MainWindow(data_dir, database, args.debug)
                window.show()
                splash.close()
                logging.info('Startup ready in %.2f seconds', perf_counter() - started)
                if args.smoke_test:
                    QTimer.singleShot(500, window.close)
            except Exception as exc:
                logging.exception('Startup failed')
                splash.hide()
                QMessageBox.critical(None, 'Piksel Atölyesi açılamadı', str(exc))
                app.exit(1)

        timer.timeout.connect(finish)
        timer.start(40)
        try:
            return app.exec()
        finally:
            executor.shutdown(wait=True)
    except Exception as exc:
        logging.exception("Startup failed")
        splash.hide()
        QMessageBox.critical(None, "Piksel Atölyesi açılamadı", str(exc))
        return 1
