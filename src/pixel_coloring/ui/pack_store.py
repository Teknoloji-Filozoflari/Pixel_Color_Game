"""In-app content store for optional category packs."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..services.pack_manager import PackError, PackManager
from ..services.packs import format_bytes, pack_for_category, preview_paths
from .i18n import number, tr
from .widgets import button, label


class PackCard(QFrame):
    download_requested = Signal(str)

    def __init__(self, pack: dict, parent=None):
        super().__init__(parent)
        self.pack = pack
        self.setObjectName("packCard")
        self.setStyleSheet(
            """
            QFrame#packCard {background:#1C2928; border:1px solid #496B62; border-radius:14px;}
            QLabel#packTitle {color:#F0F5F3; font-size:18px; font-weight:700;}
            QLabel#packMeta {color:#AEB9C4; font-size:12px;}
            QLabel#packDesc {color:#D4E8E2; font-size:13px;}
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        title = label(tr(pack["category"]), None)
        title.setObjectName("packTitle")
        title_row.addWidget(title, 1)
        self.badge = label("", "muted")
        self.badge.setObjectName("packMeta")
        title_row.addWidget(self.badge, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(title_row)

        count = pack.get("painting_count") or len(pack.get("painting_ids") or [])
        size = format_bytes(int(pack.get("bytes") or 0))
        meta = label(
            tr("{count} resim · {size}", count=number(count), size=size),
            "muted",
        )
        meta.setObjectName("packMeta")
        layout.addWidget(meta)

        description = pack.get("description") or ""
        if description:
            desc = label(tr(description), None)
            desc.setObjectName("packDesc")
            desc.setWordWrap(True)
            layout.addWidget(desc)

        previews = QHBoxLayout()
        previews.setSpacing(8)
        for path in preview_paths(pack["id"])[:4]:
            thumb = QLabel()
            thumb.setFixedSize(72, 72)
            thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumb.setStyleSheet("background:#263C3B; border-radius:8px;")
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                thumb.setPixmap(
                    pixmap.scaled(
                        72,
                        72,
                        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
            previews.addWidget(thumb)
        previews.addStretch()
        layout.addLayout(previews)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFixedHeight(18)
        self.progress.hide()
        layout.addWidget(self.progress)

        actions = QHBoxLayout()
        self.action = button(tr("İndir"), lambda: self.download_requested.emit(pack["id"]), True)
        self.action.setMinimumWidth(120)
        actions.addWidget(self.action)
        actions.addStretch()
        layout.addLayout(actions)
        self.apply_status(pack.get("status", "available"))

    def apply_status(self, status: str):
        self.pack["status"] = status
        if status == "installed":
            self.badge.setText(tr("Yüklü"))
            self.action.setText(tr("Boyamaya git"))
            self.action.setEnabled(True)
            self.progress.hide()
        elif status == "downloading":
            self.badge.setText(tr("İndiriliyor…"))
            self.action.setText(tr("İndiriliyor…"))
            self.action.setEnabled(False)
            self.progress.show()
        else:
            self.badge.setText(tr("İndirilebilir"))
            size = format_bytes(int(self.pack.get("bytes") or 0))
            self.action.setText(tr("İndir (~{size})", size=size))
            self.action.setEnabled(True)
            self.progress.hide()

    def set_progress(self, done: int, total: int, phase: str):
        if not total:
            return
        percent = max(0, min(100, int(100 * done / total)))
        labels = {
            "download": tr("İndiriliyor… %{percent}", percent=number(percent)),
            "verify": tr("Doğrulanıyor…"),
            "extract": tr("Açılıyor… %{percent}", percent=number(percent)),
            "install": tr("Kuruluyor… %{percent}", percent=number(percent)),
        }
        self.progress.show()
        self.progress.setValue(percent)
        self.progress.setFormat(labels.get(phase, tr("İndiriliyor… %{percent}", percent=number(percent))))


def build_pack_store(window, root):
    manager = PackManager(window.data_dir, window.database)
    window.pack_manager = manager

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    body = QWidget()
    cards_layout = QVBoxLayout(body)
    cards_layout.setContentsMargins(0, 0, 8, 0)
    cards_layout.setSpacing(14)
    scroll.setWidget(body)
    root.addWidget(scroll, 1)

    cards = {}
    worker = getattr(window, "pack_worker", None)
    if worker is None:
        worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="packs")
        window.pack_worker = worker

    def open_category(category: str):
        window.collection_category = category
        window.refresh_library()
        window.show_collection()

    def on_action(pack_id: str):
        card = cards[pack_id]
        if card.pack.get("status") == "installed":
            open_category(card.pack["category"])
            return
        if getattr(window, "pack_job", None):
            return
        card.apply_status("downloading")
        card.set_progress(0, 100, "download")

        updates = []

        def report(done, total, phase):
            updates.append((done, total, phase))

        def work():
            return manager.download_and_install(pack_id, progress=report)

        window.pack_job = worker.submit(work)
        window.pack_job_pack_id = pack_id

        timer = QTimer(window)

        def poll():
            while updates:
                done, total, phase = updates.pop(0)
                card.set_progress(done, total, phase)
            job = getattr(window, "pack_job", None)
            if job is None or not job.done():
                return
            timer.stop()
            window.pack_job = None
            try:
                job.result()
            except PackError as exc:
                card.apply_status("available")
                QMessageBox.warning(window, tr("İndirme başarısız"), tr(str(exc)))
                return
            except Exception as exc:
                card.apply_status("available")
                window.error(tr("İndirme başarısız"), exc)
                return
            card.apply_status("installed")
            window.refresh_library()
            window.statusBar().showMessage(
                tr("‘{category}’ paketi hazır", category=tr(card.pack["category"])),
                6000,
            )
            open_category(card.pack["category"])

        timer.timeout.connect(poll)
        timer.start(100)
        window.pack_poll_timer = timer

    for pack in manager.list_downloadable():
        card = PackCard(pack)
        card.download_requested.connect(on_action)
        cards[pack["id"]] = card
        cards_layout.addWidget(card)
    cards_layout.addStretch()
    window.pack_cards = cards


def prompt_download_category(window, category: str):
    """Empty-state helper when a remote category tab is selected but not installed."""
    pack = pack_for_category(category)
    if pack is None or pack.get("bundled"):
        return None
    manager = PackManager(window.data_dir, window.database)
    if manager.is_installed(pack["id"]):
        return None
    panel = QFrame()
    panel.setObjectName("panel")
    box = QVBoxLayout(panel)
    box.setContentsMargins(20, 20, 20, 20)
    box.setSpacing(12)
    box.addWidget(label(tr("Bu kategori henüz indirilmedi."), "subheading"))
    box.addWidget(
        label(
            tr(
                "{count} resim · {size}. İndirdikten hemen sonra boyayabilirsin.",
                count=number(pack.get("painting_count") or 0),
                size=format_bytes(int(pack.get("bytes") or 0)),
            ),
            "muted",
        )
    )
    box.addWidget(button(tr("Mağazaya git"), window.show_pack_store, True))
    return panel
