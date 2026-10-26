"""Launch MixLogic."""
import os
import sys

from PyQt6.QtGui import QColor, QIcon, QPalette
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from mixlogic.main_window import MainWindow
from mixlogic import __version__
from mixlogic.theme import STYLESHEET
from mixlogic.paths import runtime_data_dir


def resource_path(relative):
    """Path to a bundled asset, working both from source and inside a PyInstaller build."""
    root = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, relative)


def base_dir():
    return runtime_data_dir()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MixLogic")
    app.setApplicationDisplayName(f"MixLogic {__version__}")
    palette = app.palette()
    for role in (QPalette.ColorRole.Window, QPalette.ColorRole.Base, QPalette.ColorRole.AlternateBase):
        palette.setColor(role, QColor("#16181C"))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)
    icon_path = resource_path("assets/mixlogic.ico")
    app.setWindowIcon(QIcon(icon_path))
    window = MainWindow(base_dir(), icon_path)
    window.showMaximized()
    if "--smoke-test" in sys.argv:
        # Exercise the frozen application's real startup and toolbar connection.
        def check_startup():
            try:
                initial = window.btn_playlists.isChecked()
                window.btn_playlists.click()
                app.processEvents()
                assert window.playlist_browser.isVisible() != initial
                window.btn_playlists.click()
                app.processEvents()
                assert window.playlist_browser.isVisible() == initial
                # Check frozen QR/Pillow dependencies and both Options pages.
                from mixlogic.dialogs import AboutDialog, OptionsDialog
                options = OptionsDialog(window.wheel, icon_path, window)
                assert ("library", "Artist") in options.column_checks
                from mixlogic.appearance import WHEEL_STYLES, WAVE_STYLES, WAVE_MODES
                options.show()
                for style in WHEEL_STYLES:
                    options.appearance.wheel_choice.setCurrentIndex(options.appearance.wheel_choice.findData(style))
                    app.processEvents()
                    assert not options.appearance.wheel_preview.grab().isNull()
                for style in WAVE_STYLES:
                    for mode in WAVE_MODES:
                        options.appearance.wave_choice.setCurrentIndex(options.appearance.wave_choice.findData(style))
                        options.appearance.mode_choice.setCurrentIndex(options.appearance.mode_choice.findData(mode))
                        app.processEvents()
                        assert not options.appearance.wave_preview.grab().isNull()
                options.apply_button.click()
                assert window.wheel.visual_style == list(WHEEL_STYLES)[-1]
                assert window.waveform.visual_style == list(WAVE_STYLES)[-1]
                from mixlogic.theme import current_theme
                for theme_name in ('light','dark'):
                    options.appearance.theme_choice.setCurrentIndex(options.appearance.theme_choice.findData(theme_name))
                    options.apply_button.click()
                    app.processEvents()
                    assert current_theme()==theme_name
                    assert window.store.load_session()['appearance']['theme']==theme_name
                options.close()
                about = AboutDialog(QIcon(icon_path), icon_path, window)
                assert about.copy_btc_button.text() == "Copy BTC address"
                about.close()
                window.close()
            except Exception:
                import traceback
                from pathlib import Path
                Path(base_dir(),'.smoke-test-error.txt').write_text(traceback.format_exc(),encoding='utf-8')
                app.exit(1)
        QTimer.singleShot(250, check_startup)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
