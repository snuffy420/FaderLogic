"""Launch MixLogic."""
import os
import sys

from PyQt6.QtGui import QColor, QIcon, QPalette
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

from mixlogic.main_window import MainWindow
from mixlogic import __version__
from mixlogic.theme import STYLESHEET


def resource_path(relative):
    """Path to a bundled asset, working both from source and inside a PyInstaller build."""
    root = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(root, relative)


def base_dir():
    """Folder holding the cache database: next to the .exe when frozen, else next to this file."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


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
                options.close()
                about = AboutDialog(QIcon(icon_path), icon_path, window)
                assert about.copy_btc_button.text() == "Copy BTC address"
                about.close()
                window.close()
            except Exception:
                app.exit(1)
        QTimer.singleShot(250, check_startup)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
