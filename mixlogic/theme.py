"""Colour palette and Qt stylesheet for MixLogic."""

COLORS = {
    "bg": "#16181C",
    "panel": "#1E2127",
    "panel_alt": "#23262D",
    "well": "#121417",
    "border": "#2C3038",
    "text": "#E4E7EC",
    "muted": "#8A919E",
    "cyan": "#00E5FF",
    "neon_blue": "#2F9BFF",
    "neon_green": "#39FF88",
    "green": "#2EE67A",
    "orange": "#FF9A2E",
    "red": "#FF4D5E",
    "wave_low": "#00D2FF",
    "wave_mid": "#FFB800",
    "wave_high": "#FF3366",
}

STYLESHEET = f"""
QMainWindow, QWidget#root {{ background-color: {COLORS['bg']}; }}
QWidget {{ color: {COLORS['text']}; font-family: "Segoe UI"; font-size: 10pt; }}
QLabel#sectionTitle {{ color: {COLORS['cyan']};    font-size: 10pt; font-weight: bold; }}
QFrame#logoTile {{ background-color: #1A1D22; border: 1px solid {COLORS['border']}; border-radius: 12px; }}
QLabel#brandTitle {{ color: #F0F2F5; font-size: 20pt; font-weight: 700; }}
QLabel#brandVersion {{ color: {COLORS['muted']}; font-size: 11pt; }}
QLabel#hint {{ color: {COLORS['muted']}; }}
QFrame#card {{ background-color: {COLORS['panel']}; border: 1px solid {COLORS['border']}; border-radius: 8px; }}
QPushButton {{
    background-color: {COLORS['panel_alt']}; color: {COLORS['text']};
    border: 1px solid {COLORS['border']}; border-radius: 6px; padding: 7px 14px; font-weight: 600;
}}
QPushButton:hover {{ background-color: #2A3340; border: 1px solid {COLORS['neon_blue']}; color: #FFFFFF; }}
QPushButton:pressed {{ background-color: #1A2230; }}
QPushButton#playlistToggle:checked {{ background-color: #1D3550; border: 1px solid {COLORS['neon_blue']}; color: {COLORS['cyan']}; }}
QPushButton#relinkFolder:checked {{ background-color: #1D3550; border: 1px solid {COLORS['neon_blue']}; color: {COLORS['cyan']}; }}
QPushButton#primary {{ border: 1px solid {COLORS['neon_green']}; color: {COLORS['neon_green']}; }}
QPushButton#primary:hover {{ background-color: #1B3A2A; border: 1px solid {COLORS['neon_green']}; color: #FFFFFF; }}
QPushButton#playTransport {{ background-color: #12363D; border: 1px solid {COLORS['cyan']}; color: {COLORS['cyan']}; }}
QPushButton#playTransport:hover {{ background-color: #1A505A; color: #FFFFFF; }}
QPushButton#playTransport:pressed {{ background-color: #0D282E; }}
QPushButton#stopTransport {{ background-color: #3D2028; border: 1px solid {COLORS['red']}; color: #FF7C89; }}
QPushButton#stopTransport:hover {{ background-color: #63303C; color: #FFFFFF; }}
QPushButton#stopTransport:pressed {{ background-color: #2B171D; }}
QPushButton:disabled {{ color: #5A606B; border: 1px solid #262A31; }}
QLineEdit {{
    background-color: {COLORS['well']}; color: {COLORS['text']};
    border: 1px solid {COLORS['border']}; border-radius: 6px; padding: 6px 10px;
}}
QLineEdit:focus {{ border: 1px solid {COLORS['neon_blue']}; }}
QTableWidget {{
    background-color: {COLORS['well']}; alternate-background-color: #171A1F;
    gridline-color: #20242B; border: 1px solid {COLORS['border']}; border-radius: 6px;
    selection-background-color: #1D3550; selection-color: {COLORS['text']};
}}
QHeaderView {{ background-color: {COLORS['panel_alt']}; }}
QHeaderView::section {{
    background-color: {COLORS['panel_alt']}; color: {COLORS['neon_blue']};
    padding: 6px; border: none; border-bottom: 1px solid {COLORS['neon_blue']}; font-weight: bold;
}}
QTableCornerButton::section {{ background-color: {COLORS['panel_alt']}; border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; border: none; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 0; border: none; }}
QScrollArea {{ background: {COLORS['bg']}; border: none; }}
QScrollArea > QWidget > QWidget {{ background: {COLORS['bg']}; }}
QWidget#qt_scrollarea_viewport {{ background: {COLORS['bg']}; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
QAbstractScrollArea::corner {{ background: transparent; border: none; }}
QScrollBar::handle:vertical {{ background: #2C3038; border-radius: 5px; min-height: 24px; }}
QScrollBar::handle:horizontal {{ background: #2C3038; border-radius: 5px; min-width: 24px; }}
QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{ background: {COLORS['neon_blue']}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QSlider::groove:horizontal {{ height: 6px; background: #2A2F38; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: {COLORS['neon_green']}; border-radius: 3px; }}
QSlider::handle:horizontal {{ background: {COLORS['cyan']}; width: 14px; margin: -5px 0; border-radius: 7px; }}
QSlider::handle:horizontal:hover {{ background: #FFFFFF; }}
QSpinBox {{
    background-color: {COLORS['well']}; color: {COLORS['text']};
    border: 1px solid {COLORS['border']}; border-radius: 6px; padding: 4px 8px;
}}
QSpinBox:focus {{ border: 1px solid {COLORS['neon_blue']}; }}
QMessageBox {{ background-color: {COLORS['panel']}; }}
QSplitter {{ background: {COLORS['bg']}; }}
QSplitter::handle {{ background: {COLORS['bg']}; }}
QWidget#root, QWidget#body {{ background: {COLORS['bg']}; }}
QWidget#scrollBody {{ background: {COLORS['bg']}; }}
QSplitter::handle:horizontal {{ width: 10px; }}
QSplitter#tableSplitter::handle:vertical {{ height: 10px; background: #2C3038; border-radius: 4px; }}
QSplitter#tableSplitter::handle:vertical:hover {{ background: {COLORS['neon_blue']}; }}
QToolTip {{ background-color: {COLORS['panel_alt']}; color: {COLORS['text']}; border: 1px solid {COLORS['neon_blue']}; }}
"""
