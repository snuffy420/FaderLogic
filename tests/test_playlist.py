"""Rekordbox-targeted M3U8 output: order, paths, Unicode, duration and missing files."""
import unittest
from pathlib import Path

from mixlogic.playlist import build_library, export_m3u8, is_mixlogic_playlist, parse_m3u8, parse_rekordbox_txt


class PlaylistExportTests(unittest.TestCase):
    def setUp(self):
        # Use ordinary directory permissions for the test's temporary audio files.
        from uuid import uuid4
        self.root = Path("build") / ("playlist-test-" + uuid4().hex)
        self.root.mkdir(parents=True)
        self.addCleanup(self._cleanup)
        self.audio = self.root / "Music"
        self.audio.mkdir()
        self.first = self.audio / "Beyoncé - Déjà Vu #1.mp3"
        self.second = self.audio / "日本語, edit.wav"
        self.first.touch()
        self.second.touch()

    def _cleanup(self):
        import shutil
        shutil.rmtree(self.root)

    def test_utf8_absolute_paths_set_order_and_duplicates(self):
        target = self.root / "My Set.m3u8"
        tracks = [dict(path=str(self.second), title="夜, Mix", artist="DJ", time="06:12"),
                  dict(path=str(self.first), title="Déjà\nVu", artist="Beyoncé", duration=241.4),
                  dict(path=str(self.second), title="夜, Mix", artist="DJ", time="06:12")]
        export_m3u8(target, tracks)
        raw = target.read_bytes()
        self.assertTrue(raw.startswith(b"#EXTM3U\r\n"))
        text = raw.decode("utf-8")
        self.assertIn("#EXTINF:372,DJ - 夜, Mix\r\n", text)
        self.assertIn("#EXTINF:241,Beyoncé - Déjà Vu\r\n", text)
        paths = [line for line in text.splitlines() if not line.startswith("#")]
        self.assertEqual(paths, [str(self.second.resolve()), str(self.first.resolve()), str(self.second.resolve())])
        self.assertEqual([t["path"] for t in parse_m3u8(target)], paths)

    def test_import_relative_paths_and_bom_before_export_elsewhere(self):
        source = self.root / "source.m3u8"
        source.write_text("#EXTM3U\n#EXTINF:300,Example\nMusic/" + self.first.name + "\n", encoding="utf-8-sig")
        imported = parse_m3u8(source)
        self.assertEqual(imported[0]["path"], str(self.first.resolve()))
        destination = self.root / "Elsewhere"
        destination.mkdir()
        export_m3u8(destination / "output.m3u8", imported)
        self.assertEqual(parse_m3u8(destination / "output.m3u8")[0]["path"], str(self.first.resolve()))

    def test_file_url_percent_encoding(self):
        source = self.root / "url.m3u8"
        source.write_text("#EXTM3U\n" + self.first.resolve().as_uri() + "\n", encoding="utf-8")
        self.assertEqual(parse_m3u8(source)[0]["path"], str(self.first.resolve()))

    def test_missing_audio_does_not_overwrite_existing_playlist(self):
        target = self.root / "existing.m3u8"
        target.write_text("keep this playlist", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Relink Folder"):
            export_m3u8(target, [dict(path=str(self.root / "missing.mp3"))])
        self.assertEqual(target.read_text(), "keep this playlist")

    def test_unknown_duration_and_invalid_path(self):
        target = self.root / "unknown.m3u8"
        export_m3u8(target, [dict(path=str(self.first), title="Unknown", duration=float("nan"))])
        self.assertIn("#EXTINF:-1,Unknown", target.read_text(encoding="utf-8"))
        for path in ("", "a\nb.mp3", "a\0b.mp3"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                export_m3u8(target, [dict(path=path)])

    def test_export_reopens_metadata_and_exact_order_without_txt(self):
        target = self.root / "Editable Set.m3u8"
        one = dict(path=str(self.first.resolve()), title="Déjà Vu", artist="Beyoncé", bpm="127.5", key="9A", time="05:30", duration=330)
        two = dict(path=str(self.second.resolve()), title="夜, Mix", artist="DJ", bpm="132.0", key="10B", time="06:00", duration=360)
        original = [two, one, dict(two)]
        export_m3u8(target, original)
        self.assertTrue(is_mixlogic_playlist(target))
        restored = build_library(target, None)
        self.assertEqual([{key: track[key] for key in original[index]} for index, track in enumerate(restored)], original)
        self.assertTrue(all(track["metadata_checked"] and not track["metadata_issues"] for track in restored))

    def test_rekordbox_text_reads_utf16_and_utf8_without_confusing_them(self):
        text = "Track Title\tArtist\tBPM\tKey\nDéjà Vu\tBeyoncé\t127.5\t9A\n"
        for encoding in ("utf-16", "utf-16-le", "utf-16-be", "utf-8", "utf-8-sig"):
            path = self.root / (encoding + ".txt")
            path.write_text(text, encoding=encoding)
            with self.subTest(encoding=encoding):
                entry = parse_rekordbox_txt(path)[0]
                self.assertEqual(entry["artist"], "Beyoncé")
                self.assertEqual(entry["key"], "9A")
                self.assertEqual(entry["bpm"], 127.5)


if __name__ == "__main__":
    unittest.main()
