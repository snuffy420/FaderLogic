"""Render the real 1.3.0 GUI using generated audio and example Rekordbox metadata."""
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
from mixlogic import __version__, camelot, playlist
from mixlogic.dialogs import AboutDialog, OptionsDialog, MessageDialog, RenameDialog, StyledMessageBox
from mixlogic.main_window import MainWindow
from mixlogic.theme import STYLESHEET
from mixlogic.waveform import compute_bands


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
    icon_path = str(ROOT / "assets/mixlogic.ico")
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
            tracks.append(dict(title=title + " (Demo)", artist="MixLogic Demo", bpm=f"{124 + index}.0",
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
        window.linked_folder = r"C:\Music\MixLogic Demo"
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
        options = OptionsDialog(window.wheel, icon_path, window)
        options.show()
        capture(options, "options-wheel.png")
        options.findChild(QTabWidget).setCurrentIndex(1)
        capture(options, "columns.png")
        options.close()
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
