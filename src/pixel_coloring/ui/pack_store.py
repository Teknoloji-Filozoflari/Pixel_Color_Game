"""In-app content store for optional category packs."""

from __future__ import annotations

from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from ..services.pack_manager import PackError, PackManager
from ..services.packs import format_bytes, load_catalog, preview_paths
from .i18n import number, tr
from .widgets import button, label

DIFFICULTY_ORDER = [
    "Çok Kolay",
    "Kolay",
    "Kolay-Orta",
    "Orta",
    "Orta-Zor",
    "Zor",
    "Uzman",
]


def _pack_stats(pack: dict) -> dict:
    catalog = {item["id"]: item for item in load_catalog()}
    difficulties = Counter()
    for painting_id in pack.get("painting_ids") or []:
        item = catalog.get(painting_id)
        if item and item.get("difficulty"):
            difficulties[item["difficulty"]] += 1
    count = pack.get("painting_count") or len(pack.get("painting_ids") or [])
    return {
        "count": count,
        "bytes": int(pack.get("bytes") or 0),
        "difficulties": difficulties,
    }


def _difficulty_summary(difficulties: Counter) -> str:
    parts = []
    for name in DIFFICULTY_ORDER:
        amount = difficulties.get(name, 0)
        if amount:
            parts.append(f"{tr(name)} {number(amount)}")
    if not parts:
        return ""
    if len(parts) <= 3:
        return " · ".join(parts)
    # Keep the line compact when every tier is present.
    easiest = next((n for n in DIFFICULTY_ORDER if difficulties.get(n)), None)
    hardest = next((n for n in reversed(DIFFICULTY_ORDER) if difficulties.get(n)), None)
    if easiest and hardest and easiest != hardest:
        return tr("{easy} – {hard}", easy=tr(easiest), hard=tr(hardest))
    return parts[0]


class PackCard(QFrame):
    download_requested = Signal(str)

    def __init__(self, pack: dict, parent=None):
        super().__init__(parent)
        self.pack = pack
        self.setObjectName("packCard")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(320)
        self.setStyleSheet(
            """
            QFrame#packCard {background:#1C2928; border:1px solid #496B62; border-radius:14px;}
            QLabel#packTitle {color:#F0F5F3; font-size:20px; font-weight:800;}
            QLabel#packMeta {color:#AEB9C4; font-size:12px;}
            QLabel#packDesc {color:#D4E8E2; font-size:13px;}
            QLabel#statChip {background:#263C3B; color:#D4E8E2; border-radius:8px;
                padding:6px 10px; font-size:12px; font-weight:600;}
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)

        title_row = QHBoxLayout()
        title = label(tr(pack["category"]), None)
        title.setObjectName("packTitle")
        title.setWordWrap(False)
        title.setTextFormat(Qt.TextFormat.PlainText)
        title_row.addWidget(title, 1)
        self.badge = label("", None)
        self.badge.setObjectName("packMeta")
        self.badge.setWordWrap(False)
        title_row.addWidget(self.badge, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addLayout(title_row)

        stats = _pack_stats(pack)
        chips = QHBoxLayout()
        chips.setSpacing(8)
        for text in (
            tr("{count} resim", count=number(stats["count"])),
            format_bytes(stats["bytes"]),
        ):
            chip = label(text, None)
            chip.setObjectName("statChip")
            chip.setWordWrap(False)
            chips.addWidget(chip)
        chips.addStretch()
        layout.addLayout(chips)

        description = pack.get("description") or ""
        if description:
            desc = label(tr(description), None)
            desc.setObjectName("packDesc")
            desc.setWordWrap(True)
            layout.addWidget(desc)

        mix = _difficulty_summary(stats["difficulties"])
        if mix:
            difficulty = label(tr("Zorluk: {mix}", mix=mix), None)
            difficulty.setObjectName("packMeta")
            difficulty.setWordWrap(False)
            layout.addWidget(difficulty)

        previews = QHBoxLayout()
        previews.setSpacing(8)
        for path in preview_paths(pack["id"])[:4]:
            thumb = QLabel()
            thumb.setFixedSize(108, 88)
            thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
            thumb.setStyleSheet(
                "background:#263C3B; border-radius:8px; border:1px solid #3F5A54;"
            )
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                thumb.setPixmap(
                    pixmap.scaled(
                        108,
                        88,
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
        self.progress.setFixedHeight(16)
        self.progress.hide()
        layout.addWidget(self.progress)

        actions = QHBoxLayout()
        self.action = button(tr("İndir"), lambda: self.download_requested.emit(pack["id"]), True)
        self.action.setMinimumWidth(140)
        self.action.setFixedHeight(40)
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


class StoreGrid(QWidget):
    resized = Signal()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()


def build_pack_store(window, root):
    manager = PackManager(window.data_dir, window.database)
    window.pack_manager = manager

    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    container = StoreGrid()
    grid = QGridLayout(container)
    grid.setContentsMargins(0, 0, 8, 0)
    grid.setHorizontalSpacing(16)
    grid.setVerticalSpacing(16)
    grid.setAlignment(Qt.AlignmentFlag.AlignTop)
    scroll.setWidget(container)
    root.addWidget(scroll, 1)

    cards = {}
    packs = manager.list_downloadable()
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

    for pack in packs:
        card = PackCard(pack)
        card.download_requested.connect(on_action)
        cards[pack["id"]] = card

    def arrange():
        width = max(scroll.viewport().width(), 1)
        columns = 2 if width >= 720 else 1
        for card in cards.values():
            grid.removeWidget(card)
            card.hide()
        for index, card in enumerate(cards.values()):
            grid.addWidget(card, index // columns, index % columns)
            card.show()
        for column in range(2):
            grid.setColumnStretch(column, 1 if column < columns else 0)

    container.resized.connect(arrange)
    arrange()
    QTimer.singleShot(0, arrange)
    window.pack_cards = cards
