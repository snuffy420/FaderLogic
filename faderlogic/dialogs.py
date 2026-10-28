"""Options and About dialogs for FaderLogic."""

import io



import qrcode

from PyQt6.QtCore import QPointF, QSignalBlocker, QTimer, Qt

from PyQt6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap

from PyQt6.QtWidgets import (

    QButtonGroup, QCheckBox, QDialog, QHBoxLayout, QLabel, QPushButton,

    QApplication, QDialogButtonBox, QGridLayout, QLineEdit,

    QMessageBox as NativeMessageBox, QRadioButton, QTabWidget, QTextBrowser,

    QVBoxLayout, QGroupBox, QSizePolicy, QWidget, QComboBox, QFrame,

    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,

)



from . import __version__

from . import camelot as _camelot

from .camelot import CHART_CHOICES, set_active_chart

from .camelot import VARIATIONS

from .theme import COLORS, style_widget, UI_THEMES, current_theme, palette_for, ui_html, stylesheet

from .titlebar import TitleBar

from .appearance import WHEEL_STYLES, WAVE_STYLES, WAVE_MODES, RELATION_CODES, accessible_legend, standard_legend, wheel_legend_html

from .widgets import CamelotWheelWidget, WaveformWidget

from . import playlist



# Replace with your real bitcoin address when you are ready.

BTC_ADDRESS = "bc1qz8877p6vusc22qrctdj4h7w0uk2l9l9h8lwphy"





class MessageDialog(QDialog):

    """App-styled messages using the same title bar and icon as Options/About."""



    def __init__(self, parent, title, text, buttons, default_button=None):

        super().__init__(parent)

        self.choice = NativeMessageBox.StandardButton.No

        self.setWindowTitle(title)

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

        style_widget(self,DIALOG_STYLE)

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

        style_widget(self,DIALOG_STYLE)

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





class MetadataReviewDialog(QDialog):

    """Optional, bounded review table; missing values are primarily shown inline."""

    def __init__(self, parent):

        super().__init__(parent)

        self.setWindowTitle("Metadata details")

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

        style_widget(self,DIALOG_STYLE)

        screen = self.screen().availableGeometry()

        self.resize(min(820, screen.width()-40), min(480, screen.height()-40))

        outer = QVBoxLayout(self); outer.setContentsMargins(0, 0, 0, 0)

        outer.addWidget(TitleBar(self, parent._icon_path, "Metadata details", ""))

        body = QVBoxLayout(); body.setContentsMargins(16, 10, 16, 14)

        rows = [(name, track) for name, tracks in (("Library", parent.library), ("Set", parent.active_set))

                for track in tracks if playlist.metadata_issues(track)]

        required = sum(not _camelot.normalize_key(t.get('key')) or playlist.valid_bpm(t.get('bpm')) is None for _, t in rows)

        summary = QLabel(f"{len(rows)} rows with missing fields · {required} missing key or BPM")

        body.addWidget(summary)

        note = QLabel("Unknown marks unavailable fields. An absent artist does not affect key compatibility.")

        note.setWordWrap(True); body.addWidget(note)

        self.table = QTableWidget(len(rows), 3)

        self.table.setHorizontalHeaderLabels(["Table", "Track", "Unavailable / review"])

        self.table.verticalHeader().hide()

        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        self.table.setWordWrap(False)

        self.table.setTextElideMode(Qt.TextElideMode.ElideRight)

        self.table.setColumnWidth(0, 70); self.table.setColumnWidth(1, 300)

        self.table.horizontalHeader().setStretchLastSection(True)

        for row, (name, track) in enumerate(rows):

            for col, text in enumerate((name, playlist.display_metadata(track)[0], "; ".join(playlist.metadata_issues(track)))):

                item = QTableWidgetItem(text); item.setToolTip(text); self.table.setItem(row, col, item)

        body.addWidget(self.table, 1)

        close = QPushButton("Close"); close.clicked.connect(self.accept)

        actions = QHBoxLayout(); actions.addStretch(); actions.addWidget(close); body.addLayout(actions)

        outer.addLayout(body, 1)





class AppearanceChoice(QComboBox):

    """A standard accessible combo with a consistently visible dark-theme arrow."""

    def paintEvent(self, event):

        super().paintEvent(event)

        p = QPainter(self)

        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        p.setPen(QPen(QColor(palette_for()['muted']), 1.5))

        x, y = self.width()-13, self.height()/2

        p.drawLine(QPointF(x-3,y-2),QPointF(x,y+1))

        p.drawLine(QPointF(x,y+1),QPointF(x+3,y-2))

        p.end()





class SingleLineHint(QLabel):

    """A fixed-height hint; full wording is available on hover."""

    def __init__(self,text,parent=None):

        super().__init__(text,parent)

        self.setWordWrap(False)

        self.setFixedHeight(24)

        self.setMinimumWidth(0)

        self.setSizePolicy(QSizePolicy.Policy.Ignored,QSizePolicy.Policy.Fixed)

        self.setToolTip(text)

    def setText(self,text):

        super().setText(text)

        self.setToolTip(text)

    def paintEvent(self,event):

        p=QPainter(self);p.setFont(self.font());p.setPen(self.palette().windowText().color())

        text=self.fontMetrics().elidedText(self.text(),Qt.TextElideMode.ElideRight,max(0,self.width()-2))

        p.drawText(self.rect(),Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,text)

        p.end()





class AppearancePanel(QWidget):

    """A working miniature workspace rendered by the actual app widgets."""

    def __init__(self, wheel, waveform, parent=None):

        super().__init__(parent)

        layout = QVBoxLayout(self)

        choices = QGridLayout()

        self.wheel_choice, self.wave_choice, self.mode_choice = AppearanceChoice(), AppearanceChoice(), AppearanceChoice()

        self.theme_choice=AppearanceChoice()

        theme_row=QHBoxLayout();theme_row.addWidget(QLabel('Interface theme'))

        for key,title in UI_THEMES.items():self.theme_choice.addItem(title,key)

        self.theme_choice.setCurrentIndex(self.theme_choice.findData(current_theme()))

        self.theme_choice.setAccessibleName('Interface theme');self.theme_choice.setMaximumWidth(160)

        theme_row.addWidget(self.theme_choice);theme_row.addStretch();layout.addLayout(theme_row)

        for col, (label, combo, options, value) in enumerate((

            ("Camelot wheel", self.wheel_choice, WHEEL_STYLES, wheel.visual_style),

            ("Waveform design", self.wave_choice, WAVE_STYLES, waveform.visual_style if waveform else 'classic'),

            ("Waveform mode", self.mode_choice, WAVE_MODES, waveform.colour_mode if waveform else 'bands'),

        )):

            choices.addWidget(QLabel(label), 0, col)

            for key, title in options.items(): combo.addItem(title, key)

            combo.setCurrentIndex(combo.findData(value))

            combo.setAccessibleName(label)

            choices.addWidget(combo, 1, col)

        layout.addLayout(choices)

        self.note = SingleLineHint("Designs keep the original key colours, relation colours and chart behaviour.")

        layout.addWidget(self.note)

        preview = QFrame(); preview.setObjectName('card')

        preview.setProperty('_appearance_preview',True)

        self.preview = preview

        gui = QVBoxLayout(preview); gui.setContentsMargins(12, 8, 12, 8)

        bars=list(waveform.bars) if waveform is not None and waveform.bars else None
        self.preview_uses_current_track=bool(bars)
        if bars:
            title="Current track · same waveform data as the main display"
        else:
            from .dance_preview import DANCE_PREVIEW
            bars=list(DANCE_PREVIEW)
            title="128 BPM example · analyzed with FaderLogic's track overview"
        label=SingleLineHint(title)
        label.setToolTip(waveform.title if self.preview_uses_current_track else title)
        style_widget(label,f"color:{COLORS['muted']};font-size:8pt;");gui.addWidget(label)
        self.wave_preview=WaveformWidget();self.wave_preview.setFixedHeight(48)
        self.wave_preview.set_track(title,bars)
        self.wave_preview.set_progress(waveform.progress if self.preview_uses_current_track else .64)
        gui.addWidget(self.wave_preview)

        row = QHBoxLayout()

        self.wheel_preview = CamelotWheelWidget()

        self.wheel_preview.set_label_mode(wheel.label_mode)

        self.wheel_preview.set_show_all(wheel.show_all)

        self.wheel_preview.set_active_key('8A')

        self.wheel_preview.setMinimumSize(180, 180)

        row.addWidget(self.wheel_preview, 1)

        self.legend = QLabel(); self.legend.setWordWrap(True)

        self.legend.setMinimumWidth(180); self.legend.setMaximumWidth(270)

        style_widget(self.legend,f"font-size:9pt;color:{COLORS['text']};")

        row.addWidget(self.legend, 1); gui.addLayout(row, 1)

        layout.addWidget(preview, 1)

        for combo in (self.wheel_choice, self.wave_choice, self.mode_choice,self.theme_choice):

            combo.currentIndexChanged.connect(self.refresh)

        self.refresh()



    def values(self):

        return dict(wheel_style=self.wheel_choice.currentData(), wave_style=self.wave_choice.currentData(), wave_mode=self.mode_choice.currentData(),theme=self.theme_choice.currentData())



    def refresh(self):

        values = self.values()

        self.preview.setStyleSheet(stylesheet(values['theme']))

        self.wheel_preview.theme_override=values['theme']

        self.legend.setStyleSheet(f"font-size:9pt;color:{palette_for(values['theme'])['text']};")

        self.wheel_preview.set_visual_style(values['wheel_style'])

        self.wave_preview.set_appearance(values['wave_style'], values['wave_mode'])

        accessible=values['wheel_style']=='accessible'
        self.legend.setText(wheel_legend_html(_camelot.active_chart_name,self.wheel_preview.show_all,accessible))
        if accessible:
            self.note.setText("Colour-blind: relation colours, patterns and codes; selected key keeps its perfect-match colour with a white double outline.")
        else:
            self.note.setText("All standard designs keep the Classic key and relation palettes. Neon Outline has transparent interiors and coloured glowing labels.")




HELP_HTML = f"""

<h3 style="color:{COLORS['cyan']}">Getting started</h3>

<ol>

<li><b>Import Playlist</b> &mdash; choose a Rekordbox <code>.m3u8</code> export and its matching

TXT export. A set exported by FaderLogic can reopen directly from its M3U8, with no TXT file needed.</li>

<li><b>Saved playlists</b> &mdash; click <b>Playlists</b> in the top toolbar to show or hide

your playlist browser. Import each Rekordbox TXT/M3U8 pair once, then choose it from the browser

whenever you need it. Each playlist remembers its music folder and linked tracks. Switching

playlists keeps your current set; reopening FaderLogic restores the last playlist, your set,

and your preferences automatically. Use the browser to search, rename or remove saved entries.</li>

<li><b>Relink Folder</b> &mdash; if the audio is not where Rekordbox expects, point FaderLogic at your music folder.

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

<p><b>Click the actual highlighted wheel wedge</b> to filter the library to that exact Camelot key.
The filtered wedge gets a brighter fill, a dashed white inset outline and a white dot; its relation colour stays intact.
On the colour-blind wheel the same filter marker supplements the relation patterns and codes.
The reference track and its compatibility highlights stay unchanged until you choose another track.
Click the same wedge again to deselect, or click <b>Key … ×</b> centered in the bottom footer beneath the wheel column.
Its footer space stays reserved so the layout does not shift when the filter appears or disappears.
Search and the key filter work together. Clear both to show the full library. Switching saved playlists clears the key filter.
Filtering and sorting never rearrange your built set or exported order.</p>

<p><b>Options &rarr; Behavior</b> has two independent, saved title-sorting choices, both off by default.
<b>Ignore leading punctuation</b> sorts <i>- Zhu</i> under Z.
<b>Ignore leading track numbers</b> recognizes zero-padded counters followed by a space, such as <i>01 Title</i>,
or one to three digits followed by a period, hyphen, underscore or closing parenthesis, such as
<i>01. Title</i>, <i>02 - Title</i> and <i>01_Title</i>.
Meaningful titles such as <i>1999</i>, <i>99 Luftballons</i> and <i>2 Unlimited</i> are preserved.
Enable both for combined prefixes such as <i>- 02 - Title</i>. These preferences affect Title sorting only;
displayed titles, metadata, filenames and audio paths are unchanged.</p>

<p>Drag between column headings to resize any track column, including Title and Artist.

Drag the horizontal divider between the library and set to adjust their heights.

Your chosen sizes are remembered for next time.</p>

<p>In Options &rarr; Table columns, choose which columns to show in each table.</p>

<h3 style="color:{COLORS['cyan']}">Appearance and saved designs</h3>

<p>Open <b>Options &rarr; Appearance</b> to preview a wheel design, waveform design and

waveform mode. Click <b>Apply</b> to use and save your choices; they return at next startup.

Classic keeps the original wheel and bars; choose <b>FaderLogic · original colours</b> for the original

overlapping three-colour waveform. Obsidian Neon, Dark Minimal and Neon Outline keep the same key colours, relation colours and chart behaviour.</p>

<p><b>Interface theme</b> switches between Dark and Light in the same Appearance panel.

Preview it, then Apply to save it for next time. Harmonic key/relationship colours stay the same;

tables and controls use theme-appropriate contrast. Waveform canvases stay dark to keep all frequency colours readable.</p>

<p><b>Detailed audio waveform</b> shows a fine, continuous signed peak envelope measured from decoded audio,
including short transients. Choose <b>RGB</b> for frequency-mixed colours or <b>3-band</b> for blue bass,
orange mids and white highs on one centreline. Normal and FaderLogic original-colour modes also work.
Only the explicit Split bands designs use separate frequency lanes. Choose the design and mode under
<b>Options &rarr; Appearance</b>, then Apply to save. The preview uses the loaded track's data when available,
otherwise an analyzed dance example. Click or drag the waveform to seek. This is an overview, not a zoomable DJ deck;
it does not generate phrase labels, cues or beat grids. Existing waveform designs remain available.</p>

<p>The <b>Colour-blind</b> wheel uses blue/gold tones plus patterns, solid/dashed edges and text:

<b>SEL =</b> is selected and a same-key perfect match and <b>&times;</b> is unlisted. Chart 1 uses =, +, ++, +++, -, --, ---, M.

Chart 2 uses =, -1, +1, +2, S, D, J, M. The legend beneath the wheel gives the full names;

hover any sector for details. This wheel's alternative palette is separate from the standard colour key.</p>

<h3 style="color:{COLORS['cyan']}">Missing metadata</h3>

<p>Every unavailable table field displays <b>Unknown</b>. Available values stay intact.

The <b>!</b> row marker lists missing fields on hover and remains visible when columns are hidden.

Click <b>Metadata</b> below the tables for a scrollable review. An absent artist does not mean

a valid key/BPM is missing. Missing keys receive no compatibility highlights; key/BPM are never guessed.</p>

<h3 style="color:{COLORS['cyan']}">Playlist encoding and editing</h3>

<p>Rekordbox TXT exports use UTF-16; M3U8 playlists use UTF-8. FaderLogic reads both formats

and keeps M3U8 exports in UTF-8. Its exported sets also retain their titles, artists, BPM,

keys and playing order when reopened in FaderLogic through Import Playlist.</p>

{{VARIATION_HELP}}

{{ACCESSIBLE_HELP}}

<h3 style="color:{COLORS['cyan']}">Waveforms and playback</h3>

<p>Click a track to load its waveform. Waveforms are analysed once and cached in

<code>waveform_cache.db</code>. Click or drag the waveform to scrub.</p>

<p>Every waveform design offers <b>Normal</b> (cyan amplitude), <b>RGB</b> (measured frequency mixture)

and <b>3-band</b> (blue low, orange mid, white high on one shared centreline). RGB combines the

measured red/green/blue frequency components. <b>FaderLogic · original colours</b> retains the original

cyan/orange/pink palette. Only <b>Split bands · bars</b> and <b>Split bands · ribbons</b> use separate lanes.

The spectrogram shows measured frequency over time, with colours selected by

the mode. Energy segments describe measured quieter/medium/stronger passages, not inferred drops

or breakdowns. Multilayer combines the amplitude outline and a smoothed energy envelope.</p>

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





def _accessible_help_html():

    parts = ["<h3 style='color:" + COLORS['cyan'] + "'>Colour-blind wheel: both charts</h3>",

             "<p>This wheel uses a separate relation palette; the fill, edge colour and pattern describe the transition, not the A/B ring. White double edges and SEL = mark the selected key. Its outline colour and dots still mean a same-key perfect match. "

             "Dimmed sectors with × are unlisted; A/B and all key numbers remain printed. "

             "Patterns and relation codes carry the meaning without relying on colour. "

             "Orange-group relations also have dashed edges; the others have solid edges.</p>"]

    for chart in CHART_CHOICES:

        grouped = accessible_legend(chart, False)

        variations = accessible_legend(chart, True)

        parts.append(f"<h4>{chart}</h4><table cellpadding='4'><tr><th>Code / relation</th>"

                     "<th>Grouped outlines</th><th>All variations: outline / pattern</th></tr>")

        for (code,name,colour,pattern), (_,_,group_colour,group_pattern) in zip(variations,grouped):

            parts.append(f"<tr><td><b>{code}</b> {name}</td><td><span style='color:{group_colour}'>■ {group_colour}</span> / {group_pattern}</td>"

                         f"<td><span style='color:{colour}'>■ {colour}</span> / {pattern}</td></tr>")

        parts.append('</table>')

    return ''.join(parts)









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





class OptionRadioButton(QRadioButton):
    """A consistently round themed radio indicator at any display scaling."""
    def paintEvent(self,event):
        super().paintEvent(event)
        from PyQt6.QtWidgets import QStyle,QStyleOptionButton
        option=QStyleOptionButton();self.initStyleOption(option)
        rect=self.style().subElementRect(QStyle.SubElement.SE_RadioButtonIndicator,option,self)
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        colour=QColor(palette_for()['cyan'] if self.isChecked() else palette_for()['muted'])
        p.setPen(QPen(colour,2));p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(rect.center()),rect.width()/2-2,rect.height()/2-2)
        if self.isChecked():
            p.setPen(Qt.PenStyle.NoPen);p.setBrush(colour)
            p.drawEllipse(QPointF(rect.center()),rect.width()*.23,rect.height()*.23)
        p.end()


class OptionCheckBox(QCheckBox):
    """A visible check glyph over the themed on-state, with native input semantics."""
    def paintEvent(self,event):
        super().paintEvent(event)
        if not self.isChecked():return
        from PyQt6.QtWidgets import QStyle,QStyleOptionButton
        option=QStyleOptionButton();self.initStyleOption(option)
        rect=self.style().subElementRect(QStyle.SubElement.SE_CheckBoxIndicator,option,self)
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen=QPen(QColor('#FFFFFF' if current_theme()=='light' else '#10151D'),2);pen.setCapStyle(Qt.PenCapStyle.RoundCap);p.setPen(pen)
        x,y,w,h=rect.x(),rect.y(),rect.width(),rect.height()
        p.drawLine(QPointF(x+w*.24,y+h*.52),QPointF(x+w*.43,y+h*.70))
        p.drawLine(QPointF(x+w*.43,y+h*.70),QPointF(x+w*.77,y+h*.30));p.end()


class OptionCard(QFrame):
    """A keyboard-accessible radio choice with a whole-card click target."""
    def __init__(self,title,sample,description,parent=None):
        super().__init__(parent);self.setObjectName('optionCard')
        box=QVBoxLayout(self);box.setContentsMargins(12,8,12,8);box.setSpacing(4)
        example=QLabel(sample);example.setObjectName('choiceSample');box.addWidget(example)
        self.radio=OptionRadioButton(title);box.addWidget(self.radio)
        hint=QLabel(description);hint.setObjectName('settingsHint');hint.setWordWrap(True);box.addWidget(hint)
        for label in (example,hint):label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents,True)
        self.radio.toggled.connect(self._chosen)
    def _chosen(self,checked):
        self.setProperty('chosen',checked)
        self.style().unpolish(self);self.style().polish(self);self.update()
    def mousePressEvent(self,event):
        if event.button()==Qt.MouseButton.LeftButton:self.radio.click()
        else:super().mousePressEvent(event)


class OptionsDialog(QDialog):
    """Live wheel/table controls and an explicit Apply for appearance previews."""
    def __init__(self,wheel,icon_path,parent=None):
        super().__init__(parent);self.wheel=wheel
        self.setObjectName('optionsDialog');self.setWindowTitle('Options')
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint,True)
        style_widget(self,DIALOG_STYLE+OPTIONS_STYLE)
        screen=self.screen().availableGeometry()
        self.resize(min(840,screen.width()-40),min(700,screen.height()-40))
        self.setMinimumWidth(min(680,screen.width()-40))
        outer=QVBoxLayout(self);outer.setContentsMargins(0,0,0,0);outer.setSpacing(0)
        outer.addWidget(TitleBar(self,icon_path,'Options',''))
        body=QWidget();body_layout=QVBoxLayout(body);body_layout.setContentsMargins(14,12,14,14)
        outer.addWidget(body,1)
        self.tabs=QTabWidget();body_layout.addWidget(self.tabs)
        self.appearance=AppearancePanel(wheel,getattr(parent,'waveform',None),self)
        self.tabs.addTab(self.appearance,'Appearance')
        def heading(layout,title,description):
            text=QLabel(title);text.setObjectName('settingsTitle');layout.addWidget(text)
            hint=QLabel(description);hint.setObjectName('settingsHint');hint.setWordWrap(True);layout.addWidget(hint)
        wheel_page=QWidget();layout=QVBoxLayout(wheel_page)
        layout.setContentsMargins(16,14,16,14);layout.setSpacing(10)
        heading(layout,'Make the wheel yours','Choose the labels and transition guide that suit the way you mix.')
        label_row=QHBoxLayout();label_row.setSpacing(10);self.group=QButtonGroup(self)
        for title,sample,hint,mode in (
                ('Camelot number','8A','Quick harmonic reference','camelot'),
                ('Musical key','Am','Traditional key names','key'),
                ('Both','8A / Am','Number and musical key','both')):
            card=OptionCard(title,sample,hint);radio=card.radio
            radio.setProperty('mode',mode);self.group.addButton(radio)
            radio.setChecked(wheel.label_mode==mode)
            radio.toggled.connect(lambda checked,m=mode:checked and self._pick_label_mode(m))
            label_row.addWidget(card,1)
        layout.addLayout(label_row)
        variations=QFrame();variations.setObjectName('settingsCard')
        var_layout=QVBoxLayout(variations);var_layout.setContentsMargins(12,10,12,10)
        show_all=OptionCheckBox('Show all transition colors');show_all.setChecked(wheel.show_all)
        var_layout.addWidget(show_all)
        hint=QLabel('Give each relation its own color, or use the simpler grouped highlights.')
        hint.setObjectName('settingsHint');hint.setWordWrap(True);var_layout.addWidget(hint)
        layout.addWidget(variations)
        lower=QHBoxLayout();lower.setSpacing(12)
        charts=QVBoxLayout();self.chart_group=QButtonGroup(self)
        for index,name in enumerate(CHART_CHOICES,1):
            title='Energy boost / drop' if index==1 else 'Harmonic transitions'
            detail='Perfect matches, energy shifts and mood changes.' if index==1 else 'Step mixes, scale changes and special transitions.'
            card=QFrame();card.setObjectName('settingsCard');choice=QVBoxLayout(card)
            choice.setContentsMargins(12,9,12,9);choice.setSpacing(4)
            radio=OptionRadioButton(f'Chart {index} · {title}');choice.addWidget(radio)
            hint=QLabel(detail);hint.setObjectName('settingsHint');hint.setWordWrap(True);choice.addWidget(hint)
            self.chart_group.addButton(radio);radio.setChecked(name==_camelot.active_chart_name)
            radio.toggled.connect(lambda checked,n=name:checked and self._pick_chart(n))
            charts.addWidget(card)
        lower.addLayout(charts,1)
        preview=QFrame();preview.setObjectName('settingsCard');preview_box=QVBoxLayout(preview)
        title=QLabel('Live wheel');title.setObjectName('sectionTitle');preview_box.addWidget(title)
        self.settings_wheel=CamelotWheelWidget();self.settings_wheel.setMinimumSize(120,120)
        self.settings_wheel.set_visual_style(wheel.visual_style);self.settings_wheel.set_label_mode(wheel.label_mode)
        self.settings_wheel.set_show_all(wheel.show_all);self.settings_wheel.set_active_key(wheel.selected_key or '8A')
        preview_box.addWidget(self.settings_wheel,1)
        lower.addWidget(preview,1);layout.addLayout(lower,1)
        show_all.toggled.connect(wheel.set_show_all)
        show_all.toggled.connect(self.appearance.wheel_preview.set_show_all)
        show_all.toggled.connect(self.settings_wheel.set_show_all)
        show_all.toggled.connect(lambda *_:self.appearance.refresh())
        self.tabs.addTab(wheel_page,'Wheel')
        self.column_checks={}
        if parent is not None and hasattr(parent,'lib_table'):
            columns_page=QWidget();columns_layout=QVBoxLayout(columns_page)
            columns_layout.setContentsMargins(16,14,16,14);columns_layout.setSpacing(7)
            heading(columns_layout,'Your tables, your layout','Keep the information you use. Each table needs at least one visible column.')
            table_header=QFrame();table_header.setObjectName('settingsTableHeader')
            header=QHBoxLayout(table_header);header.setContentsMargins(12,8,12,8)
            header.addWidget(QLabel('Track information'),1)
            for title in ('Library','Set builder'):
                label=QLabel(title);label.setAlignment(Qt.AlignmentFlag.AlignCenter);label.setFixedWidth(100);header.addWidget(label)
            columns_layout.addWidget(table_header)
            descriptions={'#':'Position in the set','Title':'Track name','Artist':'Artist or performer','BPM':'Beats per minute','Camelot':'Wheel code, such as 8A','Key':'Musical key, such as Am','Time':'Track duration'}
            for row,name in enumerate(('#','Title','Artist','BPM','Camelot','Key','Time')):
                frame=QFrame();frame.setObjectName('settingsColumnRow');frame.setProperty('alternate',row%2==0)
                line=QHBoxLayout(frame);line.setContentsMargins(12,6,12,6)
                text=QLabel(f'<b>{name}</b> <span style="font-size:9pt"> · {descriptions[name]}</span>');line.addWidget(text,1)
                for table_name,table in (('library',parent.lib_table),('set',parent.set_table)):
                    cell=QWidget();cell.setFixedWidth(100);cell_box=QHBoxLayout(cell);cell_box.setContentsMargins(0,0,0,0);cell_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    found=False
                    for column in range(table.columnCount()):
                        if table.horizontalHeaderItem(column).text()!=name:continue
                        check=OptionCheckBox();check.setChecked(not table.isColumnHidden(column))
                        check.setAccessibleName(f'{table_name} {name} column')
                        check.setToolTip(f'Show {name} in the {table_name} table')
                        check.toggled.connect(lambda checked,t=table_name,c=column,box=check:self._pick_column(t,c,checked,box))
                        self.column_checks[(table_name,name)]=check;cell_box.addWidget(check);found=True
                    if not found:
                        empty=QLabel('—');empty.setObjectName('settingsHint');cell_box.addWidget(empty)
                    line.addWidget(cell)
                columns_layout.addWidget(frame)
            self.column_summary=QLabel();self.column_summary.setObjectName('settingsHint')
            columns_layout.addWidget(self.column_summary);self._refresh_column_summary()
            columns_layout.addStretch();self.tabs.addTab(columns_page,'Table columns')
        if parent is not None and hasattr(parent, 'apply_behavior'):
            behavior_page=QWidget();behavior_layout=QVBoxLayout(behavior_page)
            behavior_layout.setContentsMargins(16,14,16,14);behavior_layout.setSpacing(12)
            heading(behavior_layout,'Library behavior','Choose how titles sort. Track names, files and the order of your set stay unchanged.')
            self.behavior_checks={}
            for key,title,description in (
                    ('punctuation','Ignore leading punctuation when sorting titles','Sort alphabetically without counting symbols at the beginning of a title.'),
                    ('numbers','Ignore leading track numbers when sorting titles','Sort alphabetically without counting track-number prefixes. Original titles stay unchanged.')):
                card=QFrame();card.setObjectName('settingsCard');box=QVBoxLayout(card)
                check=OptionCheckBox(title);check.setChecked(parent.behavior[key]);box.addWidget(check)
                hint=QLabel(description);hint.setWordWrap(True);hint.setObjectName('settingsHint');box.addWidget(hint)
                self.behavior_checks[key]=check
                check.toggled.connect(lambda checked,k=key:parent.apply_behavior(dict(parent.behavior,**{k:checked})))
                behavior_layout.addWidget(card)
            behavior_layout.addStretch();self.tabs.addTab(behavior_page,'Behavior')
        close=QPushButton('Close');close.clicked.connect(self.accept)
        row=QHBoxLayout();self.appearance_status=QLabel('');self.appearance_status.setObjectName('settingsHint')
        row.addWidget(self.appearance_status);row.addStretch()
        self.apply_button=QPushButton('Apply');self.apply_button.setObjectName('primary')
        self.apply_button.clicked.connect(self._apply_appearance);row.addWidget(self.apply_button);row.addWidget(close)
        body_layout.addLayout(row)
        self.tabs.currentChanged.connect(self._tab_changed)

    def _tab_changed(self,index):
        self.apply_button.setVisible(index==0)
        self.appearance_status.setText('' if index==0 else 'Changes on this tab take effect immediately.')

    def _refresh_column_summary(self):
        counts={name:sum(box.isChecked() for (table,_),box in self.column_checks.items() if table==name) for name in ('library','set')}
        self.column_summary.setText(f"Visible columns: Library {counts['library']} · Set builder {counts['set']}")

    def _apply_appearance(self):

        values = self.appearance.values()

        if self.parent() is not None and hasattr(self.parent(), 'apply_appearance'):

            self.parent().apply_appearance(values)

        else:

            self.wheel.set_visual_style(values['wheel_style'])

        self.settings_wheel.set_visual_style(values["wheel_style"])
        self.appearance_status.setText("Appearance applied and saved.")





    def _pick_chart(self, name):

        set_active_chart(name)

        self.wheel.update()

        self.appearance.wheel_preview.set_active_key('8A')
        self.settings_wheel.set_active_key(self.wheel.selected_key or '8A')

        self.appearance.refresh()

        if self.parent() is not None and hasattr(self.parent(), "refresh_relations"):

            self.parent().refresh_relations()



    def _pick_label_mode(self, mode):

        self.wheel.set_label_mode(mode)

        self.appearance.wheel_preview.set_label_mode(mode)
        self.settings_wheel.set_label_mode(mode)



    def _pick_column(self, table_name, column, checked, box):

        if not self.parent().set_column_visible(table_name, column, checked):

            with QSignalBlocker(box):

                box.setChecked(True)
        self._refresh_column_summary()





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

        self.setWindowTitle("About FaderLogic")

        self.setWindowFlag(Qt.WindowType.FramelessWindowHint, True)

        self.setMinimumSize(620, 580)

        style_widget(self,DIALOG_STYLE)

        layout = QVBoxLayout(self)

        layout.setContentsMargins(0, 0, 0, 0)

        layout.setSpacing(0)

        layout.addWidget(TitleBar(self, icon_path, "About FaderLogic", ""))

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

        name = QLabel(f"<span style='font-size:20pt;font-weight:700'>FaderLogic</span>"

                      f"<br><span style='color:{COLORS['muted']}'>Version {__version__}</span>")

        head.addWidget(name)

        head.addStretch()

        layout.addLayout(head)

        text = QTextBrowser()

        text.setOpenExternalLinks(True)

        text.setHtml(ui_html(f"""

            <p style="font-size:12pt; color:{COLORS['text']}">

            A clearer way to build your next set.</p>

            <p>FaderLogic is a harmonic DJ set builder made for Rekordbox.

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

            or reopen it directly in FaderLogic to edit it again.</p>

            <p>Encoding follows each file type: UTF-16 for Rekordbox TXT imports,

            and UTF-8 for M3U8 playlists.</p>

            <p style="color:{COLORS['muted']}">Built with Python and PyQt6.

            Music stays in your own folders; FaderLogic saves its playlist data locally.</p>

        """))

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

        style_widget(footer,f"color:{COLORS['text']}; background: transparent;")

        layout.addWidget(footer)

        return page



    def _help_tab(self):

        browser = QTextBrowser()

        browser.setOpenExternalLinks(True)

        browser.setHtml(ui_html(HELP_HTML.replace("{VARIATION_HELP}", _variation_help_html()).replace("{ACCESSIBLE_HELP}", _accessible_help_html())))

        return browser



    def _donate_tab(self):

        page = QWidget_with_layout(QVBoxLayout)

        layout = page.layout()

        note = QLabel("If FaderLogic helps your sets, you can support its development with Bitcoin.")

        note.setWordWrap(True)

        layout.addWidget(note)

        coin = QLabel()

        coin.setPixmap(_btc_icon())

        coin.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(coin)

        qr = QLabel()

        qr.setPixmap(_qr_pixmap(f"bitcoin:{BTC_ADDRESS}"))

        qr.setAlignment(Qt.AlignmentFlag.AlignCenter)

        style_widget(qr,"background: #FFFFFF; border-radius: 8px; padding: 10px;")

        layout.addWidget(qr, 0, Qt.AlignmentFlag.AlignCenter)

        addr = QLabel(BTC_ADDRESS)

        addr.setAlignment(Qt.AlignmentFlag.AlignCenter)

        addr.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        style_widget(addr,f"color:{COLORS['neon_green']}; font-family: Consolas;")

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

        style_widget(self.copy_status,f"color: {COLORS['neon_green']};")

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



OPTIONS_STYLE = f"""
QDialog#optionsDialog QLabel#settingsTitle {{ font-size:15pt; font-weight:700; color:{COLORS['text']}; }}
QDialog#optionsDialog QLabel#settingsHint {{ color:{COLORS['muted']}; font-size:9pt; }}
QDialog#optionsDialog QFrame#optionCard, QDialog#optionsDialog QFrame#settingsCard {{ background:{COLORS['panel_alt']}; border:1px solid {COLORS['border']}; border-radius:9px; }}
QDialog#optionsDialog QFrame#optionCard[chosen="true"] {{ border:1px solid {COLORS['cyan']}; }}
QDialog#optionsDialog QFrame#optionCard:hover {{ border:1px solid {COLORS['neon_blue']}; }}
QDialog#optionsDialog QLabel#choiceSample {{ color:{COLORS['cyan']}; font-size:15pt; font-weight:700; }}
QDialog#optionsDialog QFrame#settingsTableHeader {{ background:{COLORS['panel_alt']}; border-radius:6px; color:{COLORS['cyan']}; font-weight:700; }}
QDialog#optionsDialog QFrame#settingsColumnRow {{ border-radius:5px; }}
QDialog#optionsDialog QFrame#settingsColumnRow[alternate="true"] {{ background:{COLORS['panel_alt']}; }}
QDialog#optionsDialog QCheckBox::indicator {{ width:18px; height:18px; border:1px solid {COLORS['muted']}; border-radius:4px; background:{COLORS['well']}; }}
QDialog#optionsDialog QCheckBox::indicator:checked {{ background:{COLORS['cyan']}; border:2px solid {COLORS['cyan']}; }}
QDialog#optionsDialog QRadioButton::indicator {{ width:20px; height:20px; border:none; background:transparent; }}
QDialog#optionsDialog QRadioButton::indicator:checked {{ border:none; background:transparent; }}
"""
