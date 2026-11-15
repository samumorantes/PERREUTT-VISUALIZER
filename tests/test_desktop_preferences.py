import copy
import json
import tempfile
import time
import unittest
from pathlib import Path

from PySide6.QtCore import QCoreApplication

from desktop.controller import Controller
from desktop.preferences import DEFAULTS, GENRE_VISUAL_PRESETS, validate, egg_kind, find_preset


class NativePreferencesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.c = Controller(self.tmp.name, smoke=True)
        self.c.timer.stop()

    def tearDown(self):
        self.c.shutdown()
        self.c.deleteLater()
        self.tmp.cleanup()

    def track(self, id='a', name='Song', artist='Artist', album='Album'):
        state = self.c.smoke_state()
        state['track'].update(id=id,name=name,artist=artist,album=album)
        self.c.receive(dict(kind='state',data=state,received_at=time.monotonic()))

    def test_priority_lock_and_base_restoration(self):
        self.c.base_settings.update(mood='party',font='system')
        self.c.presets_store = {'song:a': {'font':'impact'}, 'artist:Artist': {'font':'courier'},
                               'album:Artist|Album': {'font':'georgia'}}
        self.track()
        self.assertEqual(self.c.settings['font'],'impact')
        self.assertEqual(self.c.settings['mood'],'party')
        self.c.deletePreset('song:a')
        self.assertEqual(self.c.settings['font'],'courier')
        self.c.deletePreset('artist:Artist')
        self.assertEqual(self.c.settings['font'],'georgia')
        self.c.setSetting('globalLock',True)
        self.assertEqual(self.c.settings['font'],'system')
        self.c.setSetting('globalLock',False)
        self.assertEqual(self.c.settings['font'],'georgia')
        self.track('b',artist='Other',album='Other')
        self.assertEqual(self.c.settings['font'],'system')
        self.assertFalse(self.c.active_preset)

    def test_joji_manual_mode_and_restore(self):
        self.c.base_settings.update(mood='party',theme='classic',font='system')
        self.track(name='Die For You',artist='Joji')
        self.assertTrue(self.c.view['special'])
        self.assertEqual(self.c.settings['theme'],'vaporwave')
        self.assertFalse(self.c.view['chill'])
        self.c.setSetting('mood','auto')
        self.assertTrue(self.c.view['chill'])
        self.track('b')
        self.assertFalse(self.c.view['special'])
        self.assertEqual(self.c.settings['font'],'system')

    def test_web_import_is_validated_and_atomic(self):
        self.c.importPresets(json.dumps({'song:Song':dict(fs=10,mode='neon',noise=20,fluidStyle='aurora',moodOverride='chill',globalLock=True)}))
        self.track()
        self.assertEqual(self.c.settings['fontSize'],10)
        self.assertEqual(self.c.settings['palette'],'neon')
        self.assertEqual(self.c.settings['fluidStyle'],3)
        self.assertFalse(self.c.settings['globalLock'])
        previous=copy.deepcopy(self.c.presets_store)
        self.c.importPresets('{"song:new":{"fs":5},"invalid":{}}')
        self.assertEqual(self.c.presets_store,previous)
        self.assertEqual(validate(dict(stroke=float('nan'),tv='false',font='bad',customPalCols=['#fff'])),{})
        self.assertEqual(validate(dict(fontSize=100,phrase=0)),dict(fontSize=16,phrase=1))

    def test_rephrase_keeps_syllable_times_and_source(self):
        self.c.raw_lyrics=[dict(t=8,text='Baila conmigo',words=[dict(text='Bai',t=8,end=8.4),
            dict(text='la',part=True,t=8.4,end=9),dict(text='conmigo',t=9,end=10)])]
        original=copy.deepcopy(self.c.raw_lyrics)
        self.c.setSetting('phrase',1)
        lines=self.c.state['lyrics']
        self.assertEqual([x['text'] for x in lines],['Baila','conmigo'])
        self.assertEqual(lines[0]['words'][1]['t'],8.4)
        self.assertEqual(lines[1]['t'],9)
        self.c.setSetting('phrase',4)
        self.assertEqual(len(self.c.state['lyrics']),1)
        self.assertEqual(self.c.raw_lyrics,original)

    def test_persistence_uses_base_not_active_preset(self):
        self.c.base_settings['font']='system'
        self.c.presets_store={'song:a':{'font':'impact'}}
        self.track()
        self.c.smoke=False
        self.c.save()
        saved=json.loads(Path(self.c.path).read_text(encoding='utf8'))
        self.assertEqual(saved['settings']['font'],'system')
        self.assertEqual(saved['presets']['song:a']['font'],'impact')
        self.c.smoke=True

    def test_special_text_and_legacy_album_keys(self):
        self.assertEqual(egg_kind('¡EOOO!'),'eoo')
        self.assertEqual(egg_kind('Chequéate la historia'),'impact')
        self.assertEqual(egg_kind('otra letra'),'')
        self.assertEqual(find_preset({'album:Old':{'font':'impact'}}, {'album':'Old'})[0],'album:Old')

    def test_genre_styles_preserve_detection_and_accessibility(self):
        self.track()
        for key,value in dict(source='loopback',threshold=2.25,timing='bars',reducedMotion=True,
                              fontSize=10,fromLang='fr',qrEnabled=False).items():
            self.c.setSetting(key,value)
        self.c.setSetting('genre','salsa')
        self.c.setSetting('offset',-80)
        tracks=copy.deepcopy(self.c.track_settings)
        for style,recipe in GENRE_VISUAL_PRESETS.items():
            self.assertEqual(validate(recipe['settings']),recipe['settings'])
            self.c.applyGenreStyle(style)
            self.assertEqual(self.c.settings['mood'],recipe['settings']['mood'])
            self.assertEqual(self.c.base_settings['font'],recipe['settings']['font'])
            self.assertEqual([s['key'] for s in self.c.genreStyles if s['active']],[style])
            for key,value in dict(source='loopback',threshold=2.25,timing='bars',reducedMotion=True,
                                  fontSize=10,fromLang='fr',qrEnabled=False).items():
                self.assertEqual(self.c.settings[key],value)
            self.assertEqual(self.c.track_settings,tracks)

    def test_genre_styles_switch_without_leaking_previous_effects(self):
        self.c.applyGenreStyle('reggaeton')
        self.assertTrue(self.c.settings['spectrum'])
        self.assertEqual(self.c.settings['strength'],100)
        self.c.applyGenreStyle('bachata')
        self.assertTrue(self.c.view['chill'])
        self.assertFalse(self.c.settings['spectrum'])
        self.assertFalse(self.c.settings['dropFx'])
        self.c.applyGenreStyle('salsa')
        self.assertFalse(self.c.view['chill'])
        self.assertTrue(self.c.settings['dropFx'])
        previous=copy.deepcopy(self.c.settings)
        self.c.applyGenreStyle('unknown')
        self.assertEqual(self.c.settings,previous)


if __name__ == '__main__':
    unittest.main()
