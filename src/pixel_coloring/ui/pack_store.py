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


class PackListItem(QFrame):
    selected = Signal(str)

    def __init__(self, pack: dict, parent=None):
        super().__init__(parent)
        self.pack = pack
        self.setObjectName("packListItem")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(72)
        self.setStyleSheet(
            """
            QFrame#packListItem {background:#1C2928; border:1px solid #39424A; border-radius:12px;}
            QFrame#packListItem[active="true"] {background:#315B51; border:1px solid #8BC9B5;}
            QFrame#packListItem:hover {border-color:#639789;}
            QLabel#packListTitle {color:#F0F5F3; font-size:15px; font-weight:700;}
            QLabel#packListMeta {color:#AEB9C4; font-size:12px;}
            """
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(4)
        self.title = label(tr(pack["category"]), None)
        self.title.setObjectName("packListTitle")
        layout.addWidget(self.title)
        stats = _pack_stats(pack)
        self.meta = label(
            tr("{count} resim · {size}", count=number(stats["count"]), size=format_bytes(stats["bytes"])),
            None,
        )
        self.meta.setObjectName("packListMeta")
        layout.addWidget(self.meta)
        self.badge = label("", None)
        self.badge.setObjectName("packListMeta")
        layout.addWidget(self.badge)
        self.apply_status(pack.get("status", "available"))

    def mousePressEvent(self, event):
        self.selected.emit(self.pack["id"])
        super().mousePressEvent(event)

    def set_active(self, active: bool):
        self.setProperty("active", active)
        self.style().unpolish(self)
        self.style().polish(self)
        self.update()

    def apply_status(self, status: str):
        self.pack["status"] = status
        if status == "installed":
            self.badge.setText(tr("Yüklü"))
        elif status == "downloading":
            self.badge.setText(tr("İndiriliyor…"))
        else:
            self.badge.setText(tr("İndirilebilir"))


class PackDetailPane(QFrame):
    download_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pack = None
        self.setObjectName("packDetail")
        self.setStyleSheet(
            """
            QFrame#packDetail {background:#1C2928; border:1px solid #496B62; border-radius:14px;}
            QLabel#packTitle {color:#F0F5F3; font-size:26px; font-weight:800;}
            QLabel#packMeta {color:#AEB9C4; font-size:13px;}
            QLabel#packDesc {color:#D4E8E2; font-size:14px;}
            QLabel#statChip {background:#263C3B; color:#D4E8E2; border-radius:8px;
                padding:8px 10px; font-size:12px; font-weight:600;}
            QLabel#sectionLabel {color:#AEB9C4; font-size:11px; font-weight:700;}
            """
        )
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(22, 20, 22, 20)
        self.layout.setSpacing(12)
        self.empty = label(tr("Bir paket seçerek önizleme, boyut ve zorluk dağılımını gör."), "muted")
        self.layout.addWidget(self.empty)
        self.layout.addStretch(1)

    def clear(self):
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def show_pack(self, pack: dict):
        self.pack = pack
        self.clear()
        stats = _pack_stats(pack)

        title_row = QHBoxLayout()
        title = label(tr(pack["category"]), None)
        title.setObjectName("packTitle")
        title_row.addWidget(title, 1)
        self.badge = label("", None)
        self.badge.setObjectName("packMeta")
        title_row.addWidget(self.badge, alignment=Qt.AlignmentFlag.AlignTop)
        self.layout.addLayout(title_row)

        description = pack.get("description") or ""
        if description:
            desc = label(tr(description), None)
            desc.setObjectName("packDesc")
            desc.setWordWrap(True)
            self.layout.addWidget(desc)

        chips = QHBoxLayout()
        chips.setSpacing(8)
        for text in (
            tr("{count} resim", count=number(stats["count"])),
            format_bytes(stats["bytes"]),
            tr("Sürüm {version}", version=number(pack.get("version") or 1)),
        ):
            chip = label(text, None)
            chip.setObjectName("statChip")
            chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
            chips.addWidget(chip)
        chips.addStretch()
        self.layout.addLayout(chips)

        preview_heading = label(tr("Örnek önizlemeler"), None)
        preview_heading.setObjectName("sectionLabel")
        self.layout.addWidget(preview_heading)
        preview_grid = QGridLayout()
        preview_grid.setSpacing(12)
        preview_grid.setColumnStretch(0, 1)
        preview_grid.setColumnStretch(1, 1)
        paths = preview_paths(pack["id"])[:4]
        if paths:
            for index, path in enumerate(paths):
                thumb = QLabel()
                thumb.setFixedHeight(168)
                thumb.setMinimumWidth(220)
                thumb.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                thumb.setAlignment(Qt.AlignmentFlag.AlignCenter)
                thumb.setStyleSheet(
                    "background:#263C3B; border-radius:10px; border:1px solid #496B62;"
                )
                pixmap = QPixmap(str(path))
                if not pixmap.isNull():
                    thumb.setPixmap(
                        pixmap.scaled(
                            360,
                            160,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation,
                        )
                    )
                preview_grid.addWidget(thumb, index // 2, index % 2)
        else:
            preview_grid.addWidget(label(tr("Önizleme yok."), "muted"), 0, 0)
        self.layout.addLayout(preview_grid, 1)

        difficulties = stats["difficulties"]
        if difficulties:
            mix_heading = label(tr("Zorluk dağılımı"), None)
            mix_heading.setObjectName("sectionLabel")
            self.layout.addWidget(mix_heading)
            mix = QGridLayout()
            mix.setHorizontalSpacing(8)
            mix.setVerticalSpacing(8)
            placed = 0
            for name in DIFFICULTY_ORDER:
                amount = difficulties.get(name, 0)
                if not amount:
                    continue
                chip = label(f"{tr(name)} · {number(amount)}", None)
                chip.setObjectName("statChip")
                chip.setAlignment(Qt.AlignmentFlag.AlignCenter)
                mix.addWidget(chip, placed // 4, placed % 4)
                placed += 1
            self.layout.addLayout(mix)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(True)
        self.progress.setFixedHeight(18)
        self.progress.hide()
        self.layout.addWidget(self.progress)

        actions = QHBoxLayout()
        self.action = button(tr("İndir"), lambda: self.download_requested.emit(pack["id"]), True)
        self.action.setMinimumWidth(160)
        self.action.setFixedHeight(44)
        actions.addWidget(self.action)
        actions.addStretch()
        self.layout.addLayout(actions)
        self.apply_status(pack.get("status", "available"))

    def apply_status(self, status: str):
        if self.pack is None:
            return
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

    content = QHBoxLayout()
    content.setSpacing(18)
    root.addLayout(content, 1)

    list_scroll = QScrollArea()
    list_scroll.setWidgetResizable(True)
    list_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    list_scroll.setFixedWidth(300)
    list_body = QWidget()
    list_layout = QVBoxLayout(list_body)
    list_layout.setContentsMargins(0, 0, 6, 0)
    list_layout.setSpacing(10)
    list_scroll.setWidget(list_body)
    content.addWidget(list_scroll)

    detail = PackDetailPane()
    content.addWidget(detail, 1)

    items = {}
    packs = manager.list_downloadable()
    selected = {"id": packs[0]["id"] if packs else None}

    worker = getattr(window, "pack_worker", None)
    if worker is None:
        worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="packs")
        window.pack_worker = worker

    def open_category(category: str):
        window.collection_category = category
        window.refresh_library()
        window.show_collection()

    def select_pack(pack_id: str):
        selected["id"] = pack_id
        for key, item in items.items():
            item.set_active(key == pack_id)
        pack = items[pack_id].pack
        detail.show_pack(pack)

    def on_action(pack_id: str):
        item = items[pack_id]
        pack = item.pack
        if pack.get("status") == "installed":
            open_category(pack["category"])
            return
        if getattr(window, "pack_job", None):
            return
        select_pack(pack_id)
        item.apply_status("downloading")
        detail.apply_status("downloading")
        detail.set_progress(0, 100, "download")

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
                detail.set_progress(done, total, phase)
            job = getattr(window, "pack_job", None)
            if job is None or not job.done():
                return
            timer.stop()
            window.pack_job = None
            try:
                job.result()
            except PackError as exc:
                item.apply_status("available")
                detail.apply_status("available")
                QMessageBox.warning(window, tr("İndirme başarısız"), tr(str(exc)))
                return
            except Exception as exc:
                item.apply_status("available")
                detail.apply_status("available")
                window.error(tr("İndirme başarısız"), exc)
                return
            item.apply_status("installed")
            detail.apply_status("installed")
            window.refresh_library()
            window.statusBar().showMessage(
                tr("‘{category}’ paketi hazır", category=tr(pack["category"])),
                6000,
            )
            open_category(pack["category"])

        timer.timeout.connect(poll)
        timer.start(100)
        window.pack_poll_timer = timer

    for pack in packs:
        item = PackListItem(pack)
        item.selected.connect(select_pack)
        items[pack["id"]] = item
        list_layout.addWidget(item)
    list_layout.addStretch()

    detail.download_requested.connect(on_action)
    window.pack_cards = items
    window.pack_detail = detail
    if selected["id"]:
        select_pack(selected["id"])
