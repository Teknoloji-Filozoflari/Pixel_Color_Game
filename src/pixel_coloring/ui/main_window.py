import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PySide6.QtCore import QIODevice, QSaveFile, Qt, QTimer
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QMainWindow,
    QMessageBox,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from ..core.game_session import GameSession
from ..importer.image_importer import import_image, validate_dimensions
from ..importer.level_writer import read_level, read_thumbnail, write_level
from ..persistence.save_manager import SaveManager
from ..services.library import delete_imported
from .game import GameScreen
from .home_actions import HomeAction
from .i18n import LANGUAGES, set_language, tr, translate_error, painting_title
from .widgets import button, label

log = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(self, data_dir, database, debug=False):
        super().__init__()
        self.data_dir, self.database, self.debug = data_dir, database, debug
        self.settings = {
            "grid": True,
            "numbers": True,
            "feedback": True,
            "autosave": 300,
            "highlight": 0.75,
            "grid_opacity": 0.22,
            "sound": False,
            "language": "tr",
        }
        self.settings.update(database.get_settings())
        # Keep persisted intervals in seconds; migrate older second-based choices.
        self.settings['autosave'] = min(
            (300, 600, 900, 1800), key=lambda seconds: abs(seconds - int(self.settings['autosave']))
        )
        self.settings['language'] = set_language(self.settings.get('language', 'tr'))
        self.saver = SaveManager(database)
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="levels")
        self.job = None
        self.job_kind = None
        self.game = None
        self.paths = {}
        self.metadata = {}
        self.thumbnail_cache = {}
        self.collection_category = "Tüm kategoriler"
        self.collection_selected = None
        self.setWindowTitle("Piksel Atölyesi")
        self.resize(1280, 820)
        self.setMinimumSize(960, 640)
        root = QWidget()
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(194)
        self.nav_buttons = {}
        self.sidebar.hide()
        self.stack = QStackedWidget()
        layout.addWidget(self.stack, 1)
        self.setCentralWidget(root)
        self.statusBar().showMessage(tr("Hazır · Kayıtlar bu cihazda saklanır"))
        self.poll_timer = QTimer(self)
        self.poll_timer.timeout.connect(self.poll)
        self.poll_timer.start(150)
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.save_game)
        self.autosave_timer.start(int(self.settings["autosave"]) * 1000)
        self.refresh_library()
        self.show_home()

    def showEvent(self, event):
        super().showEvent(event)
        from .window_chrome import apply_dark_titlebar

        apply_dark_titlebar(self)

    def error(self, text, exc):
        log.error("%s: %s", text, exc, exc_info=(type(exc), exc, exc.__traceback__))
        QMessageBox.warning(self, text, translate_error(exc))

    def refresh_library(self):
        with self.database.connect() as con:
            rows = con.execute(
                "SELECT id,title,category,width,height,palette_size,data_path FROM paintings "
                "ORDER BY width * height DESC,id"
            ).fetchall()
        self.metadata = {r[0]: r[1:6] for r in rows}
        catalog = Path(__file__).resolve().parents[1] / "resources/paintings/catalog.json"
        self.level_details = {item["id"]: item for item in json.loads(catalog.read_text(encoding="utf-8"))}

        # Keep each revised category together and ordered from beginner to expert.
        progression = sorted(
            (r for r in rows if r[0] in self.level_details and self.level_details[r[0]].get("tier")),
            key=lambda r: (r[2], self.level_details[r[0]]["order"]),
        )
        progression_ids = {r[0] for r in progression}
        rows = progression + [r for r in rows if r[0] not in progression_ids]
        self.metadata = {r[0]: r[1:6] for r in rows}

        self.paths = {r[0]: Path(r[6]) for r in rows}
        for key, meta in list(self.metadata.items()):
            if not key.startswith('sample-'):
                self.metadata[key] = (meta[0], 'İçe aktarılan', *meta[2:])

    def leave_game(self):
        if self.game:
            self.game.exit_focus_mode()
            self.game.canvas.finish_stroke()
            self.save_game()
            try:
                self.saver.flush()
            except Exception as exc:
                self.error(tr("Son kayıt tamamlanamadı"), exc)
                return False
            self.stack.removeWidget(self.game)
            self.game.deleteLater()
            self.game = None
        self.sidebar.hide()
        return True

    def page(self, active, heading, subtitle):
        if not self.leave_game():
            return None
        for key, widget in self.nav_buttons.items():
            widget.setChecked(key == active)
        while self.stack.count():
            widget = self.stack.widget(0)
            self.stack.removeWidget(widget)
            widget.deleteLater()
        page = QWidget()
        root = QVBoxLayout(page)
        root.setContentsMargins(34, 28, 34, 24)
        root.setSpacing(16)
        self.stack.addWidget(page)
        self.stack.setCurrentWidget(page)
        if active == "collection":
            return root
        back = HomeAction('collection', tr('Koleksiyona dön'), self.show_collection)
        back.setObjectName('collectionBackButton')
        root.addWidget(back, alignment=Qt.AlignmentFlag.AlignLeft)
        section = {
            "home": tr("ANA SAYFA"),
            "collection": tr("KOLEKSİYON"),
            "settings": tr("AYARLAR"),
        }.get(active, active)
        root.addWidget(label("PİKSEL ATÖLYESİ  /  " + section, "eyebrow"))
        root.addWidget(label(heading, "heading"))
        root.addWidget(label(subtitle, "muted"))
        return root

    def thumbnail(self, id, width=260, height=190):
        if id not in self.thumbnail_cache:
            pixmap = QPixmap()
            pixmap.loadFromData(read_thumbnail(self.paths[id]))
            if pixmap.isNull():
                from ..rendering.tile_cache import rgb_image
                painting = read_level(self.paths[id])
                pixmap = QPixmap.fromImage(rgb_image(painting.palette[painting.target_map]))
            self.thumbnail_cache[id] = pixmap
        return self.thumbnail_cache[id].scaled(
            width,
            height,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
            if max(self.metadata[id][2:4]) > 512
            else Qt.TransformationMode.FastTransformation,
        )

    def show_home(self):
        self.show_collection()

    def change_language(self, language):
        if language not in LANGUAGES or language == self.settings['language']:
            return
        try:
            self.database.set_settings({'language': language})
        except Exception as exc:
            self.error(tr('Dil kaydedilemedi'), exc)
            self.language_combo.blockSignals(True)
            self.language_combo.setCurrentIndex(self.language_combo.findData(self.settings['language']))
            self.language_combo.blockSignals(False)
            return
        self.settings['language'] = set_language(language)
        # Rebuild the home page using stable category keys and selected painting ID.
        self.show_collection()
        self.statusBar().showMessage(tr('Hazır · Kayıtlar bu cihazda saklanır'))
        self.language_combo.setFocus()

    def show_collection(self):
        from .collection_browser import build_collection

        root = self.page("collection", "", "")
        if root is not None:
            build_collection(self, root)

    def preview_painting(self, id):
        from ..rendering.tile_cache import rgb_image

        try:
            painting = read_level(self.paths[id])
            pixmap = QPixmap.fromImage(rgb_image(painting.palette[painting.target_map]))
            dialog = QDialog(self)
            dialog.setWindowTitle(painting_title(painting.id, painting.title) + tr(" — Önizleme"))
            layout = QVBoxLayout(dialog)
            view = label("")
            view.setAlignment(Qt.AlignmentFlag.AlignCenter)
            available = self.screen().availableGeometry().size()
            view.setPixmap(pixmap.scaled(
                int(available.width() * 0.8), int(available.height() * 0.75),
                Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation,
            ))
            layout.addWidget(view)
            layout.addWidget(button(tr("Kapat"), dialog.accept))
            dialog.exec()
        except Exception as exc:
            self.error(tr("Önizleme açılamadı"), exc)

    def restart_painting(self, id):
        if self.job:
            return
        answer = QMessageBox.question(
            self, tr("Baştan başla"),
            tr("Bu resmin boyama ilerlemesi sıfırlanacak. Baştan başlamak istiyor musun?"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            if not self.leave_game():
                return
            self.saver.flush()
            painting = read_level(self.paths[id])
            with self.database.connect() as con:
                con.execute("DELETE FROM progress WHERE painting_id=?", (id,))
                con.execute("DELETE FROM achievements WHERE id=?", ("complete:" + id,))
            self.show_game((painting, 0, 0))
        except Exception as exc:
            self.error(tr("Resim yeniden başlatılamadı"), exc)

    def export_completed(self, id):
        from ..rendering.tile_cache import rgb_image

        try:
            self.saver.flush()
            painting = read_level(self.paths[id])
            self.database.load(painting)
            if painting.progress < 1:
                raise ValueError(tr("Yalnızca boyaması tamamlanan resimler indirilebilir."))
            name = ''.join(c for c in painting_title(painting.id, painting.title) if c not in '<>:"/\\|?*') or tr('Resim')
            path, _ = QFileDialog.getSaveFileName(self, tr("Tamamlanan resmi indir"), name + '.png', tr("PNG resim (*.png)"))
            if not path:
                return
            if not path.lower().endswith('.png'):
                path += '.png'
            output = QSaveFile(path)
            if not output.open(QIODevice.OpenModeFlag.WriteOnly):
                raise OSError(output.errorString())
            image = rgb_image(painting.palette[painting.target_map])
            if not image.save(output, 'PNG'):
                output.cancelWriting()
                raise OSError(tr("PNG oluşturulamadı"))
            if not output.commit():
                raise OSError(output.errorString())
            self.statusBar().showMessage(tr("Resim PNG olarak kaydedildi."), 5000)
        except Exception as exc:
            self.error(tr("Resim indirilemedi"), exc)

    def open_painting(self, id):
        if self.job:
            return
        if not self.leave_game():
            return
        self.statusBar().showMessage(tr("Resim yükleniyor…"))

        def load():
            painting = read_level(self.paths[id])
            elapsed, selected = self.database.load(painting)
            return painting, elapsed, selected

        self.job = self.worker.submit(load)
        self.job_kind = "load"

    def show_game(self, loaded):
        painting, elapsed, selected = loaded
        session = GameSession(painting)
        session.elapsed_base, session.selected = elapsed, selected
        self.game = GameScreen(session, self.settings, self.debug)
        self.game.back_requested.connect(self.show_collection)
        self.game.save_requested.connect(self.save_game)
        self.stack.addWidget(self.game)
        self.stack.setCurrentWidget(self.game)
        self.sidebar.hide()
        self.game.canvas.setFocus()
        self.statusBar().showMessage(tr("Boyamaya hazır · Ctrl+S: kaydet · Orta fare: taşı"))

    def delete_painting(self, id):
        if self.job:
            self.statusBar().showMessage(tr("Silmeden önce resim işleminin tamamlanmasını bekleyin."), 5000)
            return
        if id not in self.metadata or id.startswith("sample-"):
            return
        answer = QMessageBox.question(
            self,
            tr("Resmi sil"),
            tr('“{title}” ve boyama ilerlemesi silinsin mi?\nBilgisayarınızdaki özgün resim dosyası korunur.',
               title=self.metadata[id][0]),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        try:
            self.saver.flush()
            delete_imported(self.database, id, self.data_dir / "paintings")
            self.thumbnail_cache.pop(id, None)
            self.refresh_library()
            self.show_collection()
            self.statusBar().showMessage(tr("Resim ve boyama ilerlemesi silindi."), 5000)
        except Exception as exc:
            self.error(tr("Resim silinemedi"), exc)

    def save_game(self):
        if self.game:
            # A single ordered writer means an older autosave cannot overwrite a newer one.
            self.saver.save(self.game.session)
            self.statusBar().showMessage(tr("Kaydediliyor…"))

    def poll(self):
        try:
            if self.saver.poll():
                self.statusBar().showMessage(tr("✓ İlerlemen bu cihaza kaydedildi"), 5000)
        except Exception as exc:
            self.error(tr("İlerleme kaydedilemedi"), exc)
        if self.job and self.job.done():
            job, kind = self.job, self.job_kind
            self.job = self.job_kind = None
            try:
                result = job.result()
                if kind == "load":
                    self.show_game(result)
                else:
                    self.refresh_library()
                    self.collection_selected = result
                    self.collection_category = 'İçe aktarılan'
                    self.show_collection()
                    self.statusBar().showMessage(tr("✓ Resim koleksiyonuna eklendi"), 8000)
            except Exception as exc:
                self.error(tr("Resim açılamadı") if kind == "load" else tr("Resim içe aktarılamadı"), exc)

    def import_dialog(self):
        if self.job:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, tr("Resmini seç"), "", tr("Resimler (*.png *.jpg *.jpeg *.webp);;Piksel seviyesi (*.pcolor)")
        )
        if not path:
            return
        from pathlib import Path

        path = Path(path)
        self.statusBar().showMessage(tr("Resim dönüştürülüyor; renk paleti otomatik ayarlanıyor…"))

        def convert():
            import uuid

            if path.suffix.lower() == ".pcolor":
                painting = read_level(path)
                validate_dimensions(painting.width, painting.height)
                # Independent imported copies cannot overwrite existing painting progress.
                painting.id = str(uuid.uuid4())
            else:
                painting = import_image(path)
            dest = self.data_dir / "paintings" / (painting.id + ".pcolor")
            write_level(painting, dest)
            self.database.register(painting, dest)
            return painting.id

        self.job = self.worker.submit(convert)
        self.job_kind = "import"

    def show_settings(self):
        root = self.page("settings", tr("Senin ritmin, senin atölyen."), tr("Tercihlerin bu cihazda saklanır."))
        if root is None:
            return
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        settings_layout = QVBoxLayout(body)
        settings_layout.setContentsMargins(0, 0, 10, 0)
        scroll.setWidget(body)
        root.addWidget(scroll, 1)
        root = settings_layout
        card = QFrame()
        card.setObjectName('settingsCard')
        card.setMaximumWidth(580)
        form = QVBoxLayout(card)
        form.setContentsMargins(24, 20, 24, 24)
        form.setSpacing(12)
        controls = {}
        for key, title in [
            ("grid", tr("Hücre ızgarası")),
            ("numbers", tr("Yakından bakarken numaralar")),
            ("feedback", tr("Yanlış renkte kırmızı geri bildirim")),
            ("sound", tr("Tamamlandığında sistem sesi")),
        ]:
            cb = QCheckBox(title)
            cb.setMinimumHeight(36)
            cb.setChecked(self.settings[key])
            controls[key] = cb
            form.addWidget(cb)
        form.addSpacing(8)
        form.addWidget(label(tr('Otomatik kayıt aralığı')))
        intervals = QButtonGroup(card)
        intervals.setExclusive(True)
        interval_row = QHBoxLayout()
        interval_row.setSpacing(8)
        for minutes in (5, 10, 15, 30):
            choice = button(str(minutes) + tr(' dk'), lambda: None)
            choice.setObjectName('intervalChoice')
            choice.setCheckable(True)
            choice.setMinimumWidth(72)
            choice.setFixedHeight(44)
            intervals.addButton(choice, minutes * 60)
            choice.setChecked(self.settings['autosave'] == minutes * 60)
            interval_row.addWidget(choice)
        interval_row.addStretch()
        form.addLayout(interval_row)
        sliders = {}
        for key, title in [("highlight", tr("Seçili renk vurgusu")), ("grid_opacity", tr("Izgara yoğunluğu"))]:
            form.addSpacing(10)
            heading = QHBoxLayout()
            heading.addWidget(label(title))
            heading.addStretch()
            value = label(f'{round(self.settings[key] * 100)}%')
            value.setObjectName('settingPercent')
            value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            value.setFixedWidth(56)
            heading.addWidget(value)
            form.addLayout(heading)
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setObjectName('settingSlider')
            slider.setProperty('settingKey', key)
            slider.setAccessibleName(title)
            slider.setMinimumHeight(28)
            slider.setRange(0, 100)
            slider.setValue(round(self.settings[key] * 100))
            slider.valueChanged.connect(lambda amount, output=value: output.setText(f'{amount}%'))
            sliders[key] = slider
            form.addWidget(slider)
        root.addWidget(card)

        def apply():
            updated = {key: cb.isChecked() for key, cb in controls.items()}
            updated.update({key: slider.value() / 100 for key, slider in sliders.items()})
            updated["autosave"] = intervals.checkedId()
            try:
                self.database.set_settings(updated)
                self.settings.update(updated)
                self.autosave_timer.start(updated["autosave"] * 1000)
                self.statusBar().showMessage(tr("✓ Ayarlar kaydedildi"), 5000)
            except Exception as exc:
                self.error(tr("Ayarlar kaydedilemedi"), exc)

        root.addWidget(button(tr("Tercihleri kaydet"), apply, True), alignment=Qt.AlignmentFlag.AlignLeft)
        guide = QFrame()
        guide.setObjectName('importGuide')
        guide.setMaximumWidth(580)
        guide.setStyleSheet('QFrame#importGuide {background:#253B3B; border:1px solid #496B62; border-radius:14px;}')
        guide_box = QVBoxLayout(guide)
        guide_box.setContentsMargins(24, 20, 24, 20)
        guide_box.setSpacing(12)
        guide_box.addWidget(label(tr('Kendi resmini ekle'), 'subheading'))
        for text in (
            'Ana sayfadaki resim ekle simgesini kullan. PNG, JPG, JPEG, WEBP ve .pcolor dosyaları desteklenir.',
            'En fazla 1920 piksel genişlik ve 1080 piksel yükseklik: toplam üst sınır 2.073.600 pikseldir. Daha büyük resimleri eklemeden önce küçültmelisin.',
            'Resmin özgün boyutları korunur; her piksel bir boyama hücresi olur. Küçük ve belirgin şekilli resimler daha kolay tamamlanır.',
            'Normal resimlerde renk paleti boyuta göre otomatik belirlenir; hedef 10–60 renktir. Kaynak resimde daha az renk varsa daha az kullanılabilir. Şeffaf alanlar beyaz olur. .pcolor dosyalarının hazır paleti korunur.',
            'Resmin Yüklenenler sekmesine eklenir. Buradan resmi ve boyama kaydını silebilirsin; bilgisayarındaki özgün dosya silinmez.',
        ):
            paragraph = label(tr(text), 'muted')
            paragraph.setWordWrap(True)
            guide_box.addWidget(paragraph)
        root.addWidget(guide)
        root.addWidget(
            label(
                tr("Kısayollar: Ctrl+S kaydet\n"
                "F sığdır · G ızgara · M mini harita · Ok tuşları: resimde gezin\n"
                "Sağ tık: hücrenin rengini seç · Toplu boya: bitişik alanı doldur\n"
                "Orta fare: taşı · Tekerlek: yakınlaştır"),
                "muted",
            )
        )
        root.addStretch()

    def closeEvent(self, event):
        try:
            if self.game:
                self.game.canvas.finish_stroke()
                # Synchronous final write follows every pending background save.
                self.save_game()
            self.saver.flush()
            self.database.set_settings(self.settings)
        except Exception as exc:
            log.exception("Shutdown save failed")
            QMessageBox.critical(
                self,
                tr("Kayıt hatası"),
                tr('Son kayıt tamamlanamadı:\n{error}\nDisk erişimini kontrol edip tekrar deneyin. Oyun açık tutuldu.',
                   error=translate_error(exc)),
            )
            event.ignore()
            return
        self.saver.close()
        self.worker.shutdown(wait=True)
        self.autosave_timer.stop()
        self.poll_timer.stop()
        event.accept()
