"""Custom painted widgets: Camelot wheel and 3-band waveform."""
import math

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtWidgets import QSizePolicy, QWidget

from .camelot import CAMELOT_COLORS, VARIATIONS, get_compatibility, normalize_key
from .theme import COLORS

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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(120, 120)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.selected_key = None
        self._status = {}
        self._detail = {}

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
        self.update()

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        side = min(self.width(), self.height()) - 12
        painter.translate(self.width() / 2, self.height() / 2)
        scale = side / 200.0
        painter.scale(scale, scale)

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(COLORS["panel"]))
        painter.drawEllipse(QRectF(-30, -30, 60, 60))

        for idx, num in enumerate(WHEEL_ORDER):
            center = 90 - idx * 30
            start = center + 15
            self._segment(painter, 32, 62, start, center, f"{num}A")
            self._segment(painter, 62, 96, start, center, f"{num}B")
        painter.end()

    def _segment(self, painter, inner_r, outer_r, start_angle, center_angle, code):
        path = QPainterPath()
        outer = QRectF(-outer_r, -outer_r, outer_r * 2, outer_r * 2)
        inner = QRectF(-inner_r, -inner_r, inner_r * 2, inner_r * 2)
        path.arcMoveTo(outer, start_angle)
        path.arcTo(outer, start_angle, -30)
        path.arcTo(inner, start_angle - 30, 30)
        path.closeSubpath()

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
            pen = QPen(QColor(COLORS["panel"]), 1)
            fill = QColor(base)
            fill.setAlpha(60)
        painter.setPen(pen)
        painter.setBrush(QBrush(fill))
        painter.drawPath(path)

        # Labels: the number and key name, placed at the centre of the ring segment.
        radius = (inner_r + outer_r) / 2
        rad = math.radians(center_angle)
        x, y = radius * math.cos(rad), -radius * math.sin(rad)
        painter.setPen(QPen(QColor("#050608")))
        font = QFont("Segoe UI", 8)
        font.setBold(True)
        painter.setFont(font)
        if self.label_mode == "both":
            from .camelot import REAL_KEYS
            small = QFont("Segoe UI", 6)
            small.setBold(True)
            painter.setFont(small)
            painter.drawText(QRectF(x - 22, y - 13, 44, 13), Qt.AlignmentFlag.AlignCenter, code)
            painter.drawText(QRectF(x - 22, y, 44, 12), Qt.AlignmentFlag.AlignCenter, REAL_KEYS.get(code, code))
        else:
            painter.drawText(QRectF(x - 22, y - 10, 44, 20), Qt.AlignmentFlag.AlignCenter, self._label(code))


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

    def set_track(self, title, bars=None):
        self.title = title
        self.bars = bars or []
        self.progress = 0.0
        self.update()

    def set_loading(self):
        self.bars = []
        self.message = "Analysing waveform..."
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

        mid_y = h / 2.0
        bar_w = w / len(self.bars)
        played_x = w * self.progress
        for i, (low, mid, high) in enumerate(self.bars):
            x = i * bar_w + bar_w / 2.0
            played = x <= played_x
            pen_w = max(1.0, bar_w - 1.2)
            for amp, colour, alpha, scale in (
                (low, COLORS["wave_low"], 255, 0.42),
                (mid, COLORS["wave_mid"], 255, 0.32),
                (high, COLORS["wave_high"], 255, 0.22),
            ):
                c = QColor(colour)
                c.setAlpha(alpha if played else 90)
                half = amp * h * scale
                painter.setPen(QPen(c, pen_w, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                painter.drawLine(int(x), int(mid_y - half), int(x), int(mid_y + half))

        painter.setPen(QPen(QColor("#FFFFFF"), 2))
        painter.drawLine(int(played_x), 0, int(played_x), h)
        painter.end()
