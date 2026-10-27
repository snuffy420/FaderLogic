# Third-party software

FaderLogic application code and original graphics are GPL-3.0-or-later. Third-party software retains its own copyright and license terms. License texts from the release build environment are included in `licenses/`.

| Component | Release version | License / upstream source |
| --- | --- | --- |
| Python | 3.12.6 | PSF license and included notices; [source](https://www.python.org/downloads/release/python-3126/) |
| PyQt6 | 6.11.0 | GPLv3; [Riverbank](https://www.riverbankcomputing.com/software/pyqt/) and [distribution files](https://pypi.org/project/PyQt6/6.11.0/#files) |
| Qt runtime | 6.11.2 | LGPLv3/GPL terms and module-specific third-party notices; [Qt source archive](https://download.qt.io/archive/qt/6.11/6.11.2/) and [Qt licensing](https://doc.qt.io/qt-6/licensing.html) |
| PyQt6-sip | 13.12.0 | BSD-style SIP license; [distribution](https://pypi.org/project/PyQt6-sip/13.12.0/) |
| Pillow | 11.3.0 | HPND/PIL license and bundled-library notices in its included license file; [source](https://github.com/python-pillow/Pillow/tree/11.3.0) |
| qrcode | 8.2 | BSD 3-Clause; [source](https://github.com/lincolnloop/python-qrcode) |
| Qt Multimedia's FFmpeg libraries | 7.1.5 | LGPL-2.1-or-later for the supplied build, plus component notices; [exact source tag](https://github.com/FFmpeg/FFmpeg/tree/n7.1.5) |
| PyInstaller bootloader/runtime | 6.18.0 | GPL with the PyInstaller bootloader exception; [source](https://github.com/pyinstaller/pyinstaller/tree/v6.18.0) |
| Inno Setup installer runtime | 7.1.0 | Inno Setup license, included as `licenses/InnoSetup-LICENSE.txt`; [source](https://github.com/jrsoftware/issrc/tree/is-7_1_0) |

`licenses/runtime-manifest.json` records the installed package versions, the bundled FFmpeg version/license/configuration and SHA-256 hashes of its audio libraries. The audio libraries come from the unmodified Qt runtime wheel; FaderLogic does not bundle a separate FFmpeg command-line executable. The recorded configuration does not enable GPL FFmpeg components.

The Qt runtime includes additional third-party code for functionality such as images, fonts, PDFs, audio, TLS and compression. Its applicable upstream module notices are part of the dependency sources; see [licenses used in Qt](https://doc.qt.io/qt-6/licenses-used-in-qt.html). Python's Windows distribution also includes support libraries and their notices in `licenses/Python-LICENSE.txt`. Microsoft runtime DLLs remain governed by their own redistribution terms.

Pillow is used at runtime for donation QR image generation. Notebook, NumPy and plotting integrations are not required by FaderLogic and are excluded from the public executable's build graph. 7-Zip is used only to create/test release archives; it is not bundled with or required by the application.

The source package contains FaderLogic source and build materials. It is not a complete mirror of every third-party dependency's corresponding source. Preserve the included notices and meet the applicable source/redistribution requirements when publishing binaries; see [publishing notes](docs/PUBLISHING.md). Upstream source links alone are not a claim that those requirements have already been fulfilled for every dependency.
