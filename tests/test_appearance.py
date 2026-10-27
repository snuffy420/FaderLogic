"""Appearance choices must preserve charts, seeking, metadata and saved preferences."""
import hashlib
import math
import os
from pathlib import Path
import shutil
import unittest
from uuid import uuid4
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from faderlogic import camelot, playlist
from faderlogic.appearance import WHEEL_STYLES, WAVE_STYLES, WAVE_MODES, accessible_legend, standard_legend, RELATION_CODES
from faderlogic.widgets import CamelotWheelWidget, WaveformWidget
from faderlogic.waveform import spectrum_features, WaveformCache
from faderlogic.dialogs import OptionsDialog, MetadataReviewDialog
from faderlogic.main_window import MainWindow
from faderlogic.theme import STYLESHEET


class AppearanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(STYLESHEET)

    def setUp(self):
        from faderlogic.theme import apply_theme
        apply_theme('dark')
        self.root = Path('build') / ('appearance-test-' + uuid4().hex)
        self.root.mkdir(parents=True)
        self.windows = []
        camelot.set_active_chart(next(iter(camelot.CHART_CHOICES)))

    def tearDown(self):
        for window in self.windows:
            window.close()
        self.app.processEvents()
        shutil.rmtree(self.root)
        camelot.set_active_chart(next(iter(camelot.CHART_CHOICES)))
        from faderlogic.theme import apply_theme
        apply_theme('dark')

    def window(self):
        w = MainWindow(str(self.root), str(Path('assets/faderlogic.ico').resolve()))
        self.windows.append(w)
        w.show(); self.app.processEvents()
        return w

    def test_standard_styles_share_every_original_key_and_relation_colour(self):
        wheel = CamelotWheelWidget()
        for chart in camelot.CHART_CHOICES:
            camelot.set_active_chart(chart)
            for selected in camelot.CAMELOT_COLORS:
                wheel.set_active_key(selected)
                for show_all in (False, True):
                    wheel.set_show_all(show_all)
                    wheel.set_visual_style('classic')
                    expected = {key: tuple(c.name() if hasattr(c, 'name') else c for c in wheel.segment_colours(key))
                                for key in camelot.CAMELOT_COLORS}
                    legend = {name:colour.lower() for _,name,colour in standard_legend(chart,show_all)}
                    for code,label in wheel._detail.items():
                        if code != selected:
                            self.assertEqual(expected[code][1],legend[label])
                    status, detail = dict(wheel._status), dict(wheel._detail)
                    for style in ('obsidian', 'minimal', 'outline'):
                        wheel.set_visual_style(style)
                        for key, value in expected.items():
                            self.assertEqual(tuple(c.name() if hasattr(c, 'name') else c for c in wheel.segment_colours(key)), value)
                        self.assertEqual((wheel._status, wheel._detail), (status, detail))
        wheel.close()

    def test_accessible_wheel_has_text_relations_even_without_colour(self):
        wheel = CamelotWheelWidget()
        wheel.set_visual_style('accessible'); wheel.set_active_key('8A')
        self.assertIn('Selected key: 8A', wheel.accessibleDescription())
        self.assertIn('Perfect Match', wheel.accessibleDescription())
        self.assertEqual(wheel.segment_colours('8A')[1].name(), '#75ceff')
        wheel.set_active_key('Unknown')
        self.assertFalse(wheel._status)
        wheel.close()

    def test_accessible_explanations_match_each_chart_and_rendered_colours(self):
        wheel = CamelotWheelWidget(); wheel.set_visual_style('accessible')
        for chart in camelot.CHART_CHOICES:
            camelot.set_active_chart(chart)
            for all_variations in (False, True):
                wheel.set_show_all(all_variations); wheel.set_active_key('5A')
                legend = {name:(code,colour,pattern) for code,name,colour,pattern in accessible_legend(chart, all_variations)}
                self.assertEqual(len(legend),8)
                for key,label in wheel._detail.items():
                    self.assertEqual(wheel.segment_colours(key)[1].name(), legend[label][1].lower())
                    self.assertEqual(legend[label][0],RELATION_CODES[label])
                from faderlogic.dialogs import _accessible_help_html
                help_html=_accessible_help_html()
                self.assertEqual(camelot.active_chart_name,chart)
                self.assertIn('Energy Boost (+++)',help_html)
                self.assertIn("Jaw's Mix",help_html)
        wheel.close()

    def test_colourblind_all_keys_follow_both_chart_legends_including_selection(self):
        from faderlogic.appearance import wheel_legend_html
        wheel=CamelotWheelWidget();wheel.set_visual_style('accessible')
        for chart in camelot.CHART_CHOICES:
            camelot.set_active_chart(chart)
            for all_variations in (False,True):
                wheel.set_show_all(all_variations)
                legend={name:colour.lower() for _,name,colour,_ in accessible_legend(chart,all_variations)}
                for selected in camelot.CAMELOT_COLORS:
                    wheel.set_active_key(selected)
                    for target in camelot.CAMELOT_COLORS:
                        status,relation=camelot.get_compatibility(selected,target)
                        base,edge,active=wheel.segment_colours(target)
                        self.assertEqual(active,status in ('green','orange'))
                        if active:self.assertEqual(edge.name(),legend[relation],(chart,selected,target))
                for accessible in (False,True):
                    html=wheel_legend_html(chart,all_variations,accessible)
                    self.assertIn('|',html)
                    self.assertIn(chart,html)
                    if accessible:self.assertIn('selected + perfect match',html)
        wheel.close()

    def test_accessible_both_labels_fit_each_text_box(self):
        from PyQt6.QtGui import QPainter,QFontMetricsF
        recorded=[]
        class RecordingPainter(QPainter):
            def drawText(self,*args):
                if len(args)==3 and hasattr(args[0],'width') and args[0].width()==25:
                    box,_,text=args;metrics=QFontMetricsF(self.font())
                    recorded.append((text,metrics.horizontalAdvance(text),metrics.height(),box.width(),box.height()))
                return super().drawText(*args)
        wheel=CamelotWheelWidget();wheel.resize(600,600);wheel.set_visual_style('accessible')
        wheel.set_label_mode('both');wheel.set_active_key('11A');wheel.show()
        with patch('faderlogic.widgets.QPainter',RecordingPainter):
            self.app.processEvents();wheel.grab()
        self.assertTrue(recorded)
        texts={row[0] for row in recorded}
        for key,name in camelot.REAL_KEYS.items():
            self.assertIn(key,texts);self.assertIn(name,texts)
        self.assertIn('SEL =',texts)
        for text,width,height,box_width,box_height in recorded:
            self.assertLessEqual(width,box_width,text)
            self.assertLessEqual(height,box_height,text)
        wheel.close()

    def test_adjacent_wedge_borders_do_not_overwrite_each_other(self):
        from PyQt6.QtGui import QImage,QPainter
        wheel=CamelotWheelWidget();wheel.set_show_all(True);wheel.set_active_key('5A')
        cells=[(32,62,45,30,'2A'),(32,62,15,0,'3A')]
        for style in WHEEL_STYLES:
            wheel.set_visual_style(style)
            def render(order):
                image=QImage(600,600,QImage.Format.Format_ARGB32);image.fill(Qt.GlobalColor.transparent)
                p=QPainter(image);p.setRenderHint(QPainter.RenderHint.Antialiasing)
                p.translate(300,300);p.scale(2.8,2.8)
                for cell in order:wheel._segment(p,*cell)
                p.end();return image
            forward,reverse=render(cells),render(reversed(cells))
            for angle in (14,16):
                x=round(300+47*2.8*math.cos(math.radians(angle)))
                y=round(300-47*2.8*math.sin(math.radians(angle)))
                self.assertEqual(forward.pixelColor(x,y),reverse.pixelColor(x,y),(style,angle))
                self.assertGreater(forward.pixelColor(x,y).alpha(),200)
        wheel.close()

    def test_retired_3d_settings_fall_back_without_loading_quick(self):
        from faderlogic.appearance import clean_appearance
        import sys
        for old in ('crystal3d','titanium3d','neon3d'):
            values=clean_appearance(dict(wheel_style=old,wave_style=old,wave_mode='rgb',theme='light'))
            self.assertEqual(values,dict(wheel_style='classic',wave_style='classic',wave_mode='rgb',theme='light'))
        self.assertEqual(len(WHEEL_STYLES),5);self.assertEqual(len(WAVE_STYLES),9)
        self.assertFalse(any(name.startswith(('PyQt6.QtQuick','PyQt6.QtQml')) for name in sys.modules))

    def test_missing_row_markers_follow_library_sorting(self):
        w=self.window()
        missing=dict(title='Zebra',artist='Unknown Artist',bpm='128',key='9A',time='04:00',path='missing.wav')
        known=dict(missing,title='Alpha',artist='Known artist')
        w.library=[missing,known]; w._fill_library(w.library)
        for order in (Qt.SortOrder.AscendingOrder,Qt.SortOrder.DescendingOrder):
            w.lib_table.sortItems(0,order)
            for row in range(2):
                title=w.lib_table.item(row,0).text()
                self.assertEqual(w.lib_table.verticalHeaderItem(row).text(),'!' if title=='Zebra' else '')

    def test_apply_saves_and_preview_only_changes_do_not_change_workspace(self):
        w = self.window()
        dialog = OptionsDialog(w.wheel, w._icon_path, w)
        panel = dialog.appearance
        panel.wheel_choice.setCurrentIndex(panel.wheel_choice.findData('outline'))
        panel.wave_choice.setCurrentIndex(panel.wave_choice.findData('spectrogram'))
        panel.mode_choice.setCurrentIndex(panel.mode_choice.findData('rgb'))
        self.assertEqual(w.wheel.visual_style, 'classic')
        self.assertEqual(panel.wheel_preview.visual_style, 'outline')
        dialog.apply_button.click()
        expected = dict(wheel_style='outline', wave_style='spectrogram', wave_mode='rgb',theme='dark')
        self.assertEqual(w.appearance_settings(), expected)
        self.assertEqual(w.store.load_session()['appearance'], expected)
        panel.wheel_choice.setCurrentIndex(2)
        dialog.close()
        self.assertEqual(w.appearance_settings(), expected)
        w.close(); self.windows.remove(w)
        restored = self.window()
        self.assertEqual(restored.appearance_settings(), expected)
        restored.apply_appearance(dict(wheel_style='bad', wave_style='bad', wave_mode='bad'))
        self.assertEqual(restored.appearance_settings(), dict(wheel_style='classic',wave_style='classic',wave_mode='bands',theme='dark'))
        for style in WHEEL_STYLES:
            restored.apply_appearance(dict(wheel_style=style))
            for chart in camelot.CHART_CHOICES:
                camelot.set_active_chart(chart); restored.refresh_relations()
                self.assertTrue(restored.wheel_legend.isVisible())
                self.assertIn(chart,restored.wheel_legend.text())

    def test_missing_fields_consistent_in_both_tables_and_marker_survives_hiding_columns(self):
        w = self.window()
        blank = dict(title='', artist='Unknown Artist', bpm='', key='', time='', path='missing.wav', metadata_checked=True)
        w.library = [blank]
        w._fill_library(w.library)
        w.active_set = [dict(blank)]; w._fill_set()
        self.assertEqual([w.lib_table.item(0,c).text() for c in range(6)], ['Unknown']*6)
        self.assertEqual([w.set_table.item(0,c).text() for c in range(1,7)], ['Unknown']*6)
        self.assertEqual(w.set_table.item(0,0).text(), '1')
        for name, table in (('library', w.lib_table), ('set', w.set_table)):
            w.set_column_visible(name, 1 if name=='library' else 2, False)
            self.assertTrue(table.verticalHeader().isVisible())
            self.assertEqual(table.verticalHeaderItem(0).text(), '!')
        self.assertFalse(hasattr(w, 'lbl_metadata_warning'))
        valid = dict(blank, title='Known', artist='Artist', bpm='128', key='9A', time='04:00')
        self.assertEqual(playlist.display_metadata(valid), ['Known','Artist','128','9A','Em','04:00'])

    def test_review_dialog_is_bounded_with_long_titles_and_artist_only_issues(self):
        w = self.window()
        w.library = [dict(title='A very long title '*20,artist='Unknown Artist',bpm='128',key='9A',time='04:00',path='missing') for _ in range(93)]
        review = MetadataReviewDialog(w); review.show(); self.app.processEvents()
        self.assertEqual(review.table.rowCount(),93)
        self.assertLessEqual(review.height(), review.screen().availableGeometry().height()-20)
        self.assertIn('Artist', review.table.item(0,2).text())
        self.assertNotIn('BPM', review.table.item(0,2).text())
        self.assertTrue(review.table.verticalScrollBar().maximum()>0)
        review.close()

    def test_all_waveform_styles_modes_render_and_preserve_scrubbing(self):
        wave = WaveformWidget(); wave.resize(640,90); wave.show()
        features = [spectrum_features([int(18000*math.sin(2*math.pi*f*i/22050)) for i in range(1024)])
                    for f in (80,1000,6000)]
        bars = [features[(i//15)%3] for i in range(90)]
        wave.set_track('Real FFT test',bars); wave.set_progress(.3)
        seek=[]; wave.scrubRequested.connect(seek.append)
        hashes=set()
        for style in WAVE_STYLES:
            for mode in WAVE_MODES:
                wave.set_appearance(style,mode); self.app.processEvents()
                image=wave.grab().toImage()
                digest=hashlib.sha256(image.constBits().asstring(image.sizeInBytes())).hexdigest()
                hashes.add(digest)
                self.assertEqual(wave.progress,.3)
                QTest.mouseClick(wave,Qt.MouseButton.LeftButton,pos=QPoint(320,40))
                self.assertAlmostEqual(seek[-1],.5)
        self.assertEqual(len(hashes),len(WAVE_STYLES)*len(WAVE_MODES))
        wave.close()

    def test_frequency_analysis_separates_bass_mid_high_and_silence_is_silent(self):
        for band,f in enumerate((80,1000,6000)):
            row=spectrum_features([int(18000*math.sin(2*math.pi*f*i/22050)) for i in range(1024)])
            self.assertEqual(max(range(3),key=lambda i:row[i]),band)
            self.assertGreater(row[band],.4)
            self.assertEqual(len(row),28)
        self.assertEqual(spectrum_features([0]*1024),(0.,)*28)

    def test_description_is_one_line_and_preview_does_not_move(self):
        w=self.window();dialog=OptionsDialog(w.wheel,w._icon_path,w)
        dialog.resize(720,620);dialog.show();self.app.processEvents()
        panel=dialog.appearance
        baseline=panel.preview.geometry()
        for style in WHEEL_STYLES:
            panel.wheel_choice.setCurrentIndex(panel.wheel_choice.findData(style))
            self.app.processEvents()
            self.assertEqual(panel.note.height(),24)
            self.assertFalse(panel.note.wordWrap())
            self.assertEqual(panel.note.toolTip(),panel.note.text())
            self.assertEqual(panel.preview.geometry(),baseline,style)
        dialog.close()

    def test_three_band_uses_shared_centreline_and_split_styles_are_explicit(self):
        from faderlogic.wave_paint import THREE_BAND,SPLIT_STYLES
        self.assertEqual(THREE_BAND,('#167DFF','#FF9D28','#F2F6FF'))
        self.assertEqual(set(SPLIT_STYLES),{'split_bars','split_ribbon'})
        from PyQt6.QtGui import QImage,QPainter
        from faderlogic.wave_paint import draw_waveform
        rows=[(.9,.5,.2)]*40
        combined=QImage(400,90,QImage.Format.Format_ARGB32);combined.fill(Qt.GlobalColor.transparent)
        p=QPainter(combined);draw_waveform(p,400,90,rows,'filled','bands');p.end()
        # All three measured bands share y=45: high white centre, orange mid,
        # and blue low-frequency exterior. There are no separate lane baselines.
        centre=combined.pixelColor(200,45)
        mid=combined.pixelColor(200,32)
        outside=combined.pixelColor(200,16)
        self.assertGreater(centre.red(),200);self.assertGreater(centre.blue(),200)
        self.assertGreater(mid.red(),mid.blue())
        self.assertGreater(outside.blue(),outside.red())


    def test_dance_preview_has_rhythm_and_distinct_sections(self):
        from faderlogic.dance_preview import DANCE_PREVIEW
        self.assertEqual(len(DANCE_PREVIEW),256)
        self.assertTrue(all(len(row)==28 for row in DANCE_PREVIEW))
        def energy(a,b):return sum(max(row[:3]) for row in DANCE_PREVIEW[a:b])/(b-a)
        self.assertGreater(energy(160,224),energy(96,128)*2)
        self.assertGreater(max(row[0] for row in DANCE_PREVIEW[160:224]),.5)
        wave=WaveformWidget();wave.set_loading()
        self.assertEqual(wave.message,'Analyzing Waveform')


    def test_appearance_uses_the_loaded_tracks_waveform_without_changing_it(self):
        from faderlogic.dialogs import AppearancePanel
        from faderlogic.dance_preview import DANCE_PREVIEW
        wave=WaveformWidget();wave.set_track('Loaded dance track',list(DANCE_PREVIEW))
        wave.set_progress(.37)
        wheel=CamelotWheelWidget();panel=AppearancePanel(wheel,wave)
        self.assertTrue(panel.preview_uses_current_track)
        self.assertEqual(panel.wave_preview.bars,wave.bars)
        self.assertIsNot(panel.wave_preview.bars,wave.bars)
        self.assertEqual(panel.wave_preview.height(),48)
        self.assertAlmostEqual(panel.wave_preview.progress,.37)
        original=list(wave.bars)
        for style in WAVE_STYLES:
            panel.wave_choice.setCurrentIndex(panel.wave_choice.findData(style))
            self.assertEqual(panel.wave_preview.bars,original)
            self.assertEqual(wave.bars,original)
        panel.close();wheel.close();wave.close()

    def test_option_controls_update_preview_and_keep_a_visible_table_column(self):
        w=self.window();dialog=OptionsDialog(w.wheel,w._icon_path,w)
        next(button for button in dialog.group.buttons() if button.property('mode')=='both').click()
        self.assertEqual(dialog.settings_wheel.label_mode,'both')
        self.assertEqual(w.wheel.label_mode,'both')
        for (table,name),check in dialog.column_checks.items():
            if table=='library':check.setChecked(False)
        self.assertEqual(sum(box.isChecked() for (table,_),box in dialog.column_checks.items() if table=='library'),1)
        self.assertIn('Library 1',dialog.column_summary.text())
        dialog.close()

    def test_light_theme_preview_apply_restore_and_playback_reference(self):
        from faderlogic.theme import current_theme,palette_for
        from PyQt6.QtGui import QPalette
        w=self.window()
        track=dict(title='Theme test',artist='Artist',bpm='128',key='8A',time='04:00',path='missing.wav')
        w.library=[track];w._fill_library(w.library)
        w.active_set=[dict(track),dict(track,title='Second',key='9A')];w._fill_set()
        original_palette=dict(camelot.CAMELOT_COLORS)
        dialog=OptionsDialog(w.wheel,w._icon_path,w);dialog.show()
        choice=dialog.appearance.theme_choice
        choice.setCurrentIndex(choice.findData('light'));self.app.processEvents()
        self.assertEqual(current_theme(),'dark')
        self.assertIn('#FFFFFF',dialog.appearance.preview.styleSheet())
        with patch.object(w,'_load_waveform') as load,patch.object(w.player,'stop') as stop:
            dialog.apply_button.click()
            self.assertEqual(current_theme(),'light')
            load.assert_not_called();stop.assert_not_called()
        self.assertEqual(w._current_preview_track()['title'],'Theme test')
        self.assertEqual([row['title'] for row in w.active_set],['Theme test','Second'])
        self.assertEqual(camelot.CAMELOT_COLORS,original_palette)
        self.assertEqual(self.app.palette().color(QPalette.ColorRole.Window).name(),palette_for()['bg'].lower())
        self.assertEqual(w.store.load_session()['appearance']['theme'],'light')
        dialog.close();w.close();self.windows.remove(w)
        restored=self.window()
        self.assertEqual(restored.appearance_settings()['theme'],'light')
        restored.apply_appearance(dict(restored.appearance_settings(),theme='dark'))
        self.assertEqual(current_theme(),'dark')


if __name__=='__main__': unittest.main()
