"""Regressions for live chart changes, selection, set edits and relation visibility."""
import os
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
import shutil

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFontDatabase
from faderlogic import camelot
from faderlogic.dialogs import OptionsDialog
from faderlogic.main_window import MainWindow
from faderlogic.theme import STYLESHEET


class RelationUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        for name in ("segoeui.ttf", "segoeuib.ttf"):
            path = Path("C:/Windows/Fonts") / name
            if path.exists():
                QFontDatabase.addApplicationFont(str(path))
        cls.app.setStyleSheet(STYLESHEET)

    def setUp(self):
        camelot.set_active_chart(next(iter(camelot.CHART_CHOICES)))
        self.cache_patch = patch("faderlogic.main_window.WaveformCache")
        self.cache_patch.start()
        self.data_dir = Path("build") / ("relation-test-" + uuid4().hex)
        self.data_dir.mkdir(parents=True)
        self.window = MainWindow(str(self.data_dir), str(Path("assets/faderlogic.ico").resolve()))
        self.window.show()
        self.window.resize(1100, 700)
        for _ in range(4):
            self.app.processEvents()
        self.tracks = [dict(title="A previous track", artist="Artist", bpm="128", key="8A", time="05:30", path="missing-8A.mp3"),
                       dict(title="Z selected track " + "long title " * 40, artist="Artist", bpm="130", key="8B", time="06:00", path="missing-8B.mp3")]
        self.window.library = self.tracks
        self.window._fill_library(self.tracks)
        self.window.active_set = [dict(self.tracks[0])]
        self.window._fill_set()
        for row in range(self.window.lib_table.rowCount()):
            if self.window.lib_table.item(row, 0).data(256)["key"] == "8B":
                self.window.lib_table.selectRow(row)
                break

    def tearDown(self):
        self.window.close()
        self.cache_patch.stop()
        shutil.rmtree(self.data_dir)
        camelot.set_active_chart(next(iter(camelot.CHART_CHOICES)))

    def test_switch_chart_preserves_selection_and_recomputes_wheel_and_relation(self):
        self.assertEqual(self.window.lbl_relation.text(), "Relation to last: Energy Boost (+)")
        options = OptionsDialog(self.window.wheel, self.window._icon_path, self.window)
        with patch.object(self.window.player, "stop") as stop:
            list(options.chart_group.buttons())[1].setChecked(True)
            self.assertEqual(self.window._selected_library_track()["key"], "8B")
            self.assertEqual(self.window.lbl_relation.text(), "Relation to last: Scale Change")
            self.assertEqual(self.window.wheel._detail["8A"], "Scale Change")
            self.window.wheel.set_show_all(True)
            self.assertEqual(self.window.lbl_relation.text(), "Relation to last: Scale Change")
            stop.assert_not_called()
        list(options.chart_group.buttons())[0].setChecked(True)
        self.assertEqual(self.window.wheel._detail["8A"], "Energy Drop (-)")
        self.assertEqual(self.window.lbl_relation.text(), "Relation to last: Energy Boost (+)")
        options.close()

    def test_relation_visible_with_long_title_and_updates_after_set_edits(self):
        self.app.processEvents()
        self.assertGreaterEqual(self.window.lbl_relation.width(), self.window.lbl_relation.sizeHint().width())
        self.assertIn("8A → 8B", self.window.lbl_relation.toolTip())
        self.window.add_selected_to_set()
        self.assertEqual(self.window.lbl_relation.text(), "Relation to last: Perfect Match")
        self.window.set_table.selectRow(1)
        self.window.move_up()
        self.assertEqual(self.window.lbl_relation.text(), "Relation to last: Energy Boost (+)")
        self.window.set_table.selectRow(0)
        self.window.move_down()
        self.assertEqual(self.window.lbl_relation.text(), "Relation to last: Perfect Match")
        self.window.remove_selected()
        # Removing the previewed set track selects the remaining set track.
        self.assertEqual(self.window.lbl_relation.text(), "Relation to last: Perfect Match")
        self.window.clear_set()
        self.assertEqual(self.window.lbl_relation.text(), "Relation to last: set is empty")
        self.window.search.setText("nothing matches")
        self.assertEqual(self.window.lbl_relation.text(), "Relation: select a track")


if __name__ == "__main__":
    unittest.main()
