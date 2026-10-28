"""Workflow regressions for the 1.4.1 test build."""
import math
import os
from pathlib import Path
import tempfile
import shutil
from uuid import uuid4
from contextlib import contextmanager
import unittest
from unittest.mock import patch
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from PyQt6.QtCore import QPointF, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from faderlogic import camelot, playlist
from faderlogic.behavior import title_sort_key
from faderlogic.main_window import MainWindow
from faderlogic.widgets import CamelotWheelWidget
from faderlogic.waveform import analyze_samples, WaveformCache
from faderlogic.appearance import WHEEL_STYLES


@contextmanager
def test_directory():
    base=Path('build').resolve()
    root=base/('next-update-test-'+uuid4().hex)
    root.mkdir(parents=True)
    try:
        yield str(root)
    finally:
        assert root.resolve().parent == base and root.name.startswith('next-update-test-')
        shutil.rmtree(root)


class NextUpdateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def test_independent_sort_options_and_meaningful_numbers(self):
        for punctuation in (False,True):
            for numbers in (False,True):
                key=lambda text:title_sort_key(text,punctuation,numbers)
                self.assertEqual(key('- Zhu'),'zhu' if punctuation else '- zhu')
                self.assertEqual(key('01_Title'),'title' if numbers else '01_title')
                self.assertEqual(key('- 02 - Abba'),'abba' if punctuation and numbers else '02 - abba' if punctuation else '- 02 - abba')
                for title in ('1999','99 Luftballons','2 Unlimited'):
                    self.assertEqual(key(title),title.casefold())
        for title in ('01 Title','01. Title','02 - Title','01_Title'):
            self.assertEqual(title_sort_key(title,numbers=True),'title')

    def test_actual_wedge_hit_testing_every_style_chart_and_ring(self):
        wheel=CamelotWheelWidget();wheel.resize(612,612);scale=3
        clicks=[];wheel.keyClicked.connect(clicks.append)
        for chart in camelot.CHART_CHOICES:
            camelot.set_active_chart(chart)
            for style in WHEEL_STYLES:
                wheel.set_visual_style(style);wheel.set_active_key('5A')
                for code in camelot.CAMELOT_COLORS:
                    number=int(code[:-1]);angle=math.radians(90-(number%12)*30)
                    radius=47 if code.endswith('A') else 79
                    position=QPointF(306+radius*math.cos(angle)*scale,306-radius*math.sin(angle)*scale)
                    self.assertEqual(wheel.key_at(position),code)
                    before=len(clicks);QTest.mouseClick(wheel,Qt.MouseButton.LeftButton,pos=position.toPoint())
                    self.assertEqual(len(clicks)>before,code in wheel._status)
        self.assertIsNone(wheel.key_at(QPointF(306,306)))
        wheel.close()

    def test_filters_sorting_set_order_and_saved_behavior(self):
        with test_directory() as root:
            w=MainWindow(root,str(Path('assets/faderlogic.ico').resolve()))
            try:
                w.library=[dict(title=t,artist='DJ',bpm='125',key=k,time='03:00',path=str(Path(root)/f'{i}.mp3')) for i,(t,k) in enumerate((('- Zhu','5A'),('01 Abba','6A'),('Other','5A')))]
                w._fill_library(w.library);w.active_set=[dict(w.library[2]),dict(w.library[0])];w._fill_set()
                reference=w.wheel.selected_key;original=list(w.active_set)
                with patch.object(w.player,'stop') as stop:
                    w._wheel_key_clicked('5A')
                    self.assertEqual(w.wheel.selected_key,reference)
                    self.assertEqual(w.wheel.filter_key,'5A')
                    self.assertEqual(len(w.library_view_tracks()),2)
                    stop.assert_not_called()
                w.search.setText('zhu');self.assertEqual(len(w.library_view_tracks()),1)
                w.lib_table.sortItems(0,Qt.SortOrder.DescendingOrder)
                visible=[w.lib_table.item(r,0).text() for r in range(3) if not w.lib_table.isRowHidden(r)]
                self.assertEqual(visible,['- Zhu'])
                w._wheel_key_clicked('5A');self.assertIsNone(w.key_filter)
                self.assertEqual(len(w.library_view_tracks()),1)
                w.search.clear();self.assertEqual(len(w.library_view_tracks()),3)
                self.assertEqual(w.active_set,original)
                for track in w.library:
                    Path(track['path']).write_bytes(b'demo')
                exported=Path(root)/'ordered.m3u8'
                playlist.export_m3u8(str(exported),w.active_set)
                self.assertEqual([row['path'] for row in playlist.parse_m3u8(str(exported))],
                                 [track['path'] for track in original])
                w._set_key_filter('5A');w.search.setText('zhu')
                entry=dict(name='Other playlist',linked_folder=None,tracks=list(w.library))
                with patch.object(w.store,'get_playlist',return_value=entry):
                    w._activate_playlist('test-id')
                self.assertIsNone(w.key_filter);self.assertEqual(w.search.text(),'')
                w.apply_behavior(dict(punctuation=True,numbers=True));w.lib_table.sortItems(0)
                self.assertEqual(w.lib_table.item(0,0).text(),'01 Abba')
                w._save_session()
            finally:w.close()
            restored=MainWindow(root,str(Path('assets/faderlogic.ico').resolve()))
            self.assertEqual(restored.behavior,dict(punctuation=True,numbers=True));restored.close()

    def test_pcm_detail_preserves_transients_silence_and_cache(self):
        samples=[0]*8192;samples[99]=30000;samples[103]=-24000
        rows=analyze_samples(samples,8)
        fine=[pair for row in rows for pair in row[28]]
        self.assertAlmostEqual(max(high for low,high in fine),30000/32768)
        self.assertAlmostEqual(min(low for low,high in fine),-24000/32768)
        self.assertTrue(all(low==high==0 for row in rows[1:] for low,high in row[28]))
        with test_directory() as root:
            path=Path(root)/'track.wav';path.write_bytes(b'test')
            cache=WaveformCache(str(Path(root)/'cache.db'));cache.put(str(path),rows)
            self.assertEqual([tuple(pair) for pair in cache.get(str(path))[0][28]],rows[0][28]);cache.close()

    def test_filter_control_is_centered_under_wheel_without_layout_shift(self):
        with test_directory() as root:
            w=MainWindow(root,str(Path('assets/faderlogic.ico').resolve()))
            try:
                w.show()
                for _ in range(4):self.app.processEvents()
                def geometry():
                    return [widget.geometry() for widget in (w,w.wheel,w.lib_table,w.set_table,w.right_footer)]
                baseline=geometry()
                for key in ('5A','12B',None,'1A',None):
                    w._set_key_filter(key)
                    for _ in range(2):self.app.processEvents()
                    self.assertEqual(geometry(),baseline,key)
                    if key:
                        wheel_center=w.wheel.mapTo(w,w.wheel.rect().center())
                        control_center=w.btn_key_filter.mapTo(w,w.btn_key_filter.rect().center())
                        self.assertLessEqual(abs(wheel_center.x()-control_center.x()),1)
                        self.assertGreater(control_center.y(),wheel_center.y())
            finally:w.close()

