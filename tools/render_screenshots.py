"""Render the current GUI using generated audio and example Rekordbox metadata."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_SCALE_FACTOR", "1.25")
from array import array
import math
from pathlib import Path
import shutil
import sys
import time
from uuid import uuid4
import wave

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QFontDatabase, QIcon
from PyQt6.QtWidgets import QApplication, QTabWidget
from PyQt6 import sip
from faderlogic import __version__, camelot, playlist
from faderlogic.dialogs import AboutDialog, OptionsDialog, MessageDialog, RenameDialog, StyledMessageBox, MetadataReviewDialog
from faderlogic.appearance import WHEEL_STYLES, WAVE_STYLES
from faderlogic.main_window import MainWindow
from faderlogic.theme import STYLESHEET
from faderlogic.waveform import compute_bands


def render_galleries(app,output):
    from PyQt6.QtWidgets import QWidget,QGridLayout,QVBoxLayout,QLabel,QFrame
    from faderlogic.widgets import CamelotWheelWidget,WaveformWidget
    from faderlogic.appearance import WAVE_MODES,wheel_legend_html
    from faderlogic.dance_preview import DANCE_PREVIEW
    camelot.set_active_chart(next(iter(camelot.CHART_CHOICES)))
    def save(widget,name):
        widget.show()
        for _ in range(3):app.processEvents()
        if not widget.grab().save(str(output/name)):raise RuntimeError(name)
        widget.close()
    wheels=QWidget();wheels.setObjectName('root');grid=QGridLayout(wheels)
    for i,(style,title) in enumerate(WHEEL_STYLES.items()):
        card=QFrame();card.setObjectName('card');box=QVBoxLayout(card)
        heading=QLabel(title);heading.setObjectName('sectionTitle');box.addWidget(heading)
        wheel=CamelotWheelWidget();wheel.setFixedSize(280,280);wheel.set_visual_style(style)
        wheel.set_show_all(True);wheel.set_active_key('5A');box.addWidget(wheel)
        grid.addWidget(card,i//3,i%3)
    save(wheels,'wheel-gallery.png')
    waves=QWidget();waves.setObjectName('root');grid=QGridLayout(waves)
    for i,(style,title) in enumerate(WAVE_STYLES.items()):
        card=QFrame();card.setObjectName('card');box=QVBoxLayout(card)
        heading=QLabel(title);heading.setObjectName('sectionTitle');box.addWidget(heading)
        wave=WaveformWidget();wave.setFixedSize(350,48);wave.set_track('Generated dance overview',list(DANCE_PREVIEW))
        wave.set_appearance(style,'bands');wave.set_progress(.4);box.addWidget(wave)
        grid.addWidget(card,i//3,i%3)
    save(waves,'waveform-gallery.png')
    modes=QWidget();modes.setObjectName('root');box=QVBoxLayout(modes)
    for mode,title in WAVE_MODES.items():
        heading=QLabel(title);heading.setObjectName('sectionTitle');box.addWidget(heading)
        wave=WaveformWidget();wave.setFixedSize(1100,48);wave.set_track('Same audio overview',list(DANCE_PREVIEW))
        wave.set_appearance('enhanced',mode);wave.set_progress(.4);box.addWidget(wave)
    save(modes,'waveform-modes.png')
    accessible=QWidget();accessible.setObjectName('root');box=QVBoxLayout(accessible)
    wheel=CamelotWheelWidget();wheel.setFixedSize(600,600);wheel.set_visual_style('accessible')
    wheel.set_label_mode('both');wheel.set_show_all(True);wheel.set_active_key('11A');box.addWidget(wheel)
    legend=QLabel(wheel_legend_html(camelot.active_chart_name,True,True));legend.setWordWrap(True);legend.setMaximumWidth(600);box.addWidget(legend)
    save(accessible,'accessible-both.png')


def main():
    output = ROOT / "docs" / "screenshots" / __version__
    output.mkdir(parents=True, exist_ok=True)
    temporary_root = ROOT / ".build-temp"
    temporary_root.mkdir(exist_ok=True)
    stage = temporary_root / ("screenshots-" + uuid4().hex)
    stage.mkdir()
    if not stage.resolve().is_relative_to(temporary_root.resolve()):
        raise RuntimeError("Invalid screenshot staging path")
    app = QApplication([])
    for name in ("segoeui.ttf", "segoeuib.ttf", "seguisym.ttf"):
        path = Path("C:/Windows/Fonts") / name
        if path.exists():
            QFontDatabase.addApplicationFont(str(path))
    app.setStyleSheet(STYLESHEET)
    icon_path = str(ROOT / "assets/faderlogic.ico")
    window = None
    try:
        audio = stage / "demo.wav"
        rate, seconds = 22050, 60
        samples = array("h")
        for index in range(rate * seconds):
            t = index / rate
            envelope = .3 + .65 * math.sin(math.pi * t / seconds) ** 2
            beat = math.exp(-(t % .5) * 14)
            value = envelope * (.43 * math.sin(2 * math.pi * 55 * t) * beat
                                + .18 * math.sin(2 * math.pi * 220 * t)
                                + .055 * math.sin(2 * math.pi * 2200 * t) * math.exp(-(t % .25) * 35))
            samples.append(round(value * 32767))
        if sys.byteorder != "little":
            samples.byteswap()
        with wave.open(str(audio), "wb") as stream:
            stream.setnchannels(1); stream.setsampwidth(2); stream.setframerate(rate)
            stream.writeframes(samples.tobytes())
        bars = compute_bands(str(audio))
        if max(value[0] for value in bars) - min(value[0] for value in bars) < .03:
            raise RuntimeError("Generated audio waveform did not decode correctly")
        window = MainWindow(str(stage), icon_path)
        names = [("Midnight Signal", "8A"), ("Afterglow", "9A"), ("The Long Way Home", "8B"),
                 ("Electric City", "7A"), ("Into the Blue", "10A"), ("Last Light", "8A"),
                 ("Open Skies", "9B"), ("Echoes", "6A")]
        tracks = []
        for index, (title, key) in enumerate(names):
            path = stage / (title + " (Demo).wav")
            shutil.copy2(audio, path)
            tracks.append(dict(title=title + " (Demo)", artist="FaderLogic Demo", bpm=f"{124 + index}.0",
                               key=key, duration=60.0, time="01:00", path=str(path)))
            window.cache.put(str(path), bars)
        for name, subset in (("Warmup", tracks[:4]), ("Peak Time", tracks), ("Closing Set", tracks[4:])):
            m3u = stage / (name + ".m3u8")
            txt = stage / (name + ".txt")
            m3u.write_text("#EXTM3U\n" + "".join(f"#EXTINF:60,{t['title']}\n{t['path']}\n" for t in subset), encoding="utf-8")
            txt.write_text("Track Title\tArtist\tBPM\tKey\n" + "".join(f"{t['title']}\t{t['artist']}\t{t['bpm']}\t{t['key']}\n" for t in subset), encoding="utf-16")
            entry = window.store.add_playlist(str(m3u), str(txt), playlist.build_library(str(m3u), str(txt)))
            if name == "Peak Time":
                active_id = entry
        window._activate_playlist(active_id)
        window.active_set = [dict(track) for track in tracks[:6]]
        window._fill_set()
        window.overlap.setValue(15)
        window.linked_folder = r"C:\Music\FaderLogic Demo"
        window._refresh_playlist_browser()
        window.btn_playlists.setChecked(True)
        window.resize(1280, 800)
        window.show()

        def capture(widget, filename):
            for _ in range(4):
                app.processEvents()
            if not widget.grab().save(str(output / filename)):
                raise RuntimeError("Could not save screenshot " + filename)

        window.set_table.selectRow(0)
        window.wheel.set_show_all(True)
        window.waveform.set_progress(.32)
        capture(window, "main.png")
        for chart, filename in zip(camelot.CHART_CHOICES, ("chart-1.png", "chart-2.png")):
            camelot.set_active_chart(chart)
            window.refresh_relations()
            window.waveform.set_progress(.32)
            capture(window, filename)
        capture(window.playlist_browser,"playlist-browser.png")
        options = OptionsDialog(window.wheel, icon_path, window)
        options.show()
        capture(options, "appearance-classic.png")
        for style in WHEEL_STYLES:
            options.appearance.wheel_choice.setCurrentIndex(options.appearance.wheel_choice.findData(style))
            options.appearance.wave_choice.setCurrentIndex(options.appearance.wave_choice.findData('filled'))
            options.appearance.mode_choice.setCurrentIndex(options.appearance.mode_choice.findData('rgb'))
            capture(options, f"appearance-{style}.png")
        options.findChild(QTabWidget).setCurrentIndex(1)
        capture(options, "options-wheel.png")
        options.findChild(QTabWidget).setCurrentIndex(2)
        capture(options, "columns.png")
        options.findChild(QTabWidget).setCurrentIndex(3)
        capture(options, "options-behavior.png")
        options.close()
        window.apply_appearance(dict(wheel_style='outline',wave_style='detailed',wave_mode='rgb'))
        window._set_key_filter('8A')
        capture(window,'key-filter-detailed.png')
        window._set_key_filter(None)
        for style in WHEEL_STYLES:
            window.apply_appearance(dict(wheel_style=style, wave_style='filled', wave_mode='rgb'))
            capture(window, f"workspace-{style}.png")
        window.apply_appearance(dict(wheel_style='accessible',wave_style='filled',wave_mode='bands',theme='light'))
        capture(window,'workspace-light.png')
        options=OptionsDialog(window.wheel,icon_path,window);options.show()
        capture(options,'appearance-light.png');options.close()
        window.apply_appearance(dict(wheel_style='classic', wave_style='classic', wave_mode='bands'))
        about = AboutDialog(QIcon(icon_path), icon_path, window)
        about.resize(680, 680)
        about.show()
        for index, filename in ((0, "about.png"), (1, "help.png"), (2, "donate.png")):
            about.findChild(QTabWidget).setCurrentIndex(index)
            capture(about, filename)
        about.close()
        message = MessageDialog(window, "Relink", "Matched 8 of 8 tracks.", StyledMessageBox.StandardButton.Ok)
        message.show(); capture(message, "message.png"); message.close()
        rename = RenameDialog(window, "Rename playlist", "Playlist name", "Peak Time")
        rename.show(); capture(rename, "rename.png"); rename.close()
        window.library[0].update(key='Unknown',bpm='Unknown',artist='Unknown Artist')
        window.library[1].update(time='Unknown')
        window._fill_library(window.library)
        window._on_set_selected()
        window._set_key_filter('8A')
        capture(window,'metadata-footer.png')
        window._set_key_filter(None)
        metadata=MetadataReviewDialog(window);metadata.show();capture(metadata,'metadata.png');metadata.close()
        render_galleries(app,output)
        print("Rendered current screenshots:", output)
    finally:
        if window is not None:
            window.player.stop(); window.player.setSource(QUrl()); window.close()
            sip.delete(window)
            app.processEvents()
        for attempt in range(10):
            try:
                shutil.rmtree(stage)
                break
            except PermissionError:
                if attempt == 9:
                    raise
                time.sleep(.1)


if __name__ == "__main__":
    main()
