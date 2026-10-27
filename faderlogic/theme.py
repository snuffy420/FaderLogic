"""Colour palette and Qt stylesheet for FaderLogic."""

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

UI_THEMES = {'dark':'Dark','light':'Light'}
_current_theme = 'dark'
LIGHT_COLORS = dict(COLORS, bg='#EEF2F7',panel='#FFFFFF',panel_alt='#E5EBF3',well='#F7F9FC',
    border='#C7D2E0',text='#172B42',muted='#53677F',cyan='#006C85',neon_blue='#1765B5',
    neon_green='#087A42',green='#087A42',orange='#9C5800',red='#BD2942')


def current_theme(): return _current_theme


def palette_for(name=None): return LIGHT_COLORS if (name or _current_theme)=='light' else COLORS


def ui_style(css,name=None):
    """Adapt UI chrome; chart/material palettes remain independent and unchanged."""
    if (name or _current_theme)!='light':return css
    import re
    mapping={value.lower():LIGHT_COLORS[key] for key,value in COLORS.items() if value!=LIGHT_COLORS[key]}
    mapping.update({'#0b0c0e':'#E5EBF3','#1a1d22':'#E5EBF3','#f0f2f5':'#172B42',
        '#2a3340':'#DCE7F5','#1a2230':'#D3E1F1','#1d3550':'#D8E9FB','#1b3a2a':'#D9F1E4',
        '#12363d':'#D8EEF4','#1a505a':'#C0E2EC','#0d282e':'#B1D4DF',
        '#3d2028':'#F9E3E8','#63303c':'#F1CAD4','#2b171d':'#E7B7C3','#ff7c89':'#BD2942',
        '#5a606b':'#7A8797','#262a31':'#D8DFE8','#171a1f':'#F1F5FA','#20242b':'#D8E0EB',
        '#2a2f38':'#C7D2E0','#26313d':'#E5EFFB','#afbacb':'#53677F'})
    css=re.sub(r'#[0-9a-fA-F]{6}',lambda match:mapping.get(match.group().lower(),match.group()),css)
    css=re.sub(r'(?<![-\w])color:\s*#FFFFFF\b','color: #172B42',css,flags=re.IGNORECASE)
    return css


def style_widget(widget,dark_css):
    widget.setProperty('_faderlogic_dark_css',dark_css)
    widget.setStyleSheet(ui_style(dark_css))


def stylesheet(name=None):return ui_style(STYLESHEET,name)


def ui_html(html):
    if _current_theme!='light':return html
    import re
    mapping={COLORS[key].lower():LIGHT_COLORS[key] for key in ('text','muted','cyan','green','orange','red')}
    return re.sub(r'(?<![-\w])color:\s*(#[0-9a-fA-F]{6})',
        lambda match:'color:'+mapping.get(match.group(1).lower(),match.group(1)),html)


def apply_theme(name):
    global _current_theme
    from PyQt6.QtWidgets import QApplication,QWidget
    from PyQt6.QtGui import QColor,QPalette
    _current_theme=name if name in UI_THEMES else 'dark'
    app=QApplication.instance()
    if app is None:return
    if app.property('_faderlogic_theme')==_current_theme:return
    app.setProperty('_faderlogic_theme',_current_theme)
    colours=palette_for()
    palette=QPalette()
    for role,key in ((QPalette.ColorRole.Window,'bg'),(QPalette.ColorRole.Base,'well'),
            (QPalette.ColorRole.AlternateBase,'panel_alt'),(QPalette.ColorRole.Button,'panel_alt'),
            (QPalette.ColorRole.WindowText,'text'),(QPalette.ColorRole.Text,'text'),
            (QPalette.ColorRole.ButtonText,'text'),(QPalette.ColorRole.PlaceholderText,'muted'),
            (QPalette.ColorRole.Link,'neon_blue')):
        palette.setColor(role,QColor(colours[key]))
    palette.setColor(QPalette.ColorRole.Highlight,QColor('#D8E9FB' if name=='light' else '#1D3550'))
    palette.setColor(QPalette.ColorRole.HighlightedText,QColor(colours['text']))
    app.setPalette(palette);app.setStyleSheet(stylesheet())
    for widget in app.allWidgets():
        if widget.window().property('_faderlogic_closed'):continue
        ancestor=widget;preview=False
        while ancestor is not None:
            if ancestor.property('_appearance_preview'):preview=True;break
            ancestor=ancestor.parentWidget()
        if preview:continue
        template=widget.property('_faderlogic_dark_css')
        if template is not None:widget.setStyleSheet(ui_style(template))
        widget.update()

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
QComboBox {{ background-color: {COLORS['well']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']}; border-radius: 5px; padding: 6px 28px 6px 8px; min-height: 20px; }}
QComboBox:hover, QComboBox:focus {{ border-color: {COLORS['cyan']}; }}
QComboBox::drop-down {{ border: none; width: 22px; background: {COLORS['panel_alt']}; }}
QComboBox QAbstractItemView {{ background-color: {COLORS['panel']}; color: {COLORS['text']}; selection-background-color: #1D3550; selection-color: {COLORS['cyan']}; border: 1px solid {COLORS['border']}; padding: 4px; }}
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
