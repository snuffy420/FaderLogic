"""3-band waveform extraction (Qt audio decoding) and a persistent SQLite cache."""
import json
import os
import sqlite3
import struct
import math
import cmath
from array import array
import sys

from PyQt6.QtCore import QEventLoop, QObject, QThread, QTimer, QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioDecoder, QAudioFormat

NUM_BARS = 256
FLAT = []
SPECTRUM_BINS = 24
FFT_SIZE = 1024
FREQUENCY_EDGES = [40 * (10000 / 40) ** (i / SPECTRUM_BINS) for i in range(SPECTRUM_BINS + 1)]
_WINDOW = [.5 - .5 * math.cos(2 * math.pi * i / (FFT_SIZE - 1)) for i in range(FFT_SIZE)]
_REVERSE = [int(f"{i:010b}"[::-1], 2) for i in range(FFT_SIZE)]
_TWIDDLES = {n: [cmath.exp(-2j * math.pi * k / n) for k in range(n // 2)]
             for n in (2, 4, 8, 16, 32, 64, 128, 256, 512, 1024)}


def spectrum_features(samples):
    """Hann-windowed FFT: 3 measured bands, 24 log-frequency bins and peak."""
    padded = list(samples[:FFT_SIZE]) + [0] * max(0, FFT_SIZE - len(samples))
    values = [complex(padded[i] / 32768 * _WINDOW[i], 0) for i in _REVERSE]
    size = 2
    while size <= FFT_SIZE:
        half = size // 2
        for start in range(0, FFT_SIZE, size):
            for k, twiddle in enumerate(_TWIDDLES[size]):
                even = values[start + k]
                odd = values[start + k + half] * twiddle
                values[start + k], values[start + k + half] = even + odd, even - odd
        size *= 2
    power = [abs(value) ** 2 for value in values[:FFT_SIZE // 2]]
    def energy(low, high):
        a = max(1, int(low * FFT_SIZE / 22050))
        b = max(a + 1, min(len(power), int(high * FFT_SIZE / 22050)))
        return min(1., math.sqrt(sum(power[a:b])) / FFT_SIZE * 5)
    bands = [energy(20, 250), energy(250, 2500), energy(2500, 11025)]
    spectrum = [min(1., math.log1p(energy(low, high) * 30) / math.log(31))
                for low, high in zip(FREQUENCY_EDGES, FREQUENCY_EDGES[1:])]
    return tuple(bands + spectrum + [max(abs(s) for s in padded) / 32768])


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
    cancel = QTimer()
    cancel.setInterval(100)
    def check_cancel():
        if QThread.currentThread().isInterruptionRequested():
            decoder.stop(); loop.quit()
    cancel.timeout.connect(check_cancel)
    timeout = QTimer()
    timeout.setSingleShot(True)
    timeout.timeout.connect(lambda: (decoder.stop(), loop.quit()))
    cancel.start(); timeout.start(60000)
    decoder.start()
    loop.exec()
    cancel.stop(); timeout.stop()
    cancel.timeout.disconnect(); timeout.timeout.disconnect()
    decoder.stop()
    decoder.setSource(QUrl())
    # Release the backend before this worker's event loop goes away (Windows
    # otherwise can retain the source file until a later deferred deletion).
    from PyQt6 import sip
    sip.delete(decoder)
    return bytes(pcm)


def compute_bands(file_path, num_bars=NUM_BARS):
    """Return measured band amplitudes, spectral bins and peak for each time slot."""
    if not file_path or not os.path.exists(file_path):
        return list(FLAT)
    pcm = decode_pcm(file_path)
    count = len(pcm) // 2
    if count == 0:
        return list(FLAT)
    samples = array("h")
    samples.frombytes(pcm[:count*2])
    if sys.byteorder != "little": samples.byteswap()
    return analyze_samples(samples,num_bars)


def analyze_samples(samples, num_bars=NUM_BARS):
    """The shared overview analyzer for decoded tracks and bundled examples."""
    count=len(samples)
    if not count:return []
    bars = []
    for i in range(num_bars):
        if QThread.currentThread().isInterruptionRequested():
            return []
        start, end = i * count // num_bars, (i + 1) * count // num_bars
        # Several windows capture activity across the slot instead of one sample.
        windows = []
        for fraction in (.15, .5, .85):
            center = int(start + (end - start) * fraction)
            offset = max(0, center - FFT_SIZE // 2)
            windows.append(spectrum_features(samples[offset:offset + FFT_SIZE]))
        values = [max(feature[j] for feature in windows) for j in range(3 + SPECTRUM_BINS + 1)]
        # Fine signed envelope from every PCM sample, without extra FFT work.
        # Sixteen bins per overview slot produce 4096 real transient columns.
        detail = []
        for j in range(16):
            a = start + (end-start)*j//16
            b = start + (end-start)*(j+1)//16
            chunk = samples[a:max(a+1,b)]
            detail.append((min(chunk, default=0)/32768, max(chunk, default=0)/32768))
        values[27] = max(max(abs(low),abs(high)) for low,high in detail)
        bars.append(tuple(values + [detail]))
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
            "CREATE TABLE IF NOT EXISTS waveforms_v3 "
            "(file_path TEXT PRIMARY KEY, mtime REAL, amplitudes TEXT)"
        )
        self.conn.commit()

    def get(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return None
        try:
            mtime = os.path.getmtime(file_path)
            row = self.conn.execute(
                "SELECT mtime, amplitudes FROM waveforms_v3 WHERE file_path = ?", (file_path,)
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
                "INSERT OR REPLACE INTO waveforms_v3 (file_path, mtime, amplitudes) VALUES (?, ?, ?)",
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
