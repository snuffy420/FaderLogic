"""Custom dark title bar: icon, app name, version and window controls."""
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from .theme import COLORS


class TitleBar(QWidget):
    """Draggable title bar that replaces the Windows frame."""

    def __init__(self, window, icon_path, title, version, parent=None, inline=False):
        super().__init__(parent)
        self._window = window
        self._drag_offset = None
        self.setObjectName("titleBar")
        if inline:
            self.setMinimumHeight(34)
        else:
            self.setFixedHeight(34)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 0, 0)
        layout.setSpacing(8)

        if not inline:
            icon = QLabel()
            icon.setPixmap(QIcon(icon_path).pixmap(18, 18))
            layout.addWidget(icon)
            name = QLabel(title)
            name.setObjectName("titleName")
            layout.addWidget(name)
            layout.addStretch()
            self.add_window_controls()

        self.setStyleSheet(
            f"QWidget#titleBar {{ background-color: #0B0C0E; }}"
            f"QLabel#titleName {{ color: {COLORS['text']}; font-size: 10pt; font-weight: 700; }}"
            f"QLabel#titleVersion {{ color: {COLORS['muted']}; font-size: 9pt; }}"
            f"QPushButton#winBtn, QPushButton#winClose {{ background: transparent; border: none;"
            f" border-radius: 0; padding: 0; min-width: 46px; max-width: 46px; min-height: 34px;"
            f" color: {COLORS['text']}; font-size: 10pt; }}"
            f"QPushButton#winBtn:hover {{ background: #2A3340; color: #FFFFFF; }}"
            f"QPushButton#winClose:hover {{ background: #C42B1C; color: #FFFFFF; }}"
        )

    def add_window_controls(self):
        is_dialog = hasattr(self._window, "reject") and not hasattr(self._window, "library")
        close_slot = self._window.reject if is_dialog else self._window.close
        buttons = [("\u2013", self._window.showMinimized, "winBtn")]
        if not is_dialog:
            buttons.append(("\u2751", self._toggle_max, "winBtn"))
        buttons.append(("\u2715", close_slot, "winClose"))
        for text, slot, object_name in buttons:
            btn = QPushButton(text)
            btn.setObjectName(object_name)
            btn.setFixedWidth(38)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(slot)
            self.layout().addWidget(btn)

    def _toggle_max(self):
        if self._window.isMaximized():
            self._window.showNormal()
        else:
            self._window.showMaximized()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_offset = event.globalPosition().toPoint() - self._window.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_offset is not None and event.buttons() & Qt.MouseButton.LeftButton:
            if self._window.isMaximized():
                self._window.showNormal()
            self._window.move(event.globalPosition().toPoint() - self._drag_offset)

    def mouseReleaseEvent(self, _event):
        self._drag_offset = None

    def mouseDoubleClickEvent(self, _event):
        self._toggle_max()
