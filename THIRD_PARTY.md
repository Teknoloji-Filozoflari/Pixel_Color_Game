# Third-party components

The application's MIT license does not replace third-party licenses.

- CPython 3.13 veya üzeri: PSF lisansı. Kaynak: https://www.python.org/downloads/
- PySide6 Essentials / Qt 6.11.2 and Shiboken6: LGPL/GPL/commercial licensing as detailed
  in their included distribution license files. Website: https://www.qt.io/qt-for-python
  Source archives: https://download.qt.io/official_releases/QtForPython/ and https://download.qt.io/official_releases/qt/
- NumPy 2.5.3: BSD and bundled library notices in its distribution metadata. https://numpy.org/
- Pillow 12.3.0: HPND and bundled library notices in its distribution metadata. https://python-pillow.github.io/
- Noto Sans: SIL Open Font License 1.1, bundled alongside the font in `src/pixel_coloring/resources/fonts/OFL.txt`.
  Source: https://github.com/google/fonts/tree/main/ofl/notosans

The portable distribution uses replaceable dynamic Qt libraries. No restriction is imposed on
replacing those libraries or debugging modifications permitted by their licenses. Full application
source is included. QML, development headers and unused tooling are omitted from the portable runtime.
The sample service installs the bundled collection and contains legacy procedural sample code.

The 536 gallery paintings in `resources/paintings` were created with OpenAI image generation
for this project and converted to indexed color-by-number level data. They do not use the user's
reference screenshot as a distributed game asset. Titles and dimensions are listed in `catalog.json`.

## License copies and source distribution

Redistributed license texts are available in [LICENSES](LICENSES/README.md), including Python,
NumPy, Pillow, Noto Sans and GNU LGPL/GPL texts. The source-only GitHub package does not bundle
the Python/Qt runtime. Its dependency declarations cause the user's package manager to install
those components separately.

Qt for Python distribution metadata declares LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only.
Individual Qt and third-party components have their own terms; consult the
[Qt licensing overview](https://doc.qt.io/qt-6/licensing.html) and
[Qt for Python notices](https://doc.qt.io/qtforpython-6/licenses.html).
The commercial-license reference file supplied by a wheel does not grant a commercial license.

For binary redistribution, preserve component notices and meet the applicable corresponding-source
and replacement requirements. Upstream source locations are listed above; this documentation is
not a blanket certification of compliance for every future binary or store distribution.
