"""The public rename must preserve previous libraries, preferences and exports."""
import os
from pathlib import Path
import shutil
import sqlite3
import unittest
from unittest.mock import patch
from uuid import uuid4

from faderlogic import playlist
from faderlogic.appearance import clean_appearance
from faderlogic.paths import prepare_data_directory
from faderlogic.storage import LibraryStore


class RebrandTests(unittest.TestCase):
    def setUp(self):
        self.root = (Path('build') / ('rebrand-test-' + uuid4().hex)).resolve()
        self.root.mkdir(parents=True)
        self.addCleanup(shutil.rmtree, self.root)

    def test_old_and_new_export_headers_roundtrip_order_repeats_and_unknowns(self):
        audio = self.root / 'Beyoncé 日本語.wav'
        audio.touch()
        known = dict(path=str(audio), title='First', artist='DJ', bpm='128.0', key='5A', time='05:00', duration=300)
        unknown = dict(known, title='Second', artist='Unknown', bpm='Unknown', key='Unknown')
        tracks = [known, unknown, dict(known)]
        new = self.root / 'new.m3u8'
        playlist.export_m3u8(new, tracks)
        content = new.read_text(encoding='utf-8')
        self.assertIn('#FADERLOGIC-PLAYLIST:1', content)
        self.assertNotIn('#MIXLOGIC', content)
        old = self.root / 'old.m3u8'
        old.write_text(content.replace('#FADERLOGIC-', '#MIXLOGIC-'), encoding='utf-8')
        for file in (old, new):
            self.assertTrue(playlist.is_faderlogic_playlist(file))
            restored = playlist.build_library(file, None)
            self.assertEqual([t['title'] for t in restored], ['First', 'Second', 'First'])
            self.assertEqual([t['key'] for t in restored], ['5A', 'Unknown', '5A'])
            self.assertEqual(restored[1]['bpm'], 'Unknown')

    def create_old_library(self, base):
        source = self.root / 'original.m3u8'
        source.write_text('#EXTM3U\n', encoding='utf-8')
        store = LibraryStore(base / 'MixLogic-data')
        identity = store.add_playlist(source, None, [])
        store.update_tracks(identity, [], r'D:\Music')
        store.save_session(dict(active_playlist_id=identity, active_set=[], appearance=dict(wave_mode='mixlogic',theme='light')))
        store.close()
        return identity

    def test_portable_migration_copies_sources_settings_and_linked_folder_once(self):
        identity = self.create_old_library(self.root)
        original = self.root / 'MixLogic-data/library.sqlite3'
        original_bytes = original.read_bytes()
        migrated = prepare_data_directory(self.root)
        self.assertEqual(migrated, self.root / 'FaderLogic-data')
        self.assertTrue((migrated / 'sources' / identity / 'playlist.m3u8').is_file())
        store = LibraryStore(migrated)
        self.assertEqual(store.get_playlist(identity)['linked_folder'], r'D:\Music')
        appearance = clean_appearance(store.load_session()['appearance'])
        self.assertEqual(appearance['wave_mode'], 'faderlogic')
        self.assertEqual(appearance['theme'], 'light')
        store.rename(identity, 'New name')
        store.close()
        self.assertEqual(original.read_bytes(), original_bytes)
        self.assertEqual(prepare_data_directory(self.root), migrated)
        store = LibraryStore(migrated)
        self.assertEqual(store.get_playlist(identity)['name'], 'New name')
        store.close()

    def test_installed_migration_discovers_old_user_profile(self):
        self.create_old_library(self.root / 'MixLogic')
        with patch.dict(os.environ, LOCALAPPDATA=str(self.root)):
            result = prepare_data_directory(self.root / 'FaderLogic')
        self.assertTrue((result / 'library.sqlite3').is_file())
        self.assertTrue((self.root / 'MixLogic/MixLogic-data/library.sqlite3').is_file())

    def test_live_wal_database_is_backed_up_with_committed_state(self):
        self.create_old_library(self.root)
        database = self.root / 'MixLogic-data/library.sqlite3'
        connection = sqlite3.connect(database)
        try:
            connection.execute('PRAGMA journal_mode=WAL')
            connection.execute("INSERT INTO state VALUES ('migration-test', 'committed')")
            connection.commit()
            target = prepare_data_directory(self.root)
        finally:
            connection.close()
        connection = sqlite3.connect(target / 'library.sqlite3')
        try:
            self.assertEqual(connection.execute("SELECT value FROM state WHERE key='migration-test'").fetchone()[0], 'committed')
        finally:
            connection.close()

    def test_corrupt_old_library_never_becomes_an_empty_replacement(self):
        source = self.root / 'MixLogic-data'
        source.mkdir()
        (source / 'library.sqlite3').write_bytes(b'not a database')
        with self.assertRaises(sqlite3.DatabaseError):
            prepare_data_directory(self.root)
        self.assertFalse((self.root / 'FaderLogic-data').exists())
        self.assertFalse(list(self.root.glob('.faderlogic-migration-*')))


if __name__ == '__main__':
    unittest.main()
