"""Unknown metadata must never become a guessed key, tempo or transition."""
import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

from mixlogic import playlist, camelot
from mixlogic.storage import LibraryStore
from mixlogic.paths import runtime_data_dir


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.root = Path("build") / ("metadata-test-" + uuid4().hex)
        self.root.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.root)
        self.m3u = self.root / "source.m3u8"
        self.txt = self.root / "source.txt"

    def library(self, title, rows, duration=60):
        self.m3u.write_text(f"#EXTM3U\n#EXTINF:{duration},{title}\naudio.wav\n", encoding="utf-8")
        self.txt.write_text("Track Title\tArtist\tBPM\tKey\n" + rows, encoding="utf-16")
        return playlist.build_library(self.m3u, self.txt)

    def test_missing_fields_do_not_read_numbers_or_keys_from_title(self):
        track = self.library("8A 120 Nights", "8A 120 Nights\tArtist\t\t\n")[0]
        self.assertEqual(track["key"], "Unknown")
        self.assertEqual(track["bpm"], "Unknown")
        self.assertTrue(playlist.metadata_issues(track))

    def test_unmatched_and_ambiguous_rows_are_not_positionally_assigned(self):
        for rows in ("Other Track\tArtist\t128\t9A\n", "Target Extended\tArtist\t128\t9A\n",
                     "Target\tArtist\t128\t9A\nTarget\tArtist\t130\t10A\n"):
            with self.subTest(rows=rows):
                track = self.library("Target", rows)[0]
                self.assertEqual((track["key"], track["bpm"]), ("Unknown", "Unknown"))

    def test_actual_8a_120_metadata_is_retained(self):
        track = self.library("Target", "Target\tArtist\t120\t8A\n")[0]
        self.assertEqual((track["key"], track["bpm"]), ("8A", "120.0"))
        self.assertFalse(playlist.metadata_issues(track))

    def test_invalid_key_and_nonfinite_bpm_are_unknown(self):
        for bpm in ("nan", "inf", "-2", "0", "not known"):
            with self.subTest(bpm=bpm):
                track = self.library("Target", f"Target\tArtist\t{bpm}\t99Z\n")[0]
                self.assertEqual((track["key"], track["bpm"]), ("Unknown", "Unknown"))

    def test_unknown_keys_never_produce_compatibility_or_default_sort_key(self):
        for key in (None, "", "Unknown", "bad key"):
            self.assertEqual(camelot.get_compatibility(key, "8A")[0], "unknown")
            self.assertEqual(camelot.get_compatibility("8A", key)[0], "unknown")
            self.assertNotEqual(camelot.camelot_sort_key(key), camelot.camelot_sort_key("8A"))

    def test_unknown_fields_survive_export_reimport(self):
        track = self.library("Target", "Target\tArtist\t\t\n")[0]
        Path(track["path"]).touch()
        output = self.root / "set.m3u8"
        playlist.export_m3u8(output, [track])
        restored = playlist.build_library(output, None)[0]
        self.assertEqual((restored["key"], restored["bpm"]), ("Unknown", "Unknown"))
        self.assertTrue(restored["metadata_issues"])

    def test_legacy_saved_defaults_rechecked_against_copied_txt(self):
        self.library("Target", "Target\tArtist\t128\t9A\n")
        legacy = dict(title="Target", artist="Artist", key="8A", bpm="120.0", time="03:30",
                      duration=0, path=str((self.root / "audio.wav").resolve()))
        store = LibraryStore(self.root / "data")
        try:
            identity = store.add_playlist(self.m3u, self.txt, [legacy])
            store.save_session({"active_playlist_id": identity, "active_set": [legacy, dict(legacy)]})
            self.m3u.unlink(); self.txt.unlink()
            checked = store.get_playlist(identity)["tracks"][0]
            self.assertEqual((checked["key"], checked["bpm"]), ("9A", "128.0"))
            self.assertEqual(checked["time"], "01:00")
            session = store.load_session()["active_set"]
            self.assertEqual([track["key"] for track in session], ["9A", "9A"])
        finally:
            store.close()

    def test_legacy_without_verification_sources_is_unknown(self):
        self.library("Target", "Different\tArtist\t128\t9A\n")
        legacy = dict(title="Target", artist="Artist", key="8A", bpm="120.0", time="03:30", duration=0,
                      path=str((self.root / "audio.wav").resolve()))
        store = LibraryStore(self.root / "data")
        try:
            identity = store.add_playlist(self.m3u, self.txt, [legacy])
            track = store.get_playlist(identity)["tracks"][0]
            self.assertEqual((track["key"], track["bpm"]), ("Unknown", "Unknown"))
        finally:
            store.close()

    def test_unknown_duration_is_not_three_minutes_thirty(self):
        track = self.library("Target", "Target\tArtist\t128\t9A\n", duration=-1)[0]
        self.assertEqual(track["time"], "Unknown")
        self.assertIsNone(playlist.time_seconds(track["time"]))

    def test_windows_filename_and_foreign_path_can_be_relinked_on_unix(self):
        self.assertEqual(playlist.track_filename(r"D:\Music\Track.wav"), "Track.wav")
        with patch("mixlogic.playlist.os.name", "posix"):
            self.assertEqual(playlist._local_track_path(r"D:\Music\Track.wav", "/tmp"), "D:/Music/Track.wav")

    def test_installed_data_uses_user_directory_portable_stays_local(self):
        app = self.root / "Program Files" / "MixLogic"
        app.mkdir(parents=True)
        executable = app / "MixLogic.exe"
        self.assertEqual(runtime_data_dir(executable, True), str(app.resolve()))
        (app / "installed.flag").touch()
        with patch.dict("os.environ", {"LOCALAPPDATA": str(self.root.resolve() / "user-data")}):
            location = runtime_data_dir(executable, True)
            self.assertEqual(Path(location), self.root.resolve() / "user-data" / "MixLogic")
        self.assertFalse((app / "MixLogic-data").exists())
