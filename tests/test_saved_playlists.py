"""Import once, switch without source exports, and restore playlists/preferences/set order."""
import os
import json
import shutil
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QFontDatabase, QIcon
from PyQt6.QtWidgets import QApplication, QLabel, QPushButton, QTabWidget
from PyQt6.QtTest import QTest

from faderlogic import camelot
from faderlogic.main_window import MainWindow
from faderlogic.storage import LibraryStore
from faderlogic.theme import STYLESHEET
from faderlogic.dialogs import AboutDialog, BTC_ADDRESS, MessageDialog, OptionsDialog, RenameDialog, StyledMessageBox
from faderlogic.titlebar import TitleBar
from faderlogic import playlist


class SavedPlaylistTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        for name in ("segoeui.ttf", "segoeuib.ttf"):
            path = Path("C:/Windows/Fonts") / name
            if path.exists():
                QFontDatabase.addApplicationFont(str(path))
        cls.app.setStyleSheet(STYLESHEET)

    def setUp(self):
        self.root = Path("build") / ("browser-test-" + uuid4().hex)
        self.root.mkdir(parents=True)
        self.windows = []
        self.cache_patch = patch("faderlogic.main_window.WaveformCache")
        self.cache_patch.start()
        camelot.set_active_chart(next(iter(camelot.CHART_CHOICES)))
        self.window = self.new_window()

    def tearDown(self):
        for window in self.windows:
            window.close()
        self.cache_patch.stop()
        shutil.rmtree(self.root)
        camelot.set_active_chart(next(iter(camelot.CHART_CHOICES)))

    def new_window(self):
        window = MainWindow(str(self.root), str(Path("assets/faderlogic.ico").resolve()))
        self.windows.append(window)
        window.show()
        self.app.processEvents()
        return window

    def close_window(self, window):
        window.close()
        self.windows.remove(window)

    def import_fixture(self, name, title="Déjà Vu", key="9A", bpm="127.5"):
        source = self.root / (name + ".m3u8")
        metadata = self.root / (name + ".txt")
        source.write_text(f"#EXTM3U\n#EXTINF:333,{title}\nMusic/{name}.mp3\n", encoding="utf-8")
        metadata.write_text(f"Track Title\tArtist\tBPM\tKey\n{title}\tBeyoncé\t{bpm}\t{key}\n", encoding="utf-16")
        with patch("faderlogic.main_window.QFileDialog.getOpenFileName", side_effect=[(str(source), ""), (str(metadata), "")]):
            self.window.import_playlist()
        return self.window.active_playlist_id, source, metadata

    def test_sources_saved_and_last_playlist_preferences_and_set_restore(self):
        first_id, first_source, first_txt = self.import_fixture("Warmup", "First", "8A")
        first_track = dict(self.window.library[0])
        second_id, source, metadata = self.import_fixture("Peak Time", "Second", "10B", "132.0")
        second_track = dict(self.window.library[0])
        copied = self.root / "FaderLogic-data" / "sources" / second_id
        self.assertEqual((copied / "playlist.m3u8").read_bytes(), source.read_bytes())
        self.assertEqual((copied / "metadata.txt").read_bytes(), metadata.read_bytes())
        self.window.active_set = [second_track, first_track, dict(second_track)]
        self.window._fill_set()
        camelot.set_active_chart(list(camelot.CHART_CHOICES)[1])
        self.window.wheel.set_label_mode("both")
        self.window.wheel.set_show_all(True)
        self.window.overlap.setValue(30)
        source.unlink()
        metadata.unlink()
        first_source.unlink()
        first_txt.unlink()
        self.close_window(self.window)
        with patch("faderlogic.main_window.QFileDialog.getOpenFileName") as file_picker:
            restored = self.new_window()
            file_picker.assert_not_called()
        self.assertEqual(restored.active_playlist_id, second_id)
        self.assertEqual(restored.library[0]["key"], "10B")
        self.assertEqual(restored.library[0]["artist"], "Beyoncé")
        self.assertEqual(restored.library[0]["bpm"], "132.0")
        self.assertEqual([t["path"] for t in restored.active_set], [second_track["path"], first_track["path"], second_track["path"]])
        self.assertEqual(restored.wheel.label_mode, "both")
        self.assertTrue(restored.wheel.show_all)
        self.assertEqual(restored.overlap.value(), 30)
        self.assertEqual(camelot.active_chart_name, list(camelot.CHART_CHOICES)[1])
        self.assertTrue(restored.btn_playlists.isChecked())
        restored._activate_playlist(first_id)
        self.assertEqual(restored.library[0]["title"], "First")
        self.assertEqual(len(restored.active_set), 3)

    def test_browser_switch_search_and_remove_keep_set(self):
        first_id, _, _ = self.import_fixture("Chill", "Calm", "8A")
        first_track = dict(self.window.library[0])
        second_id, _, _ = self.import_fixture("Dance", "Move", "9A")
        self.window.active_set = [first_track]
        browser = self.window.playlist_browser
        for row in range(browser.list.count()):
            item = browser.list.item(row)
            if item.data(Qt.ItemDataRole.UserRole) == first_id:
                browser.list.setCurrentItem(item)
                break
        self.assertEqual(self.window.active_playlist_id, first_id)
        self.assertEqual(self.window.library[0]["title"], "Calm")
        self.assertEqual(len(self.window.active_set), 1)
        browser.search.setText("nothing matches")
        self.assertTrue(all(browser.list.item(row).isHidden() for row in range(browser.list.count())))
        self.assertFalse(browser.remove_button.isEnabled())
        browser.search.clear()
        self.window._remove_playlist(first_id)
        self.assertEqual(self.window.active_playlist_id, second_id)
        self.window._remove_playlist(second_id)
        self.assertEqual(self.window.library, [])
        self.assertEqual(len(self.window.active_set), 1)
        self.close_window(self.window)
        restored = self.new_window()
        self.assertIsNone(restored.active_playlist_id)
        self.assertEqual(restored.lib_table.rowCount(), 0)
        self.assertEqual(len(restored.active_set), 1)

    def test_top_button_hides_and_shows_browser_and_restores_hidden_preference(self):
        self.assertFalse(self.window.playlist_browser.isVisible())
        QTest.mouseClick(self.window.btn_playlists, Qt.MouseButton.LeftButton)
        self.app.processEvents()
        self.assertTrue(self.window.playlist_browser.isVisible())
        QTest.mouseClick(self.window.btn_playlists, Qt.MouseButton.LeftButton)
        self.app.processEvents()
        self.assertFalse(self.window.playlist_browser.isVisible())
        self.close_window(self.window)
        restored = self.new_window()
        self.assertFalse(restored.playlist_browser.isVisible())
        QTest.mouseClick(restored.btn_playlists, Qt.MouseButton.LeftButton)
        self.app.processEvents()
        self.assertTrue(restored.playlist_browser.isVisible())

    def test_reimport_updates_entry_and_keeps_rename(self):
        playlist_id, _, _ = self.import_fixture("Peak Time", key="8A")
        with patch("faderlogic.main_window.QInputDialog.getText", return_value=("Friday Night", True)):
            self.window._rename_playlist(playlist_id)
        updated_id, _, _ = self.import_fixture("Peak Time", key="11B", bpm="135.0")
        self.assertEqual(playlist_id, updated_id)
        self.assertEqual(len(self.window.store.list_playlists()), 1)
        self.assertEqual(self.window.active_playlist_name, "Friday Night")
        self.close_window(self.window)
        restored = self.new_window()
        self.assertEqual(restored.active_playlist_name, "Friday Night")
        self.assertEqual(restored.library[0]["key"], "11B")
        self.assertEqual(restored.library[0]["bpm"], "135.0")

    def test_cancel_or_failed_import_keeps_current_playlist(self):
        playlist_id, source, _ = self.import_fixture("Existing")
        with patch("faderlogic.main_window.QFileDialog.getOpenFileName", side_effect=[(str(source), ""), ("", "")]):
            self.window.import_playlist()
        self.assertEqual(self.window.active_playlist_id, playlist_id)
        with patch("faderlogic.main_window.QFileDialog.getOpenFileName", return_value=("missing", "")), \
             patch("faderlogic.main_window.QMessageBox.critical") as error:
            self.window.import_playlist()
            error.assert_called_once()
        self.assertEqual(self.window.active_playlist_id, playlist_id)
        self.assertEqual(len(self.window.store.list_playlists()), 1)

    def test_relinked_library_paths_survive_restart(self):
        playlist_id, _, _ = self.import_fixture("Relink")
        with patch("faderlogic.main_window.QFileDialog.getExistingDirectory", return_value="new music"), \
             patch("faderlogic.main_window.playlist.relink_tracks") as relink, \
             patch("faderlogic.main_window.QMessageBox.information"):
            def update(tracks, _folder):
                tracks[0]["path"] = "relocated/Relink.mp3"
                return 1
            relink.side_effect = update
            self.window.relink_folder()
        self.close_window(self.window)
        restored = self.new_window()
        self.assertEqual(restored.active_playlist_id, playlist_id)
        self.assertEqual(restored.library[0]["path"], "relocated/Relink.mp3")
        self.assertEqual(restored.linked_folder, os.path.abspath("new music"))

    def test_each_playlist_remembers_folder_and_reimport_reuses_it(self):
        with patch.object(MainWindow, "_load_waveform"), \
             patch("faderlogic.main_window.QMessageBox.information"):
            first_id, _, _ = self.import_fixture("First", key="8A")
            original = dict(self.window.library[0])
            self.window.active_set = [dict(original), dict(original)]
            folder_a = (self.root / "Music A").resolve()
            folder_a.mkdir()
            audio_a = folder_a / "First.mp3"
            audio_a.touch()
            with patch("faderlogic.main_window.QFileDialog.getExistingDirectory", return_value=str(folder_a)):
                self.window.relink_folder()
            self.assertEqual([t["path"] for t in self.window.active_set], [str(audio_a), str(audio_a)])
            second_id, _, _ = self.import_fixture("Second", key="10B")
            self.assertIsNone(self.window.linked_folder)
            folder_b = (self.root / "Music B").resolve()
            folder_b.mkdir()
            (folder_b / "Second.mp3").touch()
            with patch("faderlogic.main_window.QFileDialog.getExistingDirectory", return_value=str(folder_b)):
                self.window.relink_folder()
            self.close_window(self.window)
            self.window = self.new_window()
            self.assertEqual(self.window.active_playlist_id, second_id)
            self.assertEqual(self.window.linked_folder, str(folder_b))
            self.window._activate_playlist(first_id)
            self.assertEqual(self.window.linked_folder, str(folder_a))
            self.assertEqual(self.window.library[0]["path"], str(audio_a))
            with patch("faderlogic.main_window.QFileDialog.getExistingDirectory", return_value="") as picker:
                self.window.relink_folder()
                self.assertEqual(picker.call_args.args[2], str(folder_a))
            self.assertEqual(self.window.linked_folder, str(folder_a))
            self.import_fixture("First", key="9A", bpm="133.0")
            self.assertEqual(self.window.library[0]["path"], str(audio_a))
            self.assertEqual(self.window.library[0]["key"], "9A")
            self.assertEqual(self.window.linked_folder, str(folder_a))
            self.assertEqual(self.window.playlist_browser.linked_folder_label.toolTip(), str(folder_a))

    def test_previous_database_upgrades_without_losing_playlists_or_session(self):
        legacy = self.root / "legacy"
        legacy.mkdir()
        connection = sqlite3.connect(legacy / "library.sqlite3")
        connection.executescript("""
            CREATE TABLE playlists (id TEXT PRIMARY KEY, name TEXT NOT NULL,
                source_m3u8 TEXT NOT NULL, source_txt TEXT NOT NULL,
                tracks TEXT NOT NULL, imported_at TEXT NOT NULL,
                UNIQUE(source_m3u8, source_txt));
            CREATE TABLE state (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)
        connection.execute("INSERT INTO playlists VALUES (?, ?, ?, ?, ?, ?)",
                           ("old", "Existing library", "source.m3u8", "source.txt", "[]", "2026-10-25"))
        connection.execute("INSERT INTO state VALUES ('session', ?)",
                           (json.dumps({"active_playlist_id": "old", "overlap": 30}),))
        connection.commit()
        connection.close()
        store = LibraryStore(legacy)
        try:
            self.assertEqual(store.get_playlist("old")["name"], "Existing library")
            self.assertIsNone(store.get_playlist("old")["linked_folder"])
            self.assertEqual(store.load_session()["overlap"], 30)
            store.update_tracks("old", [], "saved music folder")
            self.assertEqual(store.get_playlist("old")["linked_folder"], "saved music folder")
        finally:
            store.close()

    def test_table_column_drag_and_panel_heights_restore(self):
        self.assertFalse(hasattr(self.window, "btn_open_set"))
        header = self.window.lib_table.horizontalHeader()
        from PyQt6.QtWidgets import QHeaderView
        self.assertEqual(header.sectionResizeMode(0), QHeaderView.ResizeMode.Interactive)
        self.assertEqual(header.sectionResizeMode(1), QHeaderView.ResizeMode.Interactive)
        start = header.sectionSize(0)
        boundary = header.sectionViewportPosition(0) + start - 1
        QTest.mousePress(header.viewport(), Qt.MouseButton.LeftButton, pos=QPoint(boundary, 12))
        QTest.mouseMove(header.viewport(), QPoint(boundary + 55, 12), delay=20)
        QTest.mouseRelease(header.viewport(), Qt.MouseButton.LeftButton, pos=QPoint(boundary + 55, 12))
        self.app.processEvents()
        self.assertGreater(header.sectionSize(0), start + 30)
        chosen_width = header.sectionSize(0)
        self.window.set_table.horizontalHeader().resizeSection(2, 190)
        self.window.table_splitter.moveSplitter(self.window.table_splitter.sizes()[0] + 65, 1)
        ratio = self.window.table_splitter.sizes()[0] / sum(self.window.table_splitter.sizes())
        self.close_window(self.window)
        restored = self.new_window()
        self.assertEqual(restored.lib_table.columnWidth(0), chosen_width)
        self.assertEqual(restored.set_table.columnWidth(2), 190)
        restored_ratio = restored.table_splitter.sizes()[0] / sum(restored.table_splitter.sizes())
        self.assertAlmostEqual(restored_ratio, ratio, delta=0.02)

    def test_column_options_persist_and_keep_one_column_visible(self):
        options = OptionsDialog(self.window.wheel, self.window._icon_path, self.window)
        options.column_checks[("library", "Artist")].setChecked(False)
        options.column_checks[("set", "Artist")].setChecked(False)
        self.assertTrue(self.window.lib_table.isColumnHidden(1))
        self.assertTrue(self.window.set_table.isColumnHidden(2))
        for name in ("BPM", "Camelot", "Key", "Time", "Title"):
            options.column_checks[("library", name)].setChecked(False)
        self.assertTrue(options.column_checks[("library", "Title")].isChecked())
        options.close()
        self.close_window(self.window)
        restored = self.new_window()
        self.assertTrue(restored.lib_table.isColumnHidden(1))
        self.assertTrue(restored.set_table.isColumnHidden(2))
        self.assertFalse(restored.lib_table.isColumnHidden(0))

    def test_dialogs_share_custom_titlebar_and_donation_copy_does_not_resize(self):
        message = MessageDialog(self.window, "Relink", "Matched 79 of 93 tracks.", StyledMessageBox.StandardButton.Ok)
        rename = RenameDialog(self.window, "Rename playlist", "Playlist name", "Friday")
        for dialog in (message, rename):
            self.assertTrue(dialog.windowFlags() & Qt.WindowType.FramelessWindowHint)
            self.assertIsNotNone(dialog.findChild(TitleBar))
            self.assertFalse(dialog.windowIcon().isNull())
            dialog.close()
        about = AboutDialog(QIcon(self.window._icon_path), self.window._icon_path, self.window)
        about.findChild(QTabWidget).setCurrentIndex(2)
        about.show()
        self.app.processEvents()
        size = about.size()
        with patch("faderlogic.dialogs.QApplication.clipboard") as clipboard:
            about.copy_btc_button.click()
            clipboard.return_value.setText.assert_called_once_with(BTC_ADDRESS)
        self.app.processEvents()
        self.assertEqual(about.size(), size)
        self.assertEqual(about.copy_status.text(), "Bitcoin address copied.")
        about.copy_timer.timeout.emit()
        self.app.processEvents()
        self.assertEqual(about.size(), size)
        self.assertEqual(about.copy_status.text(), "")
        about.close()

    def test_set_selection_updates_preview_and_survives_reorder_and_restart(self):
        self.import_fixture("Library", key="8A")
        first = dict(self.window.library[0])
        second = dict(first, title="Outkast - Roses", key="9A", path="outkast.mp3")
        self.window.active_set = [first, second]
        self.window._fill_set()
        with patch.object(self.window, "_load_waveform") as load:
            self.window.set_table.selectRow(1)
            self.assertEqual(self.window.wheel.selected_key, "9A")
            load.assert_called_once()
            self.window.move_up()
            self.assertEqual(self.window._set_row(), 0)
            self.assertEqual(self.window.wheel.selected_key, "9A")
            self.assertEqual(self.window._current_preview_track()["title"], "Outkast - Roses")
            load.assert_called_once()
            self.window.search.setText("no matches")
            self.assertEqual(self.window.wheel.selected_key, "9A")
        self.close_window(self.window)
        restored = self.new_window()
        self.assertEqual(restored.wheel.selected_key, "9A")
        self.assertEqual(restored._preview_source, "set")
        self.assertEqual(restored._set_row(), 0)

    def test_exported_set_imports_directly_without_txt_dialog(self):
        self.import_fixture("Original", key="9A")
        audio = (self.root / "audio.mp3").resolve()
        audio.touch()
        first = dict(self.window.library[0], path=str(audio))
        second = dict(first, title="Second", key="10B", bpm="132.0")
        self.window.active_set = [second, first, dict(second)]
        target = self.root / "Reopen.m3u8"
        with patch("faderlogic.main_window.QFileDialog.getSaveFileName", return_value=(str(target), "")):
            self.window.export_set()
        self.window.clear_set()
        with patch.object(MainWindow, "_load_waveform"), \
             patch("faderlogic.main_window.QFileDialog.getOpenFileName", return_value=(str(target), "")) as picker:
            self.window.import_playlist()
            picker.assert_called_once()
        self.assertEqual([t["title"] for t in self.window.active_set], ["Second", first["title"], "Second"])
        self.assertEqual([t["key"] for t in self.window.active_set], ["10B", "9A", "10B"])
        self.assertEqual(self.window.store.get_playlist(self.window.active_playlist_id)["source_txt"], "")

    def test_pre_rename_export_imports_without_txt_dialog(self):
        self.test_exported_set_imports_directly_without_txt_dialog()
        target = self.root / 'Reopen.m3u8'
        target.write_text(target.read_text(encoding='utf-8').replace('#FADERLOGIC-', '#MIXLOGIC-'), encoding='utf-8')
        self.window.clear_set()
        with patch.object(MainWindow, '_load_waveform'), \
             patch('faderlogic.main_window.QFileDialog.getOpenFileName', return_value=(str(target), '')) as picker:
            self.window.import_playlist()
            picker.assert_called_once()
        self.assertEqual([t['key'] for t in self.window.active_set], ['10B', '9A', '10B'])

    def test_pre_rename_library_opens_with_session_and_original_waveform_mode(self):
        identity, _, _ = self.import_fixture('Saved set', key='5A')
        track = dict(self.window.library[0])
        self.window.active_set = [track, dict(track)]
        self.window._fill_set()
        self.close_window(self.window)
        current = self.root / 'FaderLogic-data'
        store = LibraryStore(current)
        session = store.load_session()
        session['appearance'] = dict(wheel_style='outline', wave_style='enhanced', wave_mode='mixlogic', theme='dark')
        store.save_session(session)
        store.update_tracks(identity, [track], r'D:\Saved Music')
        store.close()
        current.rename(self.root / 'MixLogic-data')
        with patch.object(MainWindow, '_load_waveform'):
            restored = self.new_window()
        from faderlogic import __version__
        self.assertEqual(restored.windowTitle(), f'FaderLogic {__version__}')
        self.assertEqual(restored.active_playlist_id, identity)
        self.assertEqual(restored.linked_folder, r'D:\Saved Music')
        self.assertEqual([t['key'] for t in restored.active_set], ['5A', '5A'])
        self.assertEqual(restored.appearance_settings()['wave_mode'], 'faderlogic')
        self.assertEqual(restored.wheel.visual_style, 'outline')

    def test_single_titlebar_footer_alignment_and_relink_active_state(self):
        self.assertEqual(len(self.window.findChildren(TitleBar)), 1)
        self.assertIsNone(self.window.findChild(QLabel, "titleName"))
        self.window.resize(1100, 700)
        self.app.processEvents()
        self.assertEqual(self.window.width(), 1100)
        self.assertLess(self.window.findChild(TitleBar).mapTo(self.window, QPoint()).y(), 10)
        self.assertFalse(self.window.btn_relink.isEnabled())
        self.import_fixture("Linked")
        self.window.linked_folder = str(self.root.resolve())
        self.window._refresh_playlist_browser()
        self.assertTrue(self.window.btn_relink.isChecked())
        with patch("faderlogic.main_window.QFileDialog.getExistingDirectory", return_value=""):
            self.window.btn_relink.click()
        self.assertTrue(self.window.btn_relink.isChecked())
        self.app.processEvents()
        right_edge = self.window.splitter.widget(1).mapTo(self.window, QPoint()).x() + 6
        self.assertAlmostEqual(self.window.right_footer.mapTo(self.window, QPoint()).x(), right_edge, delta=3)
        self.assertIn("Transition Time", [label.text() for label in self.window.right_footer.findChildren(QLabel)])

    def test_legacy_chart_two_preference_migrates_to_new_name(self):
        camelot.set_active_chart("Chart 2 (Mixed In Key)")
        self.assertEqual(camelot.active_chart_name, "Chart 2 (harmonic transitions)")
        self.assertTrue(all("Mixed In Key" not in name for name in camelot.CHART_CHOICES))

    def test_unknown_import_shows_inline_without_popup_or_default_key(self):
        source = self.root / "Unverified.m3u8"
        metadata = self.root / "Unverified.txt"
        source.write_text("#EXTM3U\n#EXTINF:-1,Unverified\nmissing.wav\n", encoding="utf-8")
        metadata.write_text("Track Title\tArtist\tBPM\tKey\nUnverified\tArtist\t\t\n", encoding="utf-16")
        with patch("faderlogic.main_window.QFileDialog.getOpenFileName", side_effect=[(str(source), ""), (str(metadata), "")]), \
             patch("faderlogic.main_window.QMessageBox.warning") as notice:
            self.window.import_playlist()
            notice.assert_not_called()
        self.assertEqual(self.window.lib_table.item(0, 2).text(), "Unknown")
        self.assertEqual(self.window.lib_table.item(0, 3).text(), "Unknown")
        self.assertIsNone(self.window.wheel.selected_key)
        self.assertFalse(self.window.wheel._status)
        self.assertTrue(self.window.btn_metadata.isVisible())
        self.assertEqual(self.window.lib_table.verticalHeaderItem(0).text(), "!")
        self.assertIn("Unknown", self.window.lbl_relation.text())
        self.window.add_selected_to_set()
        self.assertEqual(self.window.lbl_set_time.text(), "Set length: Unknown")


if __name__ == "__main__":
    unittest.main()
