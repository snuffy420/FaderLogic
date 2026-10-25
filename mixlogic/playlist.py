"""Playlist import (M3U8 + Rekordbox TXT), folder relinking and M3U8 export."""
import os
import re
import json
import codecs
from urllib.parse import urlsplit
from urllib.request import url2pathname

from .camelot import normalize_key

AUDIO_EXTENSIONS = (".wav", ".mp3", ".flac", ".m4a", ".aiff", ".aif")
MIXLOGIC_HEADER = "#MIXLOGIC-PLAYLIST:1"
MIXLOGIC_TRACK = "#MIXLOGIC-TRACK:"


def is_mixlogic_playlist(path):
    with open(path, "r", encoding="utf-8-sig", errors="replace") as source:
        return any(line.strip() == MIXLOGIC_HEADER for _, line in zip(range(8), source))


def _strip_leading_number(text):
    return re.sub(r"^\d+[\s\.\-_]*", "", text or "").strip().lower()


def read_text_file(path):
    """Read a Rekordbox export, which is usually UTF-16 but may be UTF-8."""
    with open(path, "rb") as fh:
        raw = fh.read()
    if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        return raw.decode("utf-16")
    if raw and raw.count(b"\0") > len(raw) // 8:
        encoding = "utf-16-le" if raw[1::2].count(b"\0") >= raw[0::2].count(b"\0") else "utf-16-be"
        return raw.decode(encoding)
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            text = raw.decode(encoding)
            if text.strip():
                return text
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="ignore")


def _local_track_path(value, playlist_dir):
    """Resolve playlist-relative paths and local file URLs to native absolute paths."""
    value = value.strip().strip('"')
    if value.lower().startswith("file:"):
        parts = urlsplit(value)
        value = url2pathname(parts.path)
        if parts.netloc and parts.netloc.lower() != "localhost":
            value = "//" + parts.netloc + "/" + value.lstrip("/\\")
    if not os.path.isabs(value):
        value = os.path.join(playlist_dir, value)
    return os.path.normpath(os.path.abspath(value))


def parse_m3u8(path):
    """Return a list of dicts with title, path, filename and duration (seconds)."""
    tracks = []
    playlist_dir = os.path.dirname(os.path.abspath(path))
    with open(path, "r", encoding="utf-8-sig", errors="replace") as fh:
        lines = fh.read().splitlines()
    pending_info = None
    pending_metadata = None
    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#EXTM3U"):
            continue
        if line.startswith("#EXTINF:"):
            pending_info = line[len("#EXTINF:"):]
            pending_metadata = None
        elif line.startswith(MIXLOGIC_TRACK):
            try:
                value = json.loads(line[len(MIXLOGIC_TRACK):])
                pending_metadata = value if isinstance(value, dict) else None
            except (ValueError, TypeError):
                pending_metadata = None
        elif not line.startswith("#"):
            track_path = _local_track_path(line, playlist_dir)
            duration, title = 0.0, ""
            if pending_info is not None:
                parts = pending_info.split(",", 1)
                try:
                    duration = float(parts[0])
                except ValueError:
                    duration = 0.0
                title = parts[1].strip() if len(parts) > 1 else ""
            tracks.append({
                "title": title,
                "path": track_path,
                "filename": os.path.basename(track_path),
                "duration": max(0.0, duration),
            })
            if pending_metadata is not None:
                tracks[-1]["mixlogic"] = pending_metadata
            pending_info = None
            pending_metadata = None
    return tracks


def parse_rekordbox_txt(path):
    """Parse a Rekordbox 'Export as text' file into a list of entries."""
    content = read_text_file(path)
    lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
    if not lines:
        return []

    headers = [h.strip().lower() for h in lines[0].split("\t")]

    def find_col(*names):
        return next((i for i, h in enumerate(headers) if h in names), None)

    key_idx = find_col("key", "tonality")
    bpm_idx = find_col("bpm", "tempo")
    title_idx = find_col("track title", "title", "name")
    artist_idx = find_col("artist", "performer")
    tab_delimited = any(i is not None for i in (key_idx, bpm_idx, title_idx))
    start = 1 if tab_delimited else 0

    entries = []
    for line in lines[start:]:
        cols = line.split("\t")
        key = bpm = title = artist = None
        if tab_delimited:
            if key_idx is not None and key_idx < len(cols):
                key = normalize_key(cols[key_idx])
            if bpm_idx is not None and bpm_idx < len(cols):
                try:
                    bpm = float(cols[bpm_idx].strip())
                except ValueError:
                    pass
            if title_idx is not None and title_idx < len(cols):
                title = cols[title_idx].strip()
            if artist_idx is not None and artist_idx < len(cols):
                artist = cols[artist_idx].strip()
        if not key:
            for col in cols:
                norm = normalize_key(col)
                if norm:
                    key = norm
                    break
        if not bpm:
            match = re.search(r"\b(\d{2,3}(?:\.\d{1,2})?)\s*(?:BPM)?\b", line, re.IGNORECASE)
            if match:
                bpm = float(match.group(1))
        entries.append({"raw": line.lower(), "title": title, "artist": artist, "key": key, "bpm": bpm})
    return entries


def _match_entry(track, entries, index):
    clean_title = _strip_leading_number(track["title"])
    clean_file = _strip_leading_number(os.path.splitext(track["filename"])[0])
    for entry in entries:
        t = (entry["title"] or "").strip().lower()
        if t and (t in clean_title or (clean_title and clean_title in t) or t in clean_file):
            return entry
        if clean_file and (clean_file in entry["raw"] or (clean_title and clean_title in entry["raw"])):
            return entry
    if index < len(entries):
        return entries[index]
    return None


def format_duration(seconds):
    seconds = int(round(seconds or 0))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def build_library(m3u8_path, txt_path):
    """Merge M3U8 entries with Rekordbox TXT metadata into library track dicts."""
    m3u8_tracks = parse_m3u8(m3u8_path)
    entries = parse_rekordbox_txt(txt_path) if txt_path else []
    library = []
    for index, track in enumerate(m3u8_tracks):
        entry = _match_entry(track, entries, index) or {}
        saved = track.get("mixlogic", {})
        if saved and not txt_path:
            library.append({
                "title": str(saved.get("title") or track["title"]),
                "artist": str(saved.get("artist") or "Unknown Artist"),
                "bpm": str(saved.get("bpm") or "120.0"),
                "key": normalize_key(saved.get("key")) or "8A",
                "duration": track["duration"],
                "time": str(saved.get("time") or format_duration(track["duration"])),
                "path": track["path"],
            })
            continue
        title = track["title"] or os.path.splitext(track["filename"])[0]
        bpm = entry.get("bpm")
        duration = track["duration"]
        library.append({
            "title": title,
            "artist": entry.get("artist") or "Unknown Artist",
            "bpm": f"{bpm:.1f}" if bpm else "120.0",
            "key": entry.get("key") or "8A",
            "duration": duration,
            "time": format_duration(duration) if duration > 0 else "03:30",
            "path": track["path"],
        })
    return library


def relink_tracks(tracks, folder):
    """Point each track at a matching audio file under folder. Returns the match count."""
    local = {}
    for root, _dirs, files in os.walk(folder):
        for name in files:
            if name.lower().endswith(AUDIO_EXTENSIONS):
                full = os.path.join(root, name)
                local.setdefault(name.lower(), full)
                local.setdefault(os.path.splitext(name)[0].lower(), full)

    matched = 0
    for track in tracks:
        filename = os.path.basename(track["path"]).lower()
        clean_title = _strip_leading_number(track["title"])
        found = local.get(filename) or local.get(clean_title)
        if not found and clean_title:
            found = next((p for k, p in local.items() if clean_title in k or k in clean_title), None)
        if found:
            track["path"] = found
            matched += 1
    return matched


def _export_duration(track):
    try:
        duration = float(track.get("duration") or 0)
        if 0 < duration < float("inf"):
            return int(round(duration))
    except (TypeError, ValueError, OverflowError):
        pass
    try:
        minutes, seconds = str(track["time"]).split(":")
        return max(0, int(minutes) * 60 + int(seconds))
    except (KeyError, ValueError):
        return -1  # Extended M3U's unknown-duration value.


def export_m3u8(path, tracks):
    """Export a UTF-8 Extended M3U playlist for Rekordbox's Import Playlist command.

    Keep the set order (including duplicates) and use native absolute file paths,
    so saving the playlist in another directory does not break its references.
    """
    entries = []
    missing = []
    for track in tracks:
        raw_path = str(track.get("path") or "")
        if not raw_path or any(char in raw_path for char in "\r\n\0"):
            raise ValueError("A track has an empty or invalid audio file path. Use Relink Folder before exporting.")
        track_path = _local_track_path(raw_path, os.getcwd())
        if not os.path.isfile(track_path):
            missing.append(track_path)
        # Metadata stays on a single EXTINF line, even if an imported tag has a newline.
        title = " ".join(str(track.get("title") or "").splitlines())
        artist = " ".join(str(track.get("artist") or "").splitlines())
        display = f"{artist} - {title}" if artist else title
        metadata = {key: str(track[key]) for key in ("bpm", "key", "time") if key in track}
        metadata.update(title=title, artist=artist)
        entries.append((_export_duration(track), display, track_path, metadata))
    if missing:
        examples = "\n".join(missing[:5])
        raise ValueError(f"{len(missing)} audio file(s) could not be found. Use Relink Folder before exporting.\n\n{examples}")
    with open(path, "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write("#EXTM3U\n")
        fh.write(MIXLOGIC_HEADER + "\n")
        for seconds, display, track_path, metadata in entries:
            fh.write(f"#EXTINF:{seconds},{display}\n")
            # Optional M3U comment: regular playlist readers ignore this; MixLogic
            # uses it to recover editing metadata without an extra TXT export.
            fh.write(MIXLOGIC_TRACK + json.dumps(metadata, ensure_ascii=False) + "\n")
            fh.write(track_path + "\n")
