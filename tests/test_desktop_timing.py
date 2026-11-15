import unittest

from desktop.timing import PlaybackClock, PulseScheduler, word_groups


class NativeTimingTests(unittest.TestCase):
    def test_pause_and_seek_reset_clock(self):
        now = [10.0]
        clock = PlaybackClock(lambda: now[0])
        self.assertTrue(clock.update(30, True, "song"))
        now[0] += .5
        self.assertAlmostEqual(clock.read(), 30.5)
        self.assertTrue(clock.update(30.5, False, "song"))
        now[0] += 2
        self.assertAlmostEqual(clock.read(), 30.5)
        self.assertTrue(clock.update(80, True, "song"))
        self.assertEqual(clock.read(), 80)

    def test_threshold_stale_packet_and_strong_accent(self):
        scheduler = PulseScheduler()
        scheduler.reset(0)
        def packet(seq, score, age=0):
            return dict(sequence=seq, hit=True, age_ms=age, bands=[score, 0, 0])
        scheduler.ingest(packet(1, 1.74), 1)
        self.assertIsNone(scheduler.due(1))
        scheduler.ingest(packet(2, 9, 250), 2)
        self.assertIsNone(scheduler.due(2))
        scheduler.ingest(packet(3, 4.74), 3, mode="bars")
        self.assertIsNone(scheduler.due(3))
        scheduler.ingest(packet(4, 4.76), 4, mode="bars")
        self.assertIsNotNone(scheduler.due(4))

    def test_delayed_pulse_and_pause_clear(self):
        scheduler = PulseScheduler()
        scheduler.reset(0)
        scheduler.ingest(dict(sequence=1, hit=True, age_ms=20, bands=[5,0,0]), 1, offset=-100)
        self.assertIsNone(scheduler.due(1.05))
        self.assertAlmostEqual(scheduler.due(1.09)["age"], .01)
        scheduler.ingest(dict(sequence=2, hit=True, age_ms=0, bands=[5,0,0]), 2, offset=-100)
        scheduler.reset(2.01)
        self.assertIsNone(scheduler.due(2.2))

    def test_syllables_stay_inside_their_word(self):
        groups = word_groups([dict(text="Bai", t=1, end=1.2),
                              dict(text="la", part=True, t=1.2, end=1.5),
                              dict(text="ya", t=2, end=2.3)])
        self.assertEqual([g["text"] for g in groups], ["Baila", "ya"])
        self.assertEqual(groups[0]["syllables"][1]["t"], 1.2)


if __name__ == "__main__":
    unittest.main()
