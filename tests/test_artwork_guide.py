"""Guide coverage, place matching and on-screen source attribution."""

from urllib.parse import urlparse

import numpy as np
import pytest
from PySide6.QtWidgets import QLabel

from pixel_coloring.core.painting import Painting
from pixel_coloring.ui.artwork_info import FACTS, ArtworkInfoDialog, artwork_fact


def test_every_turkey_and_wonder_painting_has_its_own_guide_entry():
    assert len(FACTS) == 172
    assert sum(id.startswith('sample-turkiye-') for entry in FACTS for id in entry['paintings']) == 81
    assert sum(id.startswith('sample-harikalar-') for entry in FACTS for id in entry['paintings']) == 91
    assert all(len(entry['paintings']) == 1 for entry in FACTS)
    assert artwork_fact('user-personal-image') is None
    assert artwork_fact('sample-arabalar-001') is None


@pytest.mark.parametrize('id,place,wrong', [
    ('sample-turkiye-izmir-01-v1', 'Saat Kulesi', 'Efes'),
    ('sample-turkiye-sanliurfa-01-v1', 'Balıklıgöl', 'Göbeklitepe'),
    ('sample-turkiye-istanbul-01-v1', 'Ortaköy', 'Ayasofya'),
    ('sample-harikalar-079', 'Hawa Mahal', 'Amber'),
    ('sample-turkiye-tokat-01-v1', 'Ballıca', 'Karaca'),
])
def test_card_describes_landmark_in_image_instead_of_unrelated_city_fact(id, place, wrong):
    entry = artwork_fact(id)
    assert place in entry['place']
    assert place in entry['text']
    assert wrong not in entry['text']


def test_sources_are_direct_https_links_with_named_publishers():
    for entry in FACTS:
        url = urlparse(entry['source'])
        assert url.scheme == 'https' and url.hostname
        assert url.path not in ('', '/')
        assert '/search' not in url.path and '/arama' not in url.path
        assert entry['checked'] == '2026-10-18'
        assert entry['source_name'].strip()
        if 'unesco.org' in url.hostname:
            assert entry['source_name'] == 'UNESCO Dünya Mirası Merkezi'


@pytest.mark.parametrize('id', ['sample-turkiye-izmir-01-v1', 'sample-turkiye-tokat-01-v1',
                              'sample-harikalar-041', 'sample-harikalar-079'])
def test_dialog_leads_with_place_description_and_labels_actual_source(app, id):
    entry = artwork_fact(id)
    p = Painting(id, 'Title', np.array([[1, 2, 3]]), np.zeros((2, 3), dtype=np.uint8))
    dialog = ArtworkInfoDialog(p)
    try:
        dialog.show()
        app.processEvents()
        place = dialog.findChild(QLabel, 'artworkPlace')
        text = dialog.findChild(QLabel, 'artworkFactText')
        source = dialog.findChild(QLabel, 'artworkFactSource')
        assert place.text() == entry['place']
        assert text.text() == entry['text']
        assert text.y() > place.y()
        assert source.y() > text.y()
        assert entry['source'] in source.text()
        assert entry['source_name'] in source.text()
        assert source.openExternalLinks()
        labels = dialog.findChildren(QLabel)
        technical = next(label for label in labels if label.text().startswith('Boyut:'))
        assert technical.y() > source.y()
    finally:
        dialog.close()
        dialog.deleteLater()
