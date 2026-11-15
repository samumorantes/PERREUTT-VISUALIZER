import copy
import tempfile
import time
import unittest

from PySide6.QtCore import QCoreApplication
from desktop.controller import Controller


class NativeTransitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.c = Controller(self.tmp.name, smoke=True)
        self.c.timer.stop()
        self.c.tick()
        self.c.set_render_displays(['main', 'translation'])

    def tearDown(self):
        self.c.shutdown()
        self.c.deleteLater()
        self.tmp.cleanup()

    def state(self, track='new'):
        data = self.c.smoke_state()
        data['track'].update(id=track, name=track)
        data['progress_ms'] = 2000
        self.c.receive(dict(kind='state', data=data, received_at=time.monotonic()))

    def ack(self, display, phase, serial=None):
        self.c.transitionFrame(display, self.c.view['transitionSerial'] if serial is None else serial, phase)

    def test_loading_preserves_scene_and_both_windows_form_render_barrier(self):
        before = copy.deepcopy(self.c.lyric)
        self.c.receive(dict(kind='loading', track='new'))
        self.c.tick()
        self.assertEqual(self.c.view['title'], 'FIESTA NATIVO')
        self.assertEqual(self.c.lyric, before)
        self.assertFalse(self.c.want_audio.is_set())
        self.state()
        self.ack('main', 'covering')
        self.assertEqual(self.c.clock.track, 'native-smoke')
        self.ack('translation', 'covering')
        self.assertEqual(self.c.clock.track, 'new')
        self.assertEqual(self.c.lyric['text'], 'new')
        self.assertEqual(self.c.view['transitionPhase'], 'painted')
        self.ack('main', 'painted')
        self.assertEqual(self.c.view['transitionPhase'], 'painted')
        self.ack('translation', 'painted')
        self.assertEqual(self.c.view['transitionPhase'], '')

    def test_rapid_skip_rejects_old_render_acknowledgements(self):
        self.state('first')
        old_serial = self.c.view['transitionSerial']
        self.c.receive(dict(kind='loading', track='second'))
        self.state('second')
        for display in ('main', 'translation'):
            self.ack(display, 'covering', old_serial)
        self.assertEqual(self.c.clock.track, 'native-smoke')
        for display in ('main', 'translation'):
            self.ack(display, 'covering')
        self.assertEqual(self.c.clock.track, 'second')

    def test_minimized_window_does_not_hold_barrier_and_clock_stays_current(self):
        self.state()
        self.c.receive(dict(kind='clock', received_at=time.monotonic(),
                            data=dict(track_id='new', progress_ms=5000, is_playing=False)))
        self.ack('main', 'covering')
        self.c.set_render_displays(['main'])
        self.assertEqual(self.c.clock.track, 'new')
        self.assertAlmostEqual(self.c.clock.read(), 5)
        self.ack('main', 'painted')
        self.assertFalse(self.c.view['transitionPhase'])

    def test_errors_release_cover_without_loading_text(self):
        self.c.receive(dict(kind='loading', track='new'))
        self.c.receive(dict(kind='error', text='Network error'))
        self.assertFalse(self.c.view['transitionPhase'])
        self.assertEqual(self.c.view['title'], 'FIESTA NATIVO')
        self.assertEqual(self.c.view['message'], 'Network error')

    def test_reduced_motion_still_has_opaque_swap(self):
        self.c.setSetting('reducedMotion', True)
        self.state()
        self.assertEqual(self.c.view['transitionKind'], 'none')
        self.assertEqual(self.c.clock.track, 'native-smoke')
        self.c.set_render_displays([])
        self.assertEqual(self.c.clock.track, 'new')
        self.assertFalse(self.c.view['transitionPhase'])


if __name__ == '__main__':
    unittest.main()
