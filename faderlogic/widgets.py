"""Custom painted widgets: Camelot wheel and 3-band waveform."""
import math

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QFontMetricsF, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap
from PyQt6.QtWidgets import QSizePolicy, QWidget

from .camelot import CAMELOT_COLORS, VARIATIONS, get_compatibility, normalize_key
from .theme import COLORS, palette_for
from .appearance import WHEEL_STYLES, WAVE_STYLES, WAVE_MODES, RELATION_CODES, accessible_style

# Highlight colours used on the wheel and in the tables.
GREEN_HL = QColor(COLORS["green"])
ORANGE_HL = QColor(COLORS["orange"])
RED_HL = QColor(COLORS["red"])
SELECTED_HL = QColor(COLORS["cyan"])

WHEEL_ORDER = [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]


# Per-variation colours used when 'show all variations' is on (shared palette).
VARIATION_COLOURS = {name: QColor(hex_) for name, (hex_, _tint, _desc) in VARIATIONS.items()}


class CamelotWheelWidget(QWidget):
    """Two-ring Camelot wheel. Shows the selected key and its compatible keys."""

    showAllChanged = pyqtSignal(bool)
    keyClicked = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.selected_key = None
        self.filter_key = None
        self._status = {}
        self._detail = {}
        self.visual_style = "classic"
        self.setMouseTracking(True)
        self.setAccessibleName("Camelot wheel")
        self.theme_override = None

    def set_visual_style(self, style):
        self.visual_style = style if style in WHEEL_STYLES else "classic"
        self.update()

    def set_filter_key(self, key):
        self.filter_key = normalize_key(key)
        self.update()

    def key_at(self, position):
        scale = (min(self.width(), self.height()) - 12) / 200
        if scale <= 0:
            return None
        x = (position.x() - self.width()/2) / scale
        y = (self.height()/2 - position.y()) / scale
        radius = math.hypot(x, y)
        if not 32 <= radius <= 96 or abs(radius - 62) < 1:
            return None
        angle = (90 - math.degrees(math.atan2(y, x)) + 15) % 360
        if angle % 30 < .65 or angle % 30 > 29.35:
            return None
        return f"{WHEEL_ORDER[int(angle // 30)]}{'A' if radius < 62 else 'B'}"

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            code = self.key_at(event.position())
            if code and (code == self.selected_key or code in self._status or code == self.filter_key):
                self.keyClicked.emit(code)


    def segment_colours(self, code):
        """One source for the original palette across every standard design."""
        base = QColor(CAMELOT_COLORS[code])
        active = code == self.selected_key or code in self._status
        if code == self.selected_key:
            edge = QColor(SELECTED_HL)
        elif code in self._status:
            edge = QColor(VARIATION_COLOURS.get(self._detail.get(code), ORANGE_HL) if self.show_all
                          else GREEN_HL if self._status[code] == "green" else ORANGE_HL)
        else:
            edge = QColor(base)
        if self.visual_style == "accessible":
            edge = QColor(accessible_style(self._detail.get(code), self._status.get(code), self.show_all)[0] if active else "#6B7684")
            base = edge.darker(290) if active else QColor("#202630")
        return base, edge, active

    def mouseMoveEvent(self, event):
        scale = (min(self.width(), self.height()) - 12) / 200
        x = (event.position().x() - self.width()/2) / max(.1, scale)
        y = (self.height()/2 - event.position().y()) / max(.1, scale)
        radius = math.hypot(x, y)
        if 32 <= radius <= 98:
            index = int(((90 - math.degrees(math.atan2(y, x)) + 15) % 360) // 30)
            code = f"{WHEEL_ORDER[index]}{'A' if radius < 62 else 'B'}"
            relation = "Selected key" if code == self.selected_key else self._detail.get(code, "Not a listed transition" if self.selected_key else "Select a track to show relations")
            action = 'Click again to clear key filter' if code == self.filter_key else 'Click highlighted wedge to filter library'
            self.setToolTip(f"{self._label(code)} — {relation}. {action}")
        else:
            self.setToolTip("")

    # Label modes: 'camelot' (8A), 'key' (Am), 'both' (8A / Am).
    label_mode = "camelot"
    show_all = False

    def set_label_mode(self, mode):
        self.label_mode = mode
        self.update()

    def set_show_all(self, enabled):
        self.show_all = enabled
        self.update()
        self.showAllChanged.emit(enabled)

    def _label(self, code):
        from .camelot import REAL_KEYS
        if self.label_mode == "key":
            return REAL_KEYS.get(code, code)
        if self.label_mode == "both":
            return f"{code} {REAL_KEYS.get(code, code)}"
        return code

    def set_active_key(self, key):
        self.selected_key = normalize_key(key)
        self._status = {}
        self._detail = {}
        if self.selected_key:
            for code in CAMELOT_COLORS:
                colour, label = get_compatibility(self.selected_key, code)
                if colour in ("green", "orange"):
                    self._status[code] = colour
                    self._detail[code] = label
        self.setAccessibleDescription("Selected key: " + (self.selected_key or "Unknown") + ". " +
                                      "; ".join(f"{code}: {label}" for code, label in self._detail.items()))
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height()) - 12
        painter.translate(self.width() / 2, self.height() / 2)
        scale = side / 200.0
        painter.scale(scale, scale)

        if self.visual_style != "outline":
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(palette_for(self.theme_override)["panel"] if self.visual_style == "classic" else "#10151D"))
            painter.drawEllipse(QRectF(-30, -30, 60, 60))

        for idx, num in enumerate(WHEEL_ORDER):
            center = 90 - idx * 30
            start = center + 15
            self._segment(painter, 32, 62, start, center, f"{num}A")
            self._segment(painter, 62, 96, start, center, f"{num}B")
        from .camelot import REAL_KEYS
        centre_colour=palette_for(self.theme_override)['cyan'] if self.visual_style in ('classic','outline') else COLORS['cyan']
        painter.setPen(QColor("#FFFFFF" if self.visual_style == "accessible" else centre_colour))
        painter.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        painter.drawText(QRectF(-28, -13, 56, 19), Qt.AlignmentFlag.AlignCenter, self.selected_key or "—")
        painter.setFont(QFont("Segoe UI", 5))
        painter.drawText(QRectF(-29, 8, 58, 12), Qt.AlignmentFlag.AlignCenter,
                         REAL_KEYS.get(self.selected_key, 'SELECT A TRACK'))
        painter.end()


    def _segment(self, painter, inner_r, outer_r, start_angle, center_angle, code):
        def sector_path(inner_radius, outer_radius, start, sweep):
            result=QPainterPath()
            outer=QRectF(-outer_radius,-outer_radius,outer_radius*2,outer_radius*2)
            inner=QRectF(-inner_radius,-inner_radius,inner_radius*2,inner_radius*2)
            result.arcMoveTo(outer,start);result.arcTo(outer,start,sweep)
            result.arcTo(inner,start+sweep,-sweep);result.closeSubpath()
            return result
        # Each wedge owns its full angular/radial cell. Insetting its visible
        # outline leaves room for two independent colours along shared borders.
        ownership=sector_path(inner_r,outer_r,start_angle,-30)
        path=sector_path(inner_r+1.2,outer_r-1.2,start_angle-.65,-28.7)
        painter.save();painter.setClipPath(ownership,Qt.ClipOperation.IntersectClip)
        def edge_glow(colour):
            painter.setBrush(Qt.BrushStyle.NoBrush)
            for width,alpha in ((8,12),(5.5,26),(3.2,55)):
                glow=QColor(colour);glow.setAlpha(alpha)
                painter.setPen(QPen(glow,width));painter.drawPath(path)

        base = QColor(CAMELOT_COLORS[code])
        if code == self.selected_key:
            pen, fill = QPen(SELECTED_HL, 4), base
        elif code in self._status:
            if self.show_all:
                hl = VARIATION_COLOURS.get(self._detail.get(code), ORANGE_HL)
            else:
                hl = GREEN_HL if self._status[code] == "green" else ORANGE_HL
            pen, fill = QPen(hl, 4), base
        else:
            pen = QPen(QColor(palette_for(self.theme_override)["panel"]), 1)
            fill = QColor(base)
            fill=QColor("#101318")
        label_colour = QColor("#050608" if code == self.selected_key or code in self._status else "#444B54")
        if self.visual_style == "classic":
            painter.fillPath(path,QBrush(fill))
            if code==self.selected_key or code in self._status:edge_glow(pen.color())
            painter.setPen(pen);painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
        else:
            base, edge, active = self.segment_colours(code)
            selected = code == self.selected_key
            if self.visual_style == "accessible":
                painter.fillPath(path, base if active else QColor("#202630"))
                if active:
                    texture = QColor(edge); texture.setAlpha(70)
                    pattern_name = accessible_style(self._detail.get(code), self._status.get(code), self.show_all)[1]
                    pattern = {'dots': Qt.BrushStyle.Dense6Pattern, 'dense dots': Qt.BrushStyle.Dense4Pattern,
                               'forward hatch': Qt.BrushStyle.BDiagPattern, 'back hatch': Qt.BrushStyle.FDiagPattern,
                               'cross hatch': Qt.BrushStyle.CrossPattern, 'horizontal': Qt.BrushStyle.HorPattern,
                               'vertical': Qt.BrushStyle.VerPattern, 'diagonal cross': Qt.BrushStyle.DiagCrossPattern}[pattern_name]
                    painter.fillPath(path, QBrush(texture, pattern))
                if active:edge_glow(edge)
                pen = QPen(edge if active else QColor("#303842"), 2.6 if selected else 1.3)
                if active and not selected and self._status[code] == "orange":
                    pen.setStyle(Qt.PenStyle.DashLine)
                painter.setPen(pen); painter.setBrush(Qt.BrushStyle.NoBrush); painter.drawPath(path)
                if selected:
                    # White rails mark selection while the relation-coloured edge
                    # and dot pattern still identify the same-key perfect match.
                    painter.setPen(QPen(QColor('#FFFFFF'), 2.8)); painter.drawPath(path)
                    painter.setPen(QPen(edge, 1.4)); painter.drawPath(path)
                label_colour = QColor("#FFFFFF" if active else "#505965")
            else:
                if self.visual_style == "outline":
                    # No painted segment fill or centre disk: the parent shows through.
                    label_colour = QColor(edge if active or not self.selected_key else base.darker(350))
                    if palette_for(self.theme_override)['bg']!='#16181C':label_colour=label_colour.darker(180)
                else:
                    gradient = QLinearGradient(QPointF(0, -96), QPointF(0, 96))
                    strength = .58 if self.visual_style == "obsidian" else .23
                    tint = QColor(base); tint.setAlphaF(strength if active else .025)
                    gradient.setColorAt(0, tint); gradient.setColorAt(1, QColor("#0D121A"))
                    painter.fillPath(path, gradient)
                    label_colour = QColor(base.lighter(135) if active else base.darker(350))
                # Layered translucent strokes give a bright halo without changing hue.
                if active:
                    for width, alpha in ((9, 15), (6, 27), (3.8, 70)):
                        glow = QColor(edge); glow.setAlpha(alpha)
                        painter.setPen(QPen(glow, width)); painter.setBrush(Qt.BrushStyle.NoBrush); painter.drawPath(path)
                border = QColor(edge); border.setAlpha(255 if active else 25)
                painter.setPen(QPen(border, 1.5 if active else .5))
                painter.setBrush(Qt.BrushStyle.NoBrush); painter.drawPath(path)

        if code == self.filter_key:
            # Keep the relation palette underneath a distinct filter marker.
            tint = QColor('#FFFFFF'); tint.setAlpha(48)
            painter.fillPath(path, tint)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor('#FFFFFF'), 1.1, Qt.PenStyle.DashLine))
            painter.drawPath(path)
            mark_radius = outer_r - 3.7
            angle = math.radians(center_angle)
            painter.setBrush(QColor('#FFFFFF')); painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(mark_radius*math.cos(angle), -mark_radius*math.sin(angle)), 1.5, 1.5)
        painter.restore()
        # Labels: the number and key name, placed at the centre of the ring segment.
        radius = (inner_r + outer_r) / 2
        rad = math.radians(center_angle)
        x, y = radius * math.cos(rad), -radius * math.sin(rad)
        painter.setPen(QPen(label_colour))
        font = QFont("Segoe UI", 8)
        font.setBold(True)
        painter.setFont(font)
        def label_text(bounds, text):
            if self.visual_style == 'outline':
                # Glow the glyphs themselves in the same colour as their edge.
                metrics = QFontMetricsF(painter.font())
                glyphs = QPainterPath()
                glyphs.addText(QPointF(bounds.center().x()-metrics.horizontalAdvance(text)/2,
                                      bounds.center().y()+(metrics.ascent()-metrics.descent())/2), painter.font(), text)
                for width, alpha in ((1.7, 22), (.9, 55)):
                    glow = QColor(label_colour); glow.setAlpha(alpha)
                    painter.strokePath(glyphs, QPen(glow, width))
                painter.fillPath(glyphs, label_colour)
            else:
                painter.drawText(bounds, Qt.AlignmentFlag.AlignCenter, text)
        if self.visual_style == "accessible":
            from .camelot import REAL_KEYS
            # Pixel-sized fonts are in wheel coordinates, so Windows display
            # scaling cannot inflate them beyond the narrow inner-ring wedges.
            def fitted_text(top, height, text, pixels, width=25):
                font=QFont("Segoe UI");font.setBold(True);font.setPixelSize(pixels)
                while (QFontMetricsF(font).horizontalAdvance(text)>width-1 or QFontMetricsF(font).height()>height) and font.pixelSize()>4:
                    font.setPixelSize(font.pixelSize()-1)
                painter.setFont(font)
                painter.drawText(QRectF(x-width/2,y+top,width,height),Qt.AlignmentFlag.AlignCenter,text)
            tag = "SEL =" if code == self.selected_key else RELATION_CODES.get(self._detail.get(code), "×" if self.selected_key else "")
            if self.label_mode=='both':
                fitted_text(-12,8,code,8)
                fitted_text(-4,8,REAL_KEYS.get(code,code),7)
                fitted_text(4,7,tag,5)
            else:
                fitted_text(-9,11,self._label(code),8)
                fitted_text(2,8,tag,5)
        elif self.label_mode == "both":
            from .camelot import REAL_KEYS
            small = QFont("Segoe UI", 6)
            small.setBold(True)
            painter.setFont(small)
            label_text(QRectF(x - 22, y - 13, 44, 13), code)
            label_text(QRectF(x - 22, y, 44, 12), REAL_KEYS.get(code, code))
        else:
            label_text(QRectF(x - 22, y - 10, 44, 20), self._label(code))


class TrackDetailsWidget(QWidget):
    """Stationary selected-track details, elided to fit with full text on hover."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._text = "Select a track to see its details"
        self.setFixedHeight(20)
        self.setStyleSheet("font-size: 9pt;")
        self.setToolTip(self._text)

    def set_text(self, text):
        self._text = text
        self.setToolTip(text)
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(COLORS["well"]))
        painter.setPen(QPen(QColor(COLORS["text"])))
        painter.setFont(self.font())
        metrics = painter.fontMetrics()
        bounds = self.rect().adjusted(6, 0, -6, 0)
        text = metrics.elidedText(self._text, Qt.TextElideMode.ElideRight, bounds.width())
        painter.drawText(bounds, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
        painter.end()


class WaveformWidget(QWidget):
    """Draws 3-band RGB waveform bars with a playhead. Click or drag to scrub."""

    scrubRequested = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(48)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMouseTracking(True)
        self.title = ""
        self.bars = []
        self.progress = 0.0
        self.message = "Select a track to render its waveform"
        self.visual_style = "classic"
        self.colour_mode = "bands"
        self._art = None
        self._art_key = None
        self.setAccessibleName("Track waveform; click or drag to seek")

    def set_appearance(self, style, mode):
        self.visual_style = style if style in WAVE_STYLES else "classic"
        self.colour_mode = mode if mode in WAVE_MODES else "bands"
        self._art = None
        self.setToolTip("3-band: blue bass, orange mid, white high, sharing one centreline. RGB: a measured frequency-colour mixture. "
                        "Choose a Split bands design for three separate lanes. FaderLogic mode retains the original colours. "
                        "Frequency analysis: bass below 250 Hz, mid 250–2500 Hz, high above 2500 Hz. "
                        "Energy segments show measured quieter / medium / stronger passages, not inferred DJ sections. "
                        "Click or drag to seek.")
        self.update()

    def set_track(self, title, bars=None):
        self.title = title
        self.bars = bars or []
        self.message = "Waveform unavailable" if title else "Select a track to render its waveform"
        self._art = None
        self.progress = 0.0
        self.update()

    def set_loading(self):
        self.bars = []
        self._art = None
        self.message = "Analyzing Waveform"
        self.update()

    def set_progress(self, fraction):
        self.progress = max(0.0, min(1.0, fraction))
        self.update()

    def _scrub(self, event):
        if self.bars:
            self.scrubRequested.emit(max(0.0, min(1.0, event.position().x() / self.width())))

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._scrub(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._scrub(event)

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        painter.fillRect(self.rect(), QColor(COLORS["well"]))

        if not self.bars:
            painter.setPen(QColor(COLORS["muted"]))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self.message)
            painter.end()
            return


        played_x = w * self.progress
        art_key = (w, h, self.visual_style, self.colour_mode)
        if self._art is None or self._art_key != art_key:
            self._art = QPixmap(w, h)
            self._art.fill(Qt.GlobalColor.transparent)
            canvas = QPainter(self._art)
            canvas.setRenderHint(QPainter.RenderHint.Antialiasing)
            self._draw_waveform(canvas, w, h)
            canvas.end()
            self._art_key = art_key
        painter.drawPixmap(0, 0, self._art)
        self._draw_cursor(painter)
        painter.end()

    def _draw_cursor(self,painter):
        w,h=self.width(),self.height();played_x=w*self.progress
        painter.fillRect(QRectF(played_x, 0, w - played_x, h), QColor(10, 13, 18, 110))
        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        painter.drawLine(int(played_x), 0, int(played_x), h)
        painter.setBrush(QColor(COLORS['cyan'])); painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(played_x, 3), 3, 3)

    def _draw_waveform(self, painter, width, height):
        from .wave_paint import draw_waveform
        draw_waveform(painter, width, height, self.bars, self.visual_style, self.colour_mode)


