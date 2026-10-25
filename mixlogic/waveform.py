"""3-band waveform extraction (Qt audio decoding) and a persistent SQLite cache."""
import json
import os
import sqlite3
import struct

from PyQt6.QtCore import QEventLoop, QObject, QThread, QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioDecoder, QAudioFormat

NUM_BARS = 140
FLAT = [(0.12, 0.12, 0.12)] * NUM_BARS


def decode_pcm(file_path):
    """Decode a file to 22050 Hz mono signed 16-bit samples using Qt's decoder."""
    decoder = QAudioDecoder()
    decoder.setSource(QUrl.fromLocalFile(file_path))
    fmt = QAudioFormat()
    fmt.setSampleRate(22050)
    fmt.setChannelCount(1)
    fmt.setSampleFormat(QAudioFormat.SampleFormat.Int16)
    decoder.setAudioFormat(fmt)

    pcm = bytearray()
    loop = QEventLoop()

    def on_buffer():
        buf = decoder.read()
        if buf.isValid() and buf.constData():
            pcm.extend(buf.constData())

    decoder.bufferReady.connect(on_buffer)
    decoder.finished.connect(loop.quit)
    decoder.error.connect(lambda *_: loop.quit())
    decoder.start()
    loop.exec()
    return bytes(pcm)


def compute_bands(file_path, num_bars=NUM_BARS):
    """Return num_bars (low, mid, high) tuples in 0..1 for drawing."""
    if not file_path or not os.path.exists(file_path):
        return list(FLAT)
    pcm = decode_pcm(file_path)
    count = len(pcm) // 2
    if count == 0:
        return list(FLAT)
    samples = struct.unpack(f"<{count}h", pcm[: count * 2])
    chunk = max(1, count // num_bars)
    bars = []
    for i in range(num_bars):
        part = samples[i * chunk:(i + 1) * chunk]
        if not part:
            bars.append((0.1, 0.1, 0.1))
            continue
        low = min(1.0, max(abs(s) for s in part) / 32768.0)
        diff = max((abs(part[j] - part[j - 1]) for j in range(1, len(part))), default=0)
        high = min(1.0, diff / 32768.0)
        mid = min(1.0, (low + high) / 2.0 * 0.85)
        bars.append((max(0.12, low), max(0.12, mid), max(0.12, high)))
    return bars


class WaveformWorker(QThread):
    """Computes a waveform off the GUI thread."""
    computed = pyqtSignal(str, list)

    def __init__(self, file_path, parent=None):
        super().__init__(parent)
        self.file_path = file_path

    def run(self):
        try:
            bars = compute_bands(self.file_path)
        except Exception:
            bars = list(FLAT)
        self.computed.emit(self.file_path, bars)


class WaveformCache:
    """Stores waveforms in waveform_cache.db next to the app, keyed by path and mtime."""

    def __init__(self, db_path):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS waveforms "
            "(file_path TEXT PRIMARY KEY, mtime REAL, amplitudes TEXT)"
        )
        self.conn.commit()

    def get(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return None
        try:
            mtime = os.path.getmtime(file_path)
            row = self.conn.execute(
                "SELECT mtime, amplitudes FROM waveforms WHERE file_path = ?", (file_path,)
            ).fetchone()
            if row and abs(row[0] - mtime) < 1.0:
                return [tuple(bar) for bar in json.loads(row[1])]
        except Exception:
            pass
        return None

    def put(self, file_path, bars):
        if not file_path or not os.path.exists(file_path):
            return
        try:
            self.conn.execute(
                "INSERT OR REPLACE INTO waveforms (file_path, mtime, amplitudes) VALUES (?, ?, ?)",
                (file_path, os.path.getmtime(file_path), json.dumps(bars)),
            )
            self.conn.commit()
        except Exception:
            pass

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass
