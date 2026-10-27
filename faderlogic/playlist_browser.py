"""Collapsible browser for saved Rekordbox imports."""
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem,
    QPushButton, QVBoxLayout,
)

from .theme import COLORS, style_widget


class PlaylistBrowser(QFrame):
    playlistSelected = pyqtSignal(str)
    importRequested = pyqtSignal()
    renameRequested = pyqtSignal(str)
    removeRequested = pyqtSignal(str)
    closeRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("playlistBrowser")
        self.setFixedWidth(230)
        style_widget(self,f"""
            QFrame#playlistBrowser {{ background: {COLORS['panel']};
                border: 1px solid {COLORS['border']}; border-radius: 8px; }}
            QLabel, QLineEdit, QListWidget, QPushButton {{ font-size: 9pt; }}
            QPushButton {{ padding: 4px 8px; }}
            QListWidget {{ background: {COLORS['well']}; border: none; border-radius: 5px; }}
            QListWidget::item {{ padding: 10px 7px; border-bottom: 1px solid {COLORS['border']}; }}
            QListWidget::item:selected {{ background: #1D3550; color: {COLORS['cyan']}; }}
            QListWidget::item:hover {{ background: #26313D; }}
        """)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        heading = QHBoxLayout()
        title = QLabel("Playlists")
        style_widget(title,f"font-weight: bold; color: {COLORS['cyan']};")
        heading.addWidget(title)
        heading.addStretch()
        close = QPushButton("×")
        close.setFixedWidth(26)
        close.setToolTip("Hide playlist browser")
        close.clicked.connect(self.closeRequested)
        heading.addWidget(close)
        layout.addLayout(heading)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Find a saved playlist")
        self.search.textChanged.connect(self._filter)
        layout.addWidget(self.search)
        self.list = QListWidget()
        self.list.setWordWrap(True)
        self.list.currentItemChanged.connect(self._selected)
        layout.addWidget(self.list, 1)
        self.empty = QLabel("Import a Rekordbox playlist once.\nChoose it here whenever you need it.")
        self.empty.setWordWrap(True)
        style_widget(self.empty,f"color: {COLORS['muted']}; font-size: 8pt;")
        layout.addWidget(self.empty)
        self.linked_folder_label = QLabel("Folder: not linked")
        style_widget(self.linked_folder_label,f"color: {COLORS['muted']}; font-size: 8pt;")
        layout.addWidget(self.linked_folder_label)
        add = QPushButton("+ Import playlist")
        add.clicked.connect(self.importRequested)
        layout.addWidget(add)
        actions = QHBoxLayout()
        self.rename_button = QPushButton("Rename")
        self.rename_button.clicked.connect(lambda: self._action(self.renameRequested))
        actions.addWidget(self.rename_button)
        self.remove_button = QPushButton("Remove")
        self.remove_button.setToolTip("Remove this saved entry. Your source files and music are kept.")
        self.remove_button.clicked.connect(lambda: self._action(self.removeRequested))
        actions.addWidget(self.remove_button)
        layout.addLayout(actions)

    def set_playlists(self, entries, active_id):
        self.list.blockSignals(True)
        self.list.clear()
        for entry in entries:
            item = QListWidgetItem(f"{entry['name']}\n{entry['track_count']} tracks")
            item.setData(Qt.ItemDataRole.UserRole, entry["id"])
            item.setData(Qt.ItemDataRole.UserRole + 1, entry["name"])
            metadata_source = entry["source_txt"] or "Editing metadata included in M3U8"
            item.setToolTip(f"{entry['name']}\n{entry['source_m3u8']}\n{metadata_source}\n"
                            f"Music folder: {entry.get('linked_folder') or 'not linked'}")
            self.list.addItem(item)
            if entry["id"] == active_id:
                self.list.setCurrentItem(item)
        self.list.blockSignals(False)
        self.empty.setVisible(not entries)
        self._filter(self.search.text())
        self._update_actions()

    def set_linked_folder(self, folder):
        text = f"Folder: {folder}" if folder else "Folder: not linked"
        self.linked_folder_label.setText(self.linked_folder_label.fontMetrics().elidedText(
            text, Qt.TextElideMode.ElideMiddle, self.width() - 22))
        self.linked_folder_label.setToolTip(folder or "Choose a music folder using Relink Folder.")

    def _filter(self, text):
        for row in range(self.list.count()):
            item = self.list.item(row)
            item.setHidden(text.casefold() not in item.data(Qt.ItemDataRole.UserRole + 1).casefold())
        self._update_actions()

    def _selected(self, item, _previous):
        self._update_actions()
        if item is not None:
            self.playlistSelected.emit(item.data(Qt.ItemDataRole.UserRole))

    def _update_actions(self):
        item = self.list.currentItem()
        enabled = item is not None and not item.isHidden()
        self.rename_button.setEnabled(enabled)
        self.remove_button.setEnabled(enabled)

    def _action(self, signal):
        item = self.list.currentItem()
        if item and not item.isHidden():
            signal.emit(item.data(Qt.ItemDataRole.UserRole))
