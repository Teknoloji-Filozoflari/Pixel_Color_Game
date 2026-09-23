"""UI translations; persisted content IDs and titles remain untouched."""
import json
import re
from pathlib import Path

from PySide6.QtCore import QLocale, QTranslator
from PySide6.QtWidgets import QApplication

LANGUAGES = {'tr': 'Türkçe', 'az': 'Azərbaycanca', 'es': 'Español', 'ru': 'Русский', 'en': 'English'}
TRANSLATIONS = json.loads((Path(__file__).resolve().parents[1] / 'resources/translations.json').read_text(encoding='utf-8'))
TITLE_TRANSLATIONS = json.loads((Path(__file__).resolve().parents[1] / 'resources/painting_titles.json').read_text(encoding='utf-8'))
_language = 'tr'
_qt_translator = None


def tr(source, **values):
    text = TRANSLATIONS.get(source, {}).get(_language, source)
    return text.format(**values) if values else text


def painting_title(painting_id, original):
    """Translate bundled titles for display; never rename a user's artwork or save."""
    return TITLE_TRANSLATIONS.get(painting_id, {}).get(_language, original) if _language != 'tr' else original


def number(value, decimals=0):
    return QLocale(_language).toString(float(value), 'f', decimals)


def percentage(value):
    text = number(value, 1)
    return '%' + text if _language == 'tr' else text + '%'


def translate_error(error):
    source = str(error)
    match = re.fullmatch(r'Resim en fazla 1920 × 1080 piksel olabilir. Seçilen resim: (\d+) × (\d+)\.', source)
    if match:
        return tr('Resim en fazla 1920 × 1080 piksel olabilir. Seçilen resim: {width} × {height}.',
                  width=match[1], height=match[2])
    return tr(source)


class DialogTranslator(QTranslator):
    """Translate standard confirmation buttons without external .qm files."""
    captions = {
        'Yes': ('Evet', 'Bəli', 'Sí', 'Да', 'Yes'),
        'No': ('Hayır', 'Xeyr', 'No', 'Нет', 'No'),
        'OK': ('Tamam', 'Oldu', 'Aceptar', 'ОК', 'OK'),
        'Cancel': ('İptal', 'Ləğv et', 'Cancelar', 'Отмена', 'Cancel'),
        'Close': ('Kapat', 'Bağla', 'Cerrar', 'Закрыть', 'Close'),
        'Save': ('Kaydet', 'Yadda saxla', 'Guardar', 'Сохранить', 'Save'),
        'Open': ('Aç', 'Aç', 'Abrir', 'Открыть', 'Open'),
    }

    def isEmpty(self):
        return False

    def translate(self, context, sourceText, disambiguation=None, n=-1):
        if context in ('QPlatformTheme', 'QMessageBox', 'QDialogButtonBox'):
            text = sourceText.replace('&', '')
            if text in self.captions:
                return self.captions[text][['tr', 'az', 'es', 'ru', 'en'].index(_language)]
        return ''


def set_language(language):
    global _language, _qt_translator
    _language = language if language in LANGUAGES else 'tr'
    app = QApplication.instance()
    if app is not None and _qt_translator is None:
        _qt_translator = DialogTranslator(app)
        app.installTranslator(_qt_translator)
    return _language
