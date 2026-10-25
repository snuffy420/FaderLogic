"""Options and About dialogs for MixLogic."""
import io

import qrcode
from PyQt6.QtCore import QSignalBlocker, QTimer, Qt
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtWidgets import (
    QButtonGroup, QCheckBox, QDialog, QHBoxLayout, QLabel, QPushButton,
    QApplication, QDialogButtonBox, QGridLayout, QLineEdit,
    QMessageBox as NativeMessageBox, QRadioButton, QTabWidget, QTextBrowser,
    QVBoxLayout, QGroupBox, QSizePolicy, QWidget,
)

from . import __version__
from . import camelot as _camelot
from .camelot import CHART_CHOICES, set_active_chart
from .camelot import VARIATIONS
from .theme import COLORS
from .titlebar import TitleBar

# Replace with your real bitcoin address when you are ready.
BTC_ADDRESS = "bc1qz8877p6vusc22qrctdj4h7w0uk2l9l9h8lwphy"


class MessageDialog(QDialog):
    """App-styled messages using the same title bar and icon as Options/About."""

    def __init__(self, parent, title, text, buttons, default_button=None):
        super().__init__(parent)
        self.choice = NativeMessageBox.StandardButton.No
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setStyleSheet(DIALOG_STYLE)
        icon_path = getattr(parent, "_icon_path", "")
        self.setWindowIcon(QIcon(icon_path))
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(TitleBar(self, icon_path, title, ""))
        body = QHBoxLayout()
        body.setContentsMargins(18, 14, 18, 8)
        icon = QLabel()
        icon.setPixmap(QIcon(icon_path).pixmap(40, 40))
        body.addWidget(icon, 0, Qt.AlignmentFlag.AlignTop)
        label = QLabel(text)
        label.setTextFormat(Qt.TextFormat.PlainText)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        label.setMinimumWidth(220)
        label.setMaximumWidth(520)
        body.addWidget(label)
        outer.addLayout(body)
        actions = QHBoxLayout()
        actions.setContentsMargins(18, 0, 18, 14)
        actions.addStretch()
        for flag, caption in ((NativeMessageBox.StandardButton.Yes, "Yes"),
                              (NativeMessageBox.StandardButton.No, "No"),
                              (NativeMessageBox.StandardButton.Ok, "OK"),
                              (NativeMessageBox.StandardButton.Cancel, "Cancel")):
            if buttons & flag:
                button = QPushButton(caption)
                button.setDefault(flag == default_button)
                button.clicked.connect(lambda _checked=False, value=flag: self._choose(value))
                actions.addWidget(button)
        outer.addLayout(actions)

    def _choose(self, choice):
        self.choice = choice
        self.accept()


class StyledMessageBox:
    StandardButton = NativeMessageBox.StandardButton

    @staticmethod
    def information(parent, title, text):
        dialog = MessageDialog(parent, title, text, StyledMessageBox.StandardButton.Ok,
                               StyledMessageBox.StandardButton.Ok)
        dialog.exec()
        return dialog.choice

    warning = information
    critical = information

    @staticmethod
    def question(parent, title, text, buttons=None, default_button=None):
        buttons = buttons or (StyledMessageBox.StandardButton.Yes | StyledMessageBox.StandardButton.No)
        dialog = MessageDialog(parent, title, text, buttons, default_button)
        dialog.exec()
        return dialog.choice


class RenameDialog(QDialog):
    def __init__(self, parent, title, label, text):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setStyleSheet(DIALOG_STYLE)
        icon_path = getattr(parent, "_icon_path", "")
        self.setWindowIcon(QIcon(icon_path))
        self.setMinimumWidth(360)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(TitleBar(self, icon_path, title, ""))
        body = QWidget()
        layout = QVBoxLayout(body)
        layout.setContentsMargins(16, 10, 16, 16)
        layout.addWidget(QLabel(label))
        self.edit = QLineEdit(text)
        self.edit.selectAll()
        layout.addWidget(self.edit)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        outer.addWidget(body)
        self.edit.setFocus()


class StyledInputDialog:
    @staticmethod
    def getText(parent, title, label, text=""):
        dialog = RenameDialog(parent, title, label, text)
        accepted = dialog.exec() == QDialog.DialogCode.Accepted
        return dialog.edit.text(), accepted

HELP_HTML = f"""
<h3 style="color:{COLORS['cyan']}">Getting started</h3>
<ol>
<li><b>Import Playlist</b> &mdash; choose a Rekordbox <code>.m3u8</code> export and its matching
TXT export. A set exported by MixLogic can reopen directly from its M3U8, with no TXT file needed.</li>
<li><b>Saved playlists</b> &mdash; click <b>Playlists</b> in the top toolbar to show or hide
your playlist browser. Import each Rekordbox TXT/M3U8 pair once, then choose it from the browser
whenever you need it. Each playlist remembers its music folder and linked tracks. Switching
playlists keeps your current set; reopening MixLogic restores the last playlist, your set,
and your preferences automatically. Use the browser to search, rename or remove saved entries.</li>
<li><b>Relink Folder</b> &mdash; if the audio is not where Rekordbox expects, point MixLogic at your music folder.
Each saved playlist remembers its own folder and linked paths, including when you reimport an updated export.</li>
<li><b>Click a track</b> in either table to update the wheel, track details and playback preview.
Selecting a set track also lets you move or remove it.</li>
<li><b>Add Selected Track to Set</b> to build your set. Adding a track that is already in the set asks first.</li>
<li><b>Transition Time</b> sets the overlap per transition. The set length is reduced by that amount for each join.</li>
<li><b>Export Set (.m3u8)</b> saves the set in playlist order. In Rekordbox, use
<b>File &rarr; Import &rarr; Import Playlist</b>, then export to your CDJ/USB from Rekordbox.
Keep the audio files at their saved paths, or use <b>Relink Folder</b> before exporting.</li>
</ol>
<h3 style="color:{COLORS['cyan']}">Table row colours (default)</h3>
<ul>
<li><span style="color:{COLORS['green']}">Green</span> &mdash; perfect match or energy boost (+).</li>
<li><span style="color:{COLORS['orange']}">Orange</span> &mdash; boost (++/+++), energy drop, or mood change.</li>
<li><span style="color:{COLORS['red']}">Red</span> &mdash; not harmonically compatible.</li>
</ul>
<p>These are the default table row colours. With <i>Show all variations</i> enabled,
use the colour key below for each chart's individual relation colours.</p>
<h3 style="color:{COLORS['cyan']}">Camelot wheel</h3>
<p>Labels can show the Camelot code (8A), the key (Am), or both. Turn on
<i>Show all variations</i> in Options to colour each relation type separately.</p>
<p>The selected key has a cyan outline. Keys outside the selected chart's listed relations
are dimmed. Relation outlines are green or orange by default, or use the individual colours
in the colour key when <i>Show all variations</i> is enabled.</p>
<h3 style="color:{COLORS['cyan']}">Adjust your workspace</h3>
<p>Drag between column headings to resize any track column, including Title and Artist.
Drag the horizontal divider between the library and set to adjust their heights.
Your chosen sizes are remembered for next time.</p>
<p>In Options &rarr; Table columns, choose which columns to show in each table.</p>
<h3 style="color:{COLORS['cyan']}">Playlist encoding and editing</h3>
<p>Rekordbox TXT exports use UTF-16; M3U8 playlists use UTF-8. MixLogic reads both formats
and keeps M3U8 exports in UTF-8. Its exported sets also retain their titles, artists, BPM,
keys and playing order when reopened in MixLogic through Import Playlist.</p>
{{VARIATION_HELP}}
<h3 style="color:{COLORS['cyan']}">Waveforms and playback</h3>
<p>Click a track to load its waveform. Waveforms are analysed once and cached in
<code>waveform_cache.db</code>. Click or drag the waveform to scrub.</p>
"""


def _variation_help_html():
    """Colour key for the Help tab, built from the same palette as the wheel and tables."""
    rows = []
    for name, (hex_, tint, desc) in VARIATIONS.items():
        swatch = (f"<span style='background:{hex_};color:#0B0C0E;font-weight:bold;"
                  f"padding:1px 8px;border-radius:4px'>&nbsp;{name}&nbsp;</span>")
        rows.append(f"<tr><td style='padding:4px 10px 4px 0'>{swatch}</td>"
                    f"<td style='color:{COLORS['muted']}'>{desc}</td></tr>")
    return ("<h3 style='color:" + COLORS['cyan'] + "'>Colour key</h3>"
            "<p>With <i>Show all variations</i> on, each relation has its own colour, shown on the wheel "
            "and in both track tables. With it off, the tables use only green, orange and red.</p>"
            "<table>" + "".join(rows) + "</table>")




def _qr_pixmap(text, size=220):
    qr = qrcode.QRCode(box_size=8, border=2)
    qr.add_data(text)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    pixmap = QPixmap()
    pixmap.loadFromData(buf.getvalue(), "PNG")
    return pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)


class OptionsDialog(QDialog):
    """Controls what the Camelot wheel shows. Changes apply immediately."""

    def __init__(self, wheel, icon_path, parent=None):
        super().__init__(parent)
        self.wheel = wheel
        self.setWindowTitle("Options")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setStyleSheet(DIALOG_STYLE)
        self.setMinimumWidth(360)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(TitleBar(self, icon_path, "Options", ""))
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(14, 12, 14, 14)
        outer.addWidget(body, 1)
        tabs = QTabWidget()
        body_layout.addWidget(tabs)
        wheel_page = QWidget()
        layout = QVBoxLayout(wheel_page)
        tabs.addTab(wheel_page, "Wheel")

        labels = QGroupBox("Camelot wheel labels")
        labels_layout = QVBoxLayout(labels)
        self.group = QButtonGroup(self)
        for text, mode in (("Camelot number (8A)", "camelot"),
                           ("Musical key (Am)", "key"),
                           ("Both (8A / Am)", "both")):
            radio = QRadioButton(text)
            radio.setProperty("mode", mode)
            radio.setChecked(wheel.label_mode == mode)
            radio.toggled.connect(lambda checked, m=mode: checked and wheel.set_label_mode(m))
            self.group.addButton(radio)
            labels_layout.addWidget(radio)
        layout.addWidget(labels)

        variations = QGroupBox("Highlighting")
        var_layout = QVBoxLayout(variations)
        show_all = QCheckBox("Show all variations (colour each relation type)")
        show_all.setChecked(wheel.show_all)
        show_all.toggled.connect(wheel.set_show_all)
        var_layout.addWidget(show_all)
        layout.addWidget(variations)

        charts = QGroupBox("Relation chart")
        charts_layout = QVBoxLayout(charts)
        self.chart_group = QButtonGroup(self)
        for name in CHART_CHOICES:
            radio = QRadioButton(name)
            radio.setChecked(name == _camelot.active_chart_name)
            radio.toggled.connect(lambda checked, n=name: checked and self._pick_chart(n))
            self.chart_group.addButton(radio)
            charts_layout.addWidget(radio)
        layout.addWidget(charts)
        layout.addStretch()

        self.column_checks = {}
        if parent is not None and hasattr(parent, "lib_table"):
            columns_page = QWidget()
            columns_layout = QVBoxLayout(columns_page)
            note = QLabel("Choose the columns shown in each table. At least one column must stay visible.")
            note.setWordWrap(True)
            columns_layout.addWidget(note)
            grid = QGridLayout()
            grid.addWidget(QLabel("Column"), 0, 0)
            grid.addWidget(QLabel("Library"), 0, 1)
            grid.addWidget(QLabel("Set"), 0, 2)
            names = ("#", "Title", "Artist", "BPM", "Camelot", "Key", "Time")
            for row, name in enumerate(names, 1):
                grid.addWidget(QLabel(name), row, 0)
                for offset, table_name, table in ((1, "library", parent.lib_table), (2, "set", parent.set_table)):
                    for column in range(table.columnCount()):
                        if table.horizontalHeaderItem(column).text() != name:
                            continue
                        check = QCheckBox()
                        check.setChecked(not table.isColumnHidden(column))
                        check.setAccessibleName(f"{table_name} {name} column")
                        check.toggled.connect(lambda checked, t=table_name, c=column, box=check:
                                              self._pick_column(t, c, checked, box))
                        self.column_checks[(table_name, name)] = check
                        grid.addWidget(check, row, offset)
            columns_layout.addLayout(grid)
            columns_layout.addStretch()
            tabs.addTab(columns_page, "Table columns")

        close = QPushButton("Close")
        close.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(close)
        body_layout.addLayout(row)


    def _pick_chart(self, name):
        set_active_chart(name)
        self.wheel.update()
        if self.parent() is not None and hasattr(self.parent(), "refresh_relations"):
            self.parent().refresh_relations()

    def _pick_column(self, table_name, column, checked, box):
        if not self.parent().set_column_visible(table_name, column, checked):
            with QSignalBlocker(box):
                box.setChecked(True)


def _btc_icon(size=56):
    """A neon-blue and green Bitcoin coin, drawn to match the app theme."""
    from PyQt6.QtCore import QPointF, QRectF
    from PyQt6.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter, QPen
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    grad = QLinearGradient(QPointF(0, 0), QPointF(size, size))
    grad.setColorAt(0.0, QColor(COLORS["neon_blue"]))
    grad.setColorAt(1.0, QColor(COLORS["neon_green"]))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(grad)
    p.drawEllipse(QRectF(2, 2, size - 4, size - 4))
    p.setBrush(QColor(COLORS["panel"]))
    p.drawEllipse(QRectF(size * 0.12, size * 0.12, size * 0.76, size * 0.76))
    font = QFont("Segoe UI", int(size * 0.34))
    font.setBold(True)
    p.setFont(font)
    p.setPen(QPen(QColor(COLORS["neon_green"])))
    p.drawText(QRectF(0, 0, size, size), Qt.AlignmentFlag.AlignCenter, "\u20bf")
    p.end()
    return QPixmap.fromImage(img)


DIALOG_STYLE = f"""
QDialog {{ background-color: {COLORS['bg']}; }}
QTabWidget::pane {{ border: 1px solid {COLORS['border']}; background: {COLORS['panel']}; border-radius: 6px; }}
QTabBar::tab {{ background: {COLORS['panel_alt']}; color: {COLORS['muted']}; padding: 8px 18px; border: 1px solid {COLORS['border']}; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; }}
QTabBar::tab:selected {{ background: {COLORS['panel']}; color: {COLORS['cyan']}; border-bottom: 2px solid {COLORS['neon_green']}; }}
QTabBar::tab:hover {{ color: {COLORS['text']}; }}
QLabel {{ color: {COLORS['text']}; background: transparent; }}
QTextBrowser {{ background: {COLORS['panel']}; color: {COLORS['text']}; border: none; }}
QWidget#tabPage {{ background: {COLORS['panel']}; }}
"""


class AboutDialog(QDialog):
    """About, Help and Donate tabs."""

    def __init__(self, icon, icon_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About MixLogic")
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)
        self.setMinimumSize(620, 580)
        self.setStyleSheet(DIALOG_STYLE)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(TitleBar(self, icon_path, "About MixLogic", ""))
        body = QWidget()
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(14, 12, 14, 14)
        layout.addWidget(body, 1)
        layout = body_layout
        tabs = QTabWidget()
        tabs.addTab(self._about_tab(icon), "About")
        tabs.addTab(self._help_tab(), "Help")
        tabs.addTab(self._donate_tab(), "Donate")
        layout.addWidget(tabs)

    def _about_tab(self, icon):
        page = QWidget_with_layout(QVBoxLayout)
        layout = page.layout()
        head = QHBoxLayout()
        logo = QLabel()
        logo.setPixmap(icon.pixmap(72, 72))
        head.addWidget(logo)
        name = QLabel(f"<span style='font-size:20pt;font-weight:700'>MixLogic</span>"
                      f"<br><span style='color:{COLORS['muted']}'>Version {__version__}</span>")
        head.addWidget(name)
        head.addStretch()
        layout.addLayout(head)
        text = QTextBrowser()
        text.setOpenExternalLinks(True)
        text.setHtml(f"""
            <p style="font-size:12pt; color:{COLORS['text']}">
            A clearer way to build your next set.</p>
            <p>MixLogic is a harmonic DJ set builder made for Rekordbox.
            Bring in your playlists, preview tracks, explore key relationships,
            and shape a playing order that works for you.</p>
            <h3 style="color:{COLORS['cyan']}">Your library, ready when you are</h3>
            <p>Save your Rekordbox TXT/M3U8 imports with their linked music folders.
            Switch between playlists and pick up your last session with your set
            and preferences intact.</p>
            <h3 style="color:{COLORS['cyan']}">Choose the next track with context</h3>
            <p>A large Camelot wheel, two reference charts, compatibility colours,
            waveform previews and a live relation-to-last-track display help you
            explore your options. Resize the track columns and panels to suit your library.</p>
            <h3 style="color:{COLORS['cyan']}">Back to Rekordbox, in your order</h3>
            <p>Build and reorder your set, estimate its length with transition overlaps,
            and export a UTF-8 M3U8 playlist in the exact order you chose.
            Import it through Rekordbox's File &rarr; Import &rarr; Import Playlist,
            or reopen it directly in MixLogic to edit it again.</p>
            <p>Encoding follows each file type: UTF-16 for Rekordbox TXT imports,
            and UTF-8 for M3U8 playlists.</p>
            <p style="color:{COLORS['muted']}">Built with Python and PyQt6.
            Music stays in your own folders; MixLogic saves its playlist data locally.</p>
        """)
        layout.addWidget(text, 1)
        footer = QLabel(
            f"<span style='font-size:12pt;font-weight:700'>zer\u00d8 software</span><br>"
            f"&copy; 2026 zer\u00d8 software<br>"
            f"Created by <b>snuffy420</b><br>"
            f"<a href='https://github.com/snuffy420' style='color:{COLORS['neon_blue']}'>"
            f"github.com/snuffy420</a>"
        )
        footer.setTextFormat(Qt.TextFormat.RichText)
        footer.setOpenExternalLinks(True)
        footer.setStyleSheet(f"color:{COLORS['text']}; background: transparent;")
        layout.addWidget(footer)
        return page

    def _help_tab(self):
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setHtml(HELP_HTML.replace("{VARIATION_HELP}", _variation_help_html()))
        return browser

    def _donate_tab(self):
        page = QWidget_with_layout(QVBoxLayout)
        layout = page.layout()
        note = QLabel("If MixLogic helps your sets, you can support its development with Bitcoin.")
        note.setWordWrap(True)
        layout.addWidget(note)
        coin = QLabel()
        coin.setPixmap(_btc_icon())
        coin.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(coin)
        qr = QLabel()
        qr.setPixmap(_qr_pixmap(f"bitcoin:{BTC_ADDRESS}"))
        qr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr.setStyleSheet("background: #FFFFFF; border-radius: 8px; padding: 10px;")
        layout.addWidget(qr, 0, Qt.AlignmentFlag.AlignCenter)
        addr = QLabel(BTC_ADDRESS)
        addr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        addr.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        addr.setStyleSheet(f"color:{COLORS['neon_green']}; font-family: Consolas;")
        layout.addWidget(addr)
        self.copy_btc_button = QPushButton("Copy BTC address")
        self.copy_btc_button.setObjectName("primary")
        self.copy_btc_button.clicked.connect(self._copy_btc)
        layout.addWidget(self.copy_btc_button, 0, Qt.AlignmentFlag.AlignHCenter)
        layout.addStretch()
        self.copy_status = QLabel("")
        self.copy_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.copy_status.setFixedHeight(24)
        self.copy_status.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Fixed)
        self.copy_status.setStyleSheet(f"color: {COLORS['neon_green']};")
        layout.addWidget(self.copy_status)
        self.copy_timer = QTimer(self)
        self.copy_timer.setSingleShot(True)
        self.copy_timer.setInterval(2500)
        self.copy_timer.timeout.connect(self.copy_status.clear)
        return page

    def _copy_btc(self):
        QApplication.clipboard().setText(BTC_ADDRESS)
        self.copy_status.setText("Bitcoin address copied.")
        self.copy_timer.start()


def QWidget_with_layout(layout_cls):
    from PyQt6.QtWidgets import QWidget
    widget = QWidget()
    widget.setObjectName("tabPage")
    layout_cls(widget)
    return widget
