"""Draw the FaderLogic icon (a neon ring with a waveform bar) and save assets/faderlogic.ico."""
import os
import sys

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPen, QBrush
from PyQt6.QtWidgets import QApplication

SIZES = [16, 32, 48, 64, 128, 256]


def draw(size):
    img = QImage(size, size, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    s = size
    rounded = QRectF(s * 0.04, s * 0.04, s * 0.92, s * 0.92)
    grad = QLinearGradient(QPointF(0, 0), QPointF(s, s))
    grad.setColorAt(0.0, QColor("#1E2228"))
    grad.setColorAt(1.0, QColor("#111316"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(grad))
    p.drawRoundedRect(rounded, s * 0.2, s * 0.2)

    ring = QRectF(s * 0.2, s * 0.2, s * 0.6, s * 0.6)
    p.setBrush(Qt.BrushStyle.NoBrush)
    arc_pen = QPen(QColor("#2F9BFF"), max(1.0, s * 0.09))
    arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(arc_pen)
    p.drawArc(ring, 40 * 16, 260 * 16)
    green_pen = QPen(QColor("#39FF88"), max(1.0, s * 0.09))
    green_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(green_pen)
    p.drawArc(ring, -100 * 16, 120 * 16)

    bars = [0.25, 0.5, 0.85, 0.6, 0.35]
    bar_w = s * 0.07
    gap = s * 0.035
    x0 = s / 2 - (len(bars) * bar_w + (len(bars) - 1) * gap) / 2
    for i, h in enumerate(bars):
        color = QColor("#00E5FF") if i % 2 == 0 else QColor("#39FF88")
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(color))
        bh = s * 0.36 * h
        p.drawRoundedRect(QRectF(x0 + i * (bar_w + gap), s / 2 - bh / 2, bar_w, bh), bar_w / 2, bar_w / 2)
    p.end()
    return img


def main():
    app = QApplication(sys.argv)
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
    os.makedirs(out_dir, exist_ok=True)
    big = draw(256)
    png = os.path.join(out_dir, "faderlogic.png")
    big.save(png)
    frames = [draw(s) for s in SIZES]
    ico = os.path.join(out_dir, "faderlogic.ico")
    frames[-1].save(ico)  # Qt writes the largest frame; Pillow-free fallback below
    try:
        from PIL import Image
        Image.open(png).save(ico, sizes=[(s, s) for s in SIZES])
    except ImportError:
        pass
    print("wrote", png, ico)
    app.quit()


if __name__ == "__main__":
    main()
