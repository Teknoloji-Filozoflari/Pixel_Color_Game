"""Offline artwork cards; only curated entries carry historical claims."""

import json
from html import escape
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QDialogButtonBox, QLabel, QScrollArea, QVBoxLayout, QWidget

from .i18n import number, painting_meaning, painting_title, percentage, tr
from .widgets import label

RESOURCE = Path(__file__).resolve().parents[1] / 'resources/artwork_facts.json'
FACTS = json.loads(RESOURCE.read_text(encoding='utf-8'))
FACTS_BY_PAINTING = {id: entry for entry in FACTS for id in entry['paintings']}


def artwork_fact(painting_id):
    return FACTS_BY_PAINTING.get(painting_id)


class ArtworkInfoDialog(QDialog):
    def __init__(self, painting, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr('Resim hakkında'))
        self.resize(600, 520)
        root = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        body = QWidget()
        content = QVBoxLayout(body)

        def paragraph(text, role=''):
            widget = label(text, role)
            widget.setTextFormat(Qt.TextFormat.PlainText)
            widget.setWordWrap(True)
            widget.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            content.addWidget(widget)
            return widget

        paragraph(painting_title(painting.id, painting.title), 'subheading')
        paragraph(tr(painting.category), 'muted')
        fact = artwork_fact(painting.id)
        if fact:
            paragraph(tr('Mekânı tanı'), 'muted')
            place = paragraph(fact['place'], 'subheading')
            place.setObjectName('artworkPlace')
            place.setStyleSheet('font-size:17px; font-weight:600;')
            text = paragraph(tr(fact['text']))
            text.setObjectName('artworkFactText')
            source = QLabel('<a style="color:#93E1CF" href="' + escape(fact['source'], quote=True) + '">' +
                            escape(tr('Kaynak: {name}', name=fact['source_name'])) + '</a>')
            source.setObjectName('artworkFactSource')
            source.setOpenExternalLinks(True)
            source.setWordWrap(True)
            content.addWidget(source)
            content.addSpacing(14)
        paragraph(tr('Boyut: {width} × {height} · {cells} hücre',
                     width=number(painting.width), height=number(painting.height),
                     cells=number(painting.target_map.size)))
        paragraph(tr('Kullanılan renk: {colors} · Tamamlanma: {progress}',
                     colors=number((painting.totals > 0).sum()), progress=percentage(painting.progress * 100)))
        if painting.author:
            paragraph(tr('Hazırlayan: {author}', author=painting.author), 'muted')
        if painting.meaning:
            paragraph(painting_meaning(painting.id, painting.meaning))
        if not fact and not painting.meaning:
            paragraph(tr('Bu resim için ek açıklama bulunmuyor.'), 'muted')
        if painting.id.startswith('sample-') and painting.category in ('Harikalar', 'TÜRKİYE'):
            paragraph(tr('Görsel, konunun sanatsal yorumudur.'), 'muted')
        content.addStretch()
        scroll.setWidget(body)
        root.addWidget(scroll)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.button(QDialogButtonBox.StandardButton.Close).setText(tr('Kapat'))
        buttons.rejected.connect(self.reject)
        root.addWidget(buttons)
