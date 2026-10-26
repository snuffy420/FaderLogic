"""MixLogic main window: library panel, playlist builder, player and set timer."""
import os
import sqlite3

from PyQt6.QtCore import QByteArray, QSignalBlocker, QTimer, QUrl, Qt
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtWidgets import (
    QAbstractItemView, QFileDialog, QFrame, QHBoxLayout, QHeaderView, QLabel,
    QLineEdit, QMainWindow, QPushButton, QSizePolicy, QSlider,
    QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QSplitter,
    QScrollArea,
)

from . import playlist
from . import __version__
from . import camelot
from .camelot import REAL_KEYS, VARIATIONS, camelot_sort_key, get_compatibility, normalize_key
from .theme import COLORS, style_widget, current_theme, apply_theme, palette_for
from .titlebar import TitleBar
from .dialogs import AboutDialog, OptionsDialog, MetadataReviewDialog, StyledInputDialog as QInputDialog, StyledMessageBox as QMessageBox
from .appearance import clean_appearance, RELATION_CODES, accessible_legend, standard_legend, wheel_legend_html
from .playlist_browser import PlaylistBrowser
from .storage import LibraryStore, track_snapshot
from .waveform import WaveformCache, WaveformWorker
from .widgets import CamelotWheelWidget, TrackDetailsWidget, WaveformWidget

APP_NAME = "MixLogic"
ROW_COLOURS = {
    "green": QColor(20, 74, 40),
    "orange": QColor(84, 52, 14),
    "red": QColor(70, 22, 28),
    "selected": QColor(29, 53, 80),
    "unknown": QColor(38, 41, 48),
}


def relation_tint(label, colour_status, show_all):
    """Row colour for a relation: per-variation tint when show_all is on, else green/orange/red."""
    if show_all and label in VARIATIONS:
        return QColor(*VARIATIONS[label][1])
    return ROW_COLOURS[colour_status]


def _card(title=None):
    frame = QFrame()
    frame.setObjectName("card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(12, 10, 12, 12)
    if title:
        label = QLabel(title)
        label.setObjectName("sectionTitle")
        layout.addWidget(label)
    return frame, layout


class MainWindow(QMainWindow):
    """A large Camelot wheel beside the library and active set."""

    def __init__(self, base_dir, icon_path):
        super().__init__()
        self._icon_path = icon_path
        self.setWindowTitle(f"{APP_NAME} {__version__}")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setMinimumSize(1100, 700)
        self.resize(1480, 920)
        self.library = []          # all imported tracks
        self.active_set = []       # tracks in the set being built
        self.worker = None
        self._wave_workers = set()
        self._preview_source = "library"
        self._preview_track = None
        self.store = LibraryStore(os.path.join(base_dir, "MixLogic-data"))
        self.active_playlist_id = None
        self.active_playlist_name = None
        self.linked_folder = None
        self._restoring = True
        self._fitting_columns = False
        self._save_error_shown = False
        self._closed = False
        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(250)
        self._save_timer.timeout.connect(self._save_session)

        self.cache = WaveformCache(os.path.join(base_dir, "waveform_cache.db"))
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.audio.setVolume(0.8)
        self.player.setAudioOutput(self.audio)
        self.player.positionChanged.connect(self._on_position)

        self._build_ui()
        self._restore_session()
        self._restoring = False
        self._refresh_status()

    # ---------- UI construction ----------
    def _build_ui(self):
        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)
        frame = QVBoxLayout(root)
        frame.setContentsMargins(0, 0, 0, 0)
        frame.setSpacing(0)
        body = QWidget()
        body.setObjectName("body")
        outer = QVBoxLayout(body)
        outer.setContentsMargins(14, 2, 14, 10)
        outer.setSpacing(10)
        frame.addWidget(body, 1)

        toolbar = TitleBar(self, self._icon_path, "", "", inline=True)
        toolbar.setObjectName("toolbar")
        style_widget(toolbar,toolbar.styleSheet() +
            "QWidget#toolbar QPushButton { font-size: 9pt; padding: 3px 8px; }"
        )
        top = toolbar.layout()
        top.setContentsMargins(0, 0, 0, 0)
        top.setSpacing(6)
        tile = QFrame()
        tile.setObjectName("logoTile")
        tile_layout = QHBoxLayout(tile)
        tile_layout.setContentsMargins(4, 4, 4, 4)
        logo = QLabel()
        logo.setPixmap(QIcon(self._icon_path).pixmap(24, 24))
        tile_layout.addWidget(logo)
        top.addWidget(tile)
        top.addSpacing(4)
        title = QLabel(APP_NAME)
        title.setObjectName("brandTitle")
        style_widget(title,"font-size: 13pt;")
        top.addWidget(title)
        version = QLabel(__version__)
        version.setObjectName("brandVersion")
        style_widget(version,"font-size: 9pt;")
        top.addWidget(version)
        top.addSpacing(12)
        self.btn_playlists = QPushButton("Playlists")
        self.btn_playlists.setObjectName("playlistToggle")
        self.btn_playlists.setCheckable(True)
        self.btn_playlists.setToolTip("Show or hide saved Rekordbox playlists")
        self.btn_playlists.toggled.connect(self._toggle_playlist_browser)
        top.addWidget(self.btn_playlists)
        self.btn_import = QPushButton("Import Playlist")
        self.btn_import.setToolTip("Import a Rekordbox M3U8 + TXT pair, or reopen a MixLogic exported M3U8")
        self.btn_import.clicked.connect(self.import_playlist)
        self.btn_relink = QPushButton("Relink Folder")
        self.btn_relink.setObjectName("relinkFolder")
        self.btn_relink.setCheckable(True)
        self.btn_relink.setEnabled(False)
        self.btn_relink.clicked.connect(self.relink_folder)
        self.btn_export = QPushButton("Export Set (.m3u8)")
        self.btn_export.setObjectName("primary")
        self.btn_export.setToolTip("Import the exported playlist in Rekordbox via File → Import → Import Playlist")
        self.btn_export.clicked.connect(self.export_set)
        for b in (self.btn_import, self.btn_relink, self.btn_export):
            top.addWidget(b)
        top.addStretch()
        top.addSpacing(6)
        self.btn_play = QPushButton("Play")
        self.btn_play.setObjectName("playTransport")
        self.btn_play.setToolTip("Play or pause the selected track")
        self.btn_play.clicked.connect(self._toggle_play)
        self.btn_stop = QPushButton("Stop")
        self.btn_stop.setObjectName("stopTransport")
        self.btn_stop.setToolTip("Stop playback and return to the beginning")
        self.btn_stop.clicked.connect(self._stop)
        top.addWidget(self.btn_play)
        top.addWidget(self.btn_stop)
        top.addStretch()
        top.addSpacing(6)
        self.btn_options = QPushButton("Options")
        self.btn_options.clicked.connect(self.show_options)
        top.addWidget(self.btn_options)
        self.btn_about = QPushButton("About")
        self.btn_about.clicked.connect(self.show_about)
        top.addWidget(self.btn_about)
        toolbar.add_window_controls()
        outer.addWidget(toolbar)

        outer.addWidget(self._build_waveform_strip())

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.addWidget(self._build_left_panel())
        self.splitter.addWidget(self._build_right_panel())
        self._wheel_auto_size = True
        self.splitter.splitterMoved.connect(self._on_splitter_moved)
        workspace = QHBoxLayout()
        workspace.setContentsMargins(0, 0, 0, 0)
        workspace.setSpacing(10)
        self.playlist_browser = PlaylistBrowser()
        self.playlist_browser.playlistSelected.connect(self._activate_playlist)
        self.playlist_browser.importRequested.connect(self.import_playlist)
        self.playlist_browser.renameRequested.connect(self._rename_playlist)
        self.playlist_browser.removeRequested.connect(self._remove_playlist)
        self.playlist_browser.closeRequested.connect(lambda: self.btn_playlists.setChecked(False))
        self.playlist_browser.hide()
        workspace.addWidget(self.playlist_browser)
        workspace.addWidget(self.splitter, 1)
        outer.addLayout(workspace, 1)

        footer = QWidget()
        footer.setObjectName("footer")
        style_widget(footer,
            "QWidget#footer QLabel, QWidget#footer QLineEdit, QWidget#footer QSpinBox "
            "{ font-size: 8pt; }"
            "QWidget#footer QLineEdit { padding: 3px 8px; }"
            "QWidget#footer QSpinBox { padding: 2px 6px; }"
        )
        bottom = QHBoxLayout(footer)
        bottom.setContentsMargins(0, 0, 0, 0)
        self.lbl_counts = QLabel()
        self.lbl_counts.setObjectName("hint")
        bottom.addWidget(self.lbl_counts)
        self.btn_metadata = QPushButton("Metadata")
        style_widget(self.btn_metadata,f"font-size:8pt;padding:2px 6px;color:{COLORS['muted']};")
        self.btn_metadata.setToolTip("Missing values are shown as Unknown in each table. Click to review details.")
        self.btn_metadata.clicked.connect(self.show_metadata_details)
        self.btn_metadata.hide()
        bottom.addWidget(self.btn_metadata)
        bottom.addStretch()
        self.right_footer = QWidget()
        right = QHBoxLayout(self.right_footer)
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(8)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search library")
        self.search.setMinimumWidth(100)
        self.search.textChanged.connect(self._apply_filter)
        right.addWidget(self.search, 1)
        mix_label = QLabel("Transition Time")
        right.addWidget(mix_label)
        self.overlap = QSpinBox()
        self.overlap.setRange(0, 120)
        self.overlap.setSuffix(" s")
        self.overlap.setValue(15)
        self.overlap.setToolTip("Seconds each transition overlaps. Subtracted from the set length.")
        self.overlap.valueChanged.connect(self._update_set_time)
        right.addWidget(self.overlap)
        right.addSpacing(8)
        self.lbl_set_time = QLabel()
        style_widget(self.lbl_set_time,f"color: {COLORS['neon_green']}; font-weight: bold; font-size: 8pt;")
        right.addWidget(self.lbl_set_time)
        bottom.addWidget(self.right_footer)
        outer.addWidget(footer)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Wait until layouts have their new geometry before sizing the wheel column.
        QTimer.singleShot(0, self._size_wheel_column)

    def _size_wheel_column(self):
        if not self._wheel_auto_size:
            self._fit_table_columns()
            self._align_right_footer()
            return
        available = self.splitter.width() - self.splitter.handleWidth()
        right_minimum = self.splitter.widget(1).minimumWidth()
        # A square wheel area uses all available height without taking table space.
        wheel_width = min(self.splitter.height() + 6, available - right_minimum)
        wheel_width = max(self.splitter.widget(0).minimumSizeHint().width(), wheel_width)
        self.splitter.setSizes([wheel_width, max(right_minimum, available - wheel_width)])
        self._fit_table_columns()
        self._align_right_footer()

    def _align_right_footer(self):
        if hasattr(self, "right_footer"):
            self.right_footer.setFixedWidth(max(520, self.splitter.widget(1).width() - 6))

    def _on_splitter_moved(self, _position, _index):
        self._wheel_auto_size = False
        QTimer.singleShot(0, self._fit_table_columns)
        QTimer.singleShot(0, self._align_right_footer)

    def _build_waveform_strip(self):
        # Full-width waveform above the three panels. No title, so it takes less height.
        card, layout = _card()
        layout.setContentsMargins(8, 6, 8, 6)
        self.waveform = WaveformWidget()
        self.waveform.setFixedHeight(48)
        self.waveform.scrubRequested.connect(self._scrub)
        layout.addWidget(self.waveform)
        details = QHBoxLayout()
        self.track_details = TrackDetailsWidget()
        details.addWidget(self.track_details, 1)
        self.lbl_relation = QLabel("Relation: select a track")
        style_widget(self.lbl_relation,f"font-size: 9pt; color: {COLORS['muted']};")
        self.lbl_relation.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Preferred)
        details.addWidget(self.lbl_relation)
        layout.addLayout(details)
        return card

    def _build_left_panel(self):
        # The wheel fills the largest square beside the track tables.
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(8)

        wheel_card, wheel_layout = _card()
        self.wheel = CamelotWheelWidget()
        self.wheel.showAllChanged.connect(self._on_show_all_changed)
        wheel_layout.addWidget(self.wheel)
        self.wheel_legend = QLabel()
        self.wheel_legend.setWordWrap(True)
        style_widget(self.wheel_legend,"font-size:8pt;color:#E4E7EC;")
        self.wheel_legend.hide()
        wheel_layout.addWidget(self.wheel_legend)
        layout.addWidget(wheel_card, 1)
        return panel

    def _build_right_panel(self):
        panel = QWidget()
        panel.setMinimumWidth(560)
        style_widget(panel,
            "QPushButton, QTableWidget, QHeaderView::section { font-size: 9pt; }"
            "QPushButton { padding: 4px 10px; }"
            "QHeaderView::section { padding: 4px; }"
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(6, 0, 0, 0)
        layout.setSpacing(8)

        lib_card, lib_layout = _card()
        lib_layout.setContentsMargins(8, 8, 8, 8)
        self.lib_table = self._make_table(["Title", "Artist", "BPM", "Camelot", "Key", "Time"])
        self.lib_table.setSortingEnabled(True)
        self.lib_table.model().layoutChanged.connect(lambda *_: self._sync_metadata_markers(self.lib_table))
        self.lib_table.itemSelectionChanged.connect(self._on_library_selected)
        self.lib_table.cellClicked.connect(lambda *_: self._on_library_selected())
        lib_layout.addWidget(self.lib_table)
        library_group = QWidget()
        library_group_layout = QVBoxLayout(library_group)
        library_group_layout.setContentsMargins(0, 0, 0, 0)
        library_group_layout.setSpacing(8)
        library_group_layout.addWidget(lib_card, 1)

        self.btn_add = QPushButton("Add Selected Track to Set")
        self.btn_add.setObjectName("primary")
        self.btn_add.clicked.connect(self.add_selected_to_set)
        library_group_layout.addWidget(self.btn_add)

        set_card, set_layout = _card()
        set_layout.setContentsMargins(8, 8, 8, 8)
        self.set_table = self._make_table(["#", "Title", "Artist", "BPM", "Camelot", "Key", "Time"])
        self.set_table.setDragDropMode(QAbstractItemView.DragDropMode.NoDragDrop)
        self.set_table.itemSelectionChanged.connect(self._on_set_selected)
        self.set_table.cellClicked.connect(lambda *_: self._on_set_selected())
        set_layout.addWidget(self.set_table)
        btns = QHBoxLayout()
        for text, slot in (("Move Up", self.move_up), ("Move Down", self.move_down),
                           ("Remove", self.remove_selected), ("Clear Set", self.clear_set)):
            b = QPushButton(text)
            b.clicked.connect(slot)
            btns.addWidget(b)
        btns.addStretch()
        set_layout.addLayout(btns)
        self.table_splitter = QSplitter(Qt.Orientation.Vertical)
        self.table_splitter.setObjectName("tableSplitter")
        self.table_splitter.setChildrenCollapsible(False)
        self.table_splitter.setHandleWidth(10)
        self.table_splitter.addWidget(library_group)
        self.table_splitter.addWidget(set_card)
        self.table_splitter.setSizes([300, 300])
        self.table_splitter.splitterMoved.connect(self._queue_save_session)
        self.table_splitter.handle(1).setToolTip("Drag to resize the library and set tables")
        layout.addWidget(self.table_splitter, 1)
        return panel

    def _make_table(self, headers):
        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(False)
        table.verticalHeader().setVisible(True)
        table.verticalHeader().setFixedWidth(18)
        style_widget(table.verticalHeader(),"QHeaderView::section { background:#121417; color:#FF9A2E; border:none; padding:0px; font-size:9pt; font-weight:700; }")
        table.verticalHeader().setToolTip("! marks missing metadata. Hover for details; double-click to review.")
        table.verticalHeader().sectionDoubleClicked.connect(lambda *_: self.show_metadata_details())
        table.setShowGrid(False)
        table.setTextElideMode(Qt.TextElideMode.ElideRight)
        table.verticalHeader().setMinimumSectionSize(24)
        table.verticalHeader().setDefaultSectionSize(24)
        table.setMinimumHeight(4 * 24 + 32 + 12)
        header = table.horizontalHeader()
        header.setMinimumSectionSize(28)
        header.setStretchLastSection(False)
        header.setToolTip("Drag the boundary between column headings to resize a column")
        widths = {"#": 32, "Title": 240, "Artist": 160, "BPM": 46, "Camelot": 64, "Key": 54, "Time": 52}
        for column, name in enumerate(headers):
            header.setSectionResizeMode(column, QHeaderView.ResizeMode.Interactive)
            if name in widths:
                table.setColumnWidth(column, widths[name])
        table.setProperty("custom_columns", False)
        header.sectionResized.connect(lambda *_: self._on_column_resized(table))
        return table

    def _on_column_resized(self, table):
        if not self._fitting_columns and not self._restoring:
            table.setProperty("custom_columns", True)
            self._queue_save_session()

    def _fit_table_columns(self):
        # Fit untouched defaults; a user's resized columns stay exactly as chosen.
        self._fitting_columns = True
        try:
            for table in (self.lib_table, self.set_table):
                if table.property("custom_columns"):
                    continue
                title = 1 if table is self.set_table else 0
                artist = title + 1
                fixed = sum(table.columnWidth(c) for c in range(table.columnCount())
                            if c not in (title, artist) and not table.isColumnHidden(c))
                space = max(160, table.viewport().width() - fixed - 2)
                visible = [c for c in (title, artist) if not table.isColumnHidden(c)]
                if len(visible) == 2:
                    table.setColumnWidth(title, int(space * 0.6))
                    table.setColumnWidth(artist, space - int(space * 0.6))
                elif visible:
                    table.setColumnWidth(visible[0], space)
        finally:
            self._fitting_columns = False

    # ---------- helpers ----------
    def set_column_visible(self, table_name, column, visible):
        table = self.lib_table if table_name == "library" else self.set_table
        remaining = sum(not table.isColumnHidden(c) for c in range(table.columnCount()))
        if not visible and not table.isColumnHidden(column) and remaining <= 1:
            return False
        with QSignalBlocker(table.horizontalHeader()):
            table.setColumnHidden(column, not visible)
        self._fit_table_columns()
        self._queue_save_session()
        return True

    def _refresh_status(self):
        self.lbl_counts.setText(f"Library: {len(self.library)} tracks   |   Set: {len(self.active_set)} tracks")
        self.lbl_counts.setToolTip(f"Current playlist: {self.active_playlist_name}"
                                  if self.active_playlist_name else "No saved playlist selected")
        self._update_set_time()
        bad_library = [track for track in self.library if playlist.metadata_issues(track)]
        bad_set = [track for track in self.active_set if playlist.metadata_issues(track)]
        self.btn_metadata.setVisible(bool(bad_library or bad_set))
        self.btn_metadata.setText(f"Metadata · {len(bad_library) + len(bad_set)}")
        self.btn_metadata.setToolTip(f"Missing fields in {len(bad_library)} library rows and {len(bad_set)} set rows. "
                                     "Unknown cells and ! row markers identify them. Click for details.")
        self._queue_save_session()

    # ---------- saved playlists and preferences ----------
    def _queue_save_session(self, *_):
        if not self._restoring and not self._closed:
            self._save_timer.start()

    def _save_session(self):
        self._save_timer.stop()
        if self._closed:return True
        selected = self._selected_library_track()
        state = {
            "active_playlist_id": self.active_playlist_id,
            "active_set": track_snapshot(self.active_set),
            "selected_path": selected["path"] if selected else None,
            "chart": camelot.active_chart_name,
            "label_mode": self.wheel.label_mode,
            "show_all": self.wheel.show_all,
            "appearance": self.appearance_settings(),
            "overlap": self.overlap.value(),
            "browser_visible": self.btn_playlists.isChecked(),
            "table_sizes": self.table_splitter.sizes(),
            "preview_source": self._preview_source,
            "selected_set_row": self._set_row(),
            "hidden_columns": {
                name: [c for c in range(table.columnCount()) if table.isColumnHidden(c)]
                for name, table in (("library", self.lib_table), ("set", self.set_table))
            },
            "table_columns": {
                name: bytes(table.horizontalHeader().saveState().toBase64()).decode("ascii")
                for name, table in (("library", self.lib_table), ("set", self.set_table))
                if table.property("custom_columns")
            },
        }
        try:
            self.store.save_session(state)
            self._save_error_shown = False
            return True
        except (OSError, sqlite3.Error) as exc:
            if not self._save_error_shown:
                self._save_error_shown = True
                QMessageBox.warning(self, "Could not save session", str(exc))
            return False

    def _restore_session(self):
        state = self.store.load_session()
        camelot.set_active_chart(state.get("chart", camelot.active_chart_name))
        self.wheel.set_label_mode(state.get("label_mode", "camelot"))
        self.wheel.set_show_all(bool(state.get("show_all", False)))
        self.apply_appearance(state.get("appearance", {}), persist=False)
        self.overlap.setValue(state.get("overlap", 15))
        for name, table in (("library", self.lib_table), ("set", self.set_table)):
            saved = state.get("table_columns", {}).get(name)
            if saved and table.horizontalHeader().restoreState(QByteArray.fromBase64(saved.encode("ascii"))):
                table.setProperty("custom_columns", True)
            for column in state.get("hidden_columns", {}).get(name, []):
                if 0 <= column < table.columnCount():
                    table.setColumnHidden(column, True)
            if all(table.isColumnHidden(c) for c in range(table.columnCount())):
                table.setColumnHidden(1 if name == "set" else 0, False)
        sizes = state.get("table_sizes")
        if sizes:
            self.table_splitter.setSizes(sizes)
        self.active_set = state.get("active_set", [])
        entries = self.store.list_playlists()
        playlist_id = state.get("active_playlist_id")
        if playlist_id and self.store.get_playlist(playlist_id):
            self._activate_playlist(playlist_id)
        elif entries:
            self._activate_playlist(entries[0]["id"])
        else:
            self._refresh_playlist_browser()
        self._fill_set()
        selected_path = state.get("selected_path")
        for row in range(self.lib_table.rowCount()):
            item = self.lib_table.item(row, 0)
            if item.data(Qt.ItemDataRole.UserRole)["path"] == selected_path:
                self.lib_table.selectRow(row)
                break
        self.btn_playlists.setChecked(bool(state.get("browser_visible", False)))
        row = state.get("selected_set_row", -1)
        if state.get("preview_source") == "set" and 0 <= row < self.set_table.rowCount():
            self.set_table.selectRow(row)
            self._on_set_selected()

    def _refresh_playlist_browser(self):
        self.playlist_browser.set_playlists(self.store.list_playlists(), self.active_playlist_id)
        self.playlist_browser.set_linked_folder(self.linked_folder)
        self.btn_relink.setToolTip(f"Music folder: {self.linked_folder}\nClick to change it."
                                  if self.linked_folder else "Choose this playlist's music folder")
        self.btn_relink.setEnabled(bool(self.library))
        self.btn_relink.setChecked(bool(self.linked_folder))

    def _toggle_playlist_browser(self, visible):
        self.playlist_browser.setVisible(visible)
        QTimer.singleShot(0, self._size_wheel_column)
        self._queue_save_session()

    def _activate_playlist(self, playlist_id):
        entry = self.store.get_playlist(playlist_id)
        if entry is None:
            return
        self._stop()
        self.player.setSource(QUrl())
        self.active_playlist_id = playlist_id
        self.active_playlist_name = entry["name"]
        self.linked_folder = entry["linked_folder"]
        self.library = entry["tracks"]
        self._preview_source = "library"
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self._fill_library(self.library)
        if not self.library:
            self._on_library_selected()
            self.waveform.set_track("", [])
        self._refresh_playlist_browser()
        self._queue_save_session()

    def _rename_playlist(self, playlist_id):
        entry = self.store.get_playlist(playlist_id)
        if entry is None:
            return
        name, accepted = QInputDialog.getText(self, "Rename playlist", "Playlist name", text=entry["name"])
        if accepted and name.strip():
            try:
                self.store.rename(playlist_id, name)
            except (OSError, sqlite3.Error, ValueError) as exc:
                QMessageBox.warning(self, "Rename failed", str(exc))
                return
            self._refresh_playlist_browser()
            if playlist_id == self.active_playlist_id:
                self.active_playlist_name = name.strip()
            self._refresh_status()

    def _remove_playlist(self, playlist_id):
        try:
            self.store.remove(playlist_id)
        except (OSError, sqlite3.Error) as exc:
            QMessageBox.warning(self, "Remove failed", str(exc))
            return
        if playlist_id == self.active_playlist_id:
            self.active_playlist_id = None
            self.active_playlist_name = None
            self.linked_folder = None
            entries = self.store.list_playlists()
            if entries:
                self._activate_playlist(entries[0]["id"])
            else:
                self._stop()
                self.player.setSource(QUrl())
                self.library = []
                self.search.clear()
                self._fill_library([])
                self._on_library_selected()
                self.waveform.set_track("", [])
        self._refresh_playlist_browser()
        self._queue_save_session()

    def _colour_row(self, table, row, colour, ncols):
        if current_theme()=='light':
            colour=QColor(*[int(channel*.24+255*.76) for channel in (colour.red(),colour.green(),colour.blue())])
        for c in range(ncols):
            item = table.item(row, c)
            if item:
                item.setBackground(colour)

    @staticmethod
    def _track_seconds(track):
        """Track length in seconds, from the stored mm:ss string."""
        return playlist.time_seconds(track.get("time"))

    def _update_set_time(self, *_):
        overlap = self.overlap.value()
        total = 0
        missing = sum(self._track_seconds(track) is None for track in self.active_set)
        if missing:
            self.lbl_set_time.setText("Set length: Unknown")
            self.lbl_set_time.setToolTip(f"{missing} track(s) have no verified duration. No length was guessed.")
            self._queue_save_session()
            return
        for i, t in enumerate(self.active_set):
            total += self._track_seconds(t)
            if i > 0:
                total -= overlap
        total = max(0, total)
        h, rem = divmod(total, 3600)
        m, s = divmod(rem, 60)
        self.lbl_set_time.setText(f"Set length: {h:02d}:{m:02d}:{s:02d}")
        self.lbl_set_time.setToolTip(f"Includes {overlap}s of overlap per transition.")
        self._queue_save_session()

    # ---------- selection and highlighting ----------
    def _selected_library_track(self):
        rows = self.lib_table.selectionModel().selectedRows()
        if not rows:
            return None
        item = self.lib_table.item(rows[0].row(), 0)
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def _selected_set_track(self):
        row = self._set_row()
        item = self.set_table.item(row, 1) if row >= 0 else None
        token = item.data(Qt.ItemDataRole.UserRole + 2) if item else None
        return next((track for track in self.active_set if id(track) == token), None)

    def _current_preview_track(self):
        return self._selected_set_track() if self._preview_source == "set" else self._selected_library_track()

    def _colour_library_for_selection(self):
        """Colour every library row against the selected track (or leave plain if none)."""
        track = self._current_preview_track()
        if not track:
            return
        key = normalize_key(track["key"])
        rows = self.lib_table.selectionModel().selectedRows()
        selected_row = rows[0].row() if rows and self._preview_source == "library" else -1
        ncols = self.lib_table.columnCount()
        for r in range(self.lib_table.rowCount()):
            if r == selected_row:
                colour = ROW_COLOURS["selected"]
            else:
                other = self.lib_table.item(r, 0).data(Qt.ItemDataRole.UserRole)
                status, label = get_compatibility(key, other["key"])
                colour = relation_tint(label, status, self.wheel.show_all)
            self._colour_row(self.lib_table, r, colour, ncols)

    def _on_library_selected(self):
        track = self._selected_library_track()
        self._preview_source = "library"
        self._preview_selected(track)

    def _on_set_selected(self):
        track = self._selected_set_track()
        if track is not None:
            self._preview_source = "set"
            self._preview_selected(track)

    def _preview_selected(self, track):
        if not track:
            self.wheel.set_active_key(None)
            self._show_details(None)
            self._preview_track = None
            return
        changed = self._preview_track is None or self._preview_track["path"] != track["path"]
        self._preview_track = track
        if changed:
            self.player.stop()
            self.btn_play.setText("Play")
        key = normalize_key(track["key"])
        self.wheel.set_active_key(key)
        self._colour_library_for_selection()
        self._show_details(track)
        if changed:
            self._load_waveform(track)
        self._queue_save_session()

    def _load_waveform(self, track):
        path = track["path"]
        if self.worker and self.worker.isRunning():
            self.worker.requestInterruption()
        # Invalidate pending decodes when browsing quickly, including cached tracks.
        token=object()
        self._pending_waveform=token
        if not os.path.exists(path):
            self.player.setSource(QUrl())
            self.waveform.set_track(track["title"], [])
            return
        self.player.setSource(QUrl.fromLocalFile(path))
        bars = track.get("waveform") or self.cache.get(path)
        if bars:
            track["waveform"] = bars
            self.waveform.set_track(track["title"], bars)
            return
        self.waveform.set_loading()
        def start_analysis():
            if self._closed or self._pending_waveform is not token:return
            worker=WaveformWorker(path, self)
            self.worker=worker
            self._wave_workers.add(worker)
            worker.finished.connect(lambda: self._wave_worker_finished(worker))
            worker.finished.connect(worker.deleteLater)
            worker.computed.connect(self._on_waveform_ready)
            worker.start()
        QTimer.singleShot(140,start_analysis)

    def _wave_worker_finished(self, worker):
        self._wave_workers.discard(worker)
        if self.worker is worker:
            self.worker = None

    def _on_waveform_ready(self, path, bars):
        self.cache.put(path, bars)
        for t in self.library + self.active_set:
            if t["path"] == path:
                t["waveform"] = bars
        current = self._current_preview_track()
        if current and current["path"] == path:
            self.waveform.set_track(current["title"], bars)

    def _toggle_play(self):
        if self.player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self.player.pause()
            self.btn_play.setText("Play")
        else:
            self.player.play()
            self.btn_play.setText("Pause")

    def _stop(self):
        self.player.stop()
        self.btn_play.setText("Play")
        self.waveform.set_progress(0.0)

    def _on_position(self, position):
        duration = self.player.duration()
        if duration > 0:
            self.waveform.set_progress(position / duration)

    def _scrub(self, fraction):
        duration = self.player.duration()
        if duration > 0:
            self.player.setPosition(int(duration * fraction))
            self.waveform.set_progress(fraction)

    # ---------- import / relink / export ----------
    def import_playlist(self):
        m3u8, _ = QFileDialog.getOpenFileName(self, "Select M3U8 playlist", "", "M3U8 playlists (*.m3u8)")
        if not m3u8:
            return
        try:
            own_export = playlist.is_mixlogic_playlist(m3u8)
            txt = None
            if not own_export:
                txt, _ = QFileDialog.getOpenFileName(self, "Select Rekordbox TXT export", "", "Text files (*.txt)")
                if not txt:
                    return
            elif self.active_set:
                answer = QMessageBox.question(
                    self, "Reopen exported set", "Replace the current set with the order saved in this playlist?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No)
                if answer != QMessageBox.StandardButton.Yes:
                    return
            tracks = playlist.build_library(m3u8, txt)
            previous = self.store.find_import(m3u8, txt)
            if previous and previous["linked_folder"]:
                playlist.relink_tracks(tracks, previous["linked_folder"])
            playlist_id = self.store.add_playlist(m3u8, txt, tracks)
        except Exception as exc:
            QMessageBox.critical(self, "Import failed", str(exc))
            return
        self.playlist_browser.search.clear()
        self._activate_playlist(playlist_id)
        if own_export:
            self.active_set = [dict(track) for track in tracks]
            self._fill_set()
        self.btn_playlists.setChecked(True)

    def relink_folder(self):
        self.btn_relink.setChecked(bool(self.linked_folder))
        if not self.library:
            QMessageBox.information(self, "Relink", "Import a playlist first.")
            return
        folder = QFileDialog.getExistingDirectory(self, "Select music folder", self.linked_folder or "")
        if not folder:
            return
        folder = os.path.abspath(folder)
        old_paths = [track["path"] for track in self.library]
        matched = playlist.relink_tracks(self.library, folder)
        if self.active_playlist_id:
            try:
                self.store.update_tracks(self.active_playlist_id, self.library, folder)
            except (OSError, sqlite3.Error) as exc:
                QMessageBox.warning(self, "Could not save relinked paths", str(exc))
        self.linked_folder = folder
        changed_paths = {old: track["path"] for old, track in zip(old_paths, self.library)
                         if old != track["path"]}
        for track in self.active_set:
            if track["path"] in changed_paths:
                track["path"] = changed_paths[track["path"]]
        self._fill_library(self.library)
        self._fill_set()
        self._refresh_playlist_browser()
        QMessageBox.information(self, "Relink", f"Matched {matched} of {len(self.library)} tracks.")

    def export_set(self):
        if not self.active_set:
            QMessageBox.information(self, "Export", "The set is empty.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Export Rekordbox playlist", "MixLogic Set.m3u8", "Rekordbox playlist (*.m3u8)")
        if path:
            if not path.lower().endswith(".m3u8"):
                path += ".m3u8"
            try:
                playlist.export_m3u8(path, self.active_set)
            except (OSError, ValueError) as exc:
                QMessageBox.warning(self, "Export failed", str(exc))

    # ---------- table filling ----------
    def _metadata_marker(self, table, row, track):
        issues = playlist.metadata_issues(track)
        marker = QTableWidgetItem("!" if issues else "")
        marker.setToolTip("Missing metadata: " + "; ".join(issues) if issues else "Metadata available")
        marker.setForeground(QColor(palette_for()['orange']))
        table.setVerticalHeaderItem(row, marker)

    def _sync_metadata_markers(self, table):
        for row in range(table.rowCount()):
            item = table.item(row, 0 if table is self.lib_table else 1)
            track = item.data(Qt.ItemDataRole.UserRole) if item else None
            if isinstance(track, dict):
                self._metadata_marker(table, row, track)

    def _fill_library(self, tracks):
        preview_set = self._preview_source == "set" and self._selected_set_track() is not None
        # Populate completely before selection callbacks inspect the new playlist.
        with QSignalBlocker(self.lib_table):
            self.lib_table.setSortingEnabled(False)
            self.lib_table.setRowCount(len(tracks))
            for r, t in enumerate(tracks):
                key = normalize_key(t["key"])
                texts = playlist.display_metadata(t)
                first = QTableWidgetItem(texts[0])
                first.setData(Qt.ItemDataRole.UserRole, t)
                camelot = QTableWidgetItem(key or playlist.UNKNOWN)
                camelot.setData(Qt.ItemDataRole.UserRole + 1, camelot_sort_key(key))
                values = [first, QTableWidgetItem(texts[1]), QTableWidgetItem(texts[2]),
                          camelot, QTableWidgetItem(texts[4]), QTableWidgetItem(texts[5])]
                self._metadata_marker(self.lib_table, r, t)
                for c, item in enumerate(values):
                    item.setToolTip("; ".join(playlist.metadata_issues(t)) or "Metadata matched to the imported source")
                    if item.text() == playlist.UNKNOWN or item.text() == "Unknown Artist":
                        item.setForeground(QColor(palette_for()['orange']))
                    self.lib_table.setItem(r, c, item)
            self.lib_table.setSortingEnabled(True)
            if tracks:
                self.lib_table.selectRow(0)
        if preview_set:
            self._on_set_selected()
        else:
            self._on_library_selected()
        self._refresh_status()

    def _fill_set(self):
        selected = self._selected_set_track()
        old_row = self._set_row()
        with QSignalBlocker(self.set_table):
            self.set_table.setRowCount(len(self.active_set))
            selected_row = -1
            for r, t in enumerate(self.active_set):
                key = normalize_key(t["key"])
                values = [str(r + 1)] + playlist.display_metadata(t)
                self._metadata_marker(self.set_table, r, t)
                for c, text in enumerate(values):
                    item = QTableWidgetItem(text)
                    item.setToolTip("; ".join(playlist.metadata_issues(t)) or "Metadata matched to the imported source")
                    if text == playlist.UNKNOWN or text == "Unknown Artist":
                        item.setForeground(QColor(palette_for()['orange']))
                    if c == 1:
                        item.setData(Qt.ItemDataRole.UserRole, t)
                        item.setData(Qt.ItemDataRole.UserRole + 2, id(t))
                    self.set_table.setItem(r, c, item)
                if t is selected:
                    selected_row = r
                colour = QColor(COLORS["panel_alt"])
                if r > 0:
                    prev = normalize_key(self.active_set[r - 1]["key"])
                    status, label = get_compatibility(prev, key)
                    colour = relation_tint(label, status, self.wheel.show_all)
                self._colour_row(self.set_table, r, colour, self.set_table.columnCount())
            if selected_row < 0 and old_row >= 0 and self.active_set:
                selected_row = min(old_row, len(self.active_set) - 1)
            if selected_row >= 0:
                self.set_table.selectRow(selected_row)
        if self._preview_source == "set":
            if self._selected_set_track():
                self._on_set_selected()
            else:
                self._on_library_selected()
        else:
            self._show_details(self._current_preview_track())
        self._refresh_status()

    def _apply_filter(self, text):
        query = text.strip().lower()
        if not query:
            self._fill_library(self.library)
            return
        matches = [t for t in self.library
                   if query in t["title"].lower() or query in t["artist"].lower()
                   or query in t["bpm"].lower() or query in (normalize_key(t["key"]) or "").lower()]
        self._fill_library(matches)

    # ---------- set builder ----------
    def add_selected_to_set(self):
        track = self._selected_library_track()
        if not track:
            return
        if any(t["path"] == track["path"] for t in self.active_set):
            answer = QMessageBox.question(
                self, "Already in set",
                f"\"{track['title']}\" is already in the set.\n\nAdd it again?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self.active_set.append(dict(track))
        self._fill_set()

    def refresh_relations(self):
        # Recompute in place so chart/colour changes preserve selection and playback.
        self._update_wheel_legend()
        current = self._current_preview_track()
        self.wheel.set_active_key(current["key"] if current else None)
        self._colour_library_for_selection()
        self._fill_set()

    def _on_show_all_changed(self, _enabled):
        self.refresh_relations()

    def library_view_tracks(self):
        query = self.search.text().strip().lower()
        if not query:
            return self.library
        return [t for t in self.library
                if query in t["title"].lower() or query in t["artist"].lower()
                or query in t["bpm"].lower() or query in (normalize_key(t["key"]) or "").lower()]

    def show_options(self):
        OptionsDialog(self.wheel, self._icon_path, self).exec()
        self._queue_save_session()

    def show_metadata_details(self):
        MetadataReviewDialog(self).exec()

    def appearance_settings(self):
        return dict(wheel_style=self.wheel.visual_style, wave_style=self.waveform.visual_style,
                    wave_mode=self.waveform.colour_mode,theme=current_theme())

    def apply_appearance(self, values, persist=True):
        values = clean_appearance(values)
        theme_changed=values['theme']!=current_theme()
        apply_theme(values['theme'])
        self.wheel.set_visual_style(values['wheel_style'])
        self.waveform.set_appearance(values['wave_style'], values['wave_mode'])
        self.waveform.setFixedHeight(48)
        self._update_wheel_legend()
        if theme_changed and not self._restoring:
            # Recolour in place: a theme change must not select another track,
            # restart playback, or change set order.
            for table in (self.lib_table,self.set_table):
                for row in range(table.rowCount()):
                    for col in range(table.columnCount()):
                        item=table.item(row,col)
                        if item:item.setForeground(QColor(palette_for()['orange' if item.text()==playlist.UNKNOWN else 'text']))
            self.refresh_relations()
        if persist:
            self._save_session()

    def _update_wheel_legend(self):
        self.wheel_legend.setVisible(True)
        self.wheel_legend.setText(wheel_legend_html(camelot.active_chart_name,self.wheel.show_all,self.wheel.visual_style=='accessible'))

    def show_about(self):
        AboutDialog(QIcon(self._icon_path), self._icon_path, self).exec()

    def _set_row(self):
        rows = self.set_table.selectionModel().selectedRows()
        return rows[0].row() if rows else -1

    def move_up(self):
        r = self._set_row()
        if r > 0:
            self.active_set[r - 1], self.active_set[r] = self.active_set[r], self.active_set[r - 1]
            self._fill_set()
            self.set_table.selectRow(r - 1)

    def move_down(self):
        r = self._set_row()
        if 0 <= r < len(self.active_set) - 1:
            self.active_set[r + 1], self.active_set[r] = self.active_set[r], self.active_set[r + 1]
            self._fill_set()
            self.set_table.selectRow(r + 1)

    def remove_selected(self):
        r = self._set_row()
        if 0 <= r < len(self.active_set):
            del self.active_set[r]
            self._fill_set()

    def clear_set(self):
        self.active_set = []
        self._fill_set()

    def closeEvent(self, event):
        if self._closed:
            super().closeEvent(event);return
        if not self._save_session():
            event.ignore()
            return
        for worker in list(self._wave_workers):
            worker.requestInterruption()
            worker.wait()
        self._closed=True
        self.setProperty('_mixlogic_closed',True)
        self.store.close()
        self.cache.close()
        super().closeEvent(event)

    def _show_details(self, track):
        if track is None:
            self.track_details.set_text("Select a track to see its details")
            self.lbl_relation.setText("Relation: select a track")
            self.lbl_relation.setToolTip("Select a library track to compare it with the last track in your set.")
            style_widget(self.lbl_relation,f"font-size: 9pt; color: {COLORS['muted']};")
            return
        key = normalize_key(track["key"])
        relation = "set is empty" if key else "Unknown — key metadata unavailable"
        colour = COLORS["muted"]
        tooltip = "Add a track to your set to compare its key with the selected library track."
        if self.active_set:
            last = normalize_key(self.active_set[-1]["key"])
            status, relation = get_compatibility(last, key)
            colour = {"green": COLORS["green"], "orange": COLORS["orange"], "red": COLORS["red"], "unknown": COLORS["muted"]}[status]
            tooltip = (f"{camelot.active_chart_name}\n"
                       f"Last set track: {self.active_set[-1]['title']} ({last})\n"
                       f"Selected track: {track['title']} ({key})\n"
                       f"{last} → {key}: {relation}")
        self.lbl_relation.setText(f"Relation to last: {relation}")
        self.lbl_relation.setToolTip(tooltip)
        style_widget(self.lbl_relation,f"font-size: 9pt; font-weight: bold; color: {colour};")
        self.track_details.set_text(
            f"Title: {track['title']}   |   Artist: {track['artist']}   |   BPM: {track['bpm']}   |   "
            f"Key: {key or playlist.UNKNOWN} / {REAL_KEYS.get(key, playlist.UNKNOWN)}   |   Duration: {track['time']}"
        )
