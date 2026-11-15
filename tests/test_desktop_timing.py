import unittest

from desktop.timing import PlaybackClock, PulseScheduler, word_groups, PROFILES


class NativeTimingTests(unittest.TestCase):
    def test_midrange_never_flashes_learns_or_blocks_next_bass(self):
        for genre in PROFILES:
            scheduler = PulseScheduler()
            for i in range(1, 101):
                scheduler.ingest(dict(sequence=i, hit=True, age_ms=0,
                                      bands=[0, 12, 0], level=.8), i/10, genre=genre)
                self.assertIsNone(scheduler.due(i/10))
            self.assertEqual(len(scheduler.adaptation.events), 0)
            scheduler.ingest(dict(sequence=101, hit=True, age_ms=0,
                                  bands=[8, 0, 0], level=.2), 10.02, genre=genre)
            self.assertIsNotNone(scheduler.due(10.02))

    def test_bass_treble_gains_and_mute(self):
        for bands, bass, treble, expected in (
            ([8, 12, 0], 1, 0, True), ([0, 12, 8], 0, 1, True),
            ([8, 12, 0], 0, 1, False), ([0, 12, 8], 1, 0, False),
            ([12, 12, 12], 0, 0, False),
            ([1, 0, 0], 1, 1, False), ([1, 0, 0], 2, 1, True),
            ([0, 0, 1.5], 1, 1, False), ([0, 0, 1.5], 1, 2, True)):
            scheduler = PulseScheduler()
            scheduler.ingest(dict(sequence=1, hit=True, age_ms=0, bands=bands),
                             1, bass_gain=bass, treble_gain=treble)
            self.assertEqual(scheduler.due(1) is not None, expected)

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

    def test_busy_background_rejected_but_strong_attacks_stay_in_phase(self):
        auto, fixed = PulseScheduler(), PulseScheduler()
        counts = {"auto_weak":0,"fixed_weak":0,"auto_strong":0,"fixed_strong":0}
        for i in range(1,161):
            now=i*.1
            strong=i%5 == 0
            packet=dict(sequence=i,hit=True,age_ms=20,bands=[8 if strong else 2.5,0,0],level=.1)
            for name,scheduler in (("auto",auto),("fixed",fixed)):
                scheduler.ingest(packet,now,adaptive=name=='auto')
                pulse=scheduler.due(now)
                if pulse and now>8:
                    counts[name+('_strong' if strong else '_weak')]+=1
                    self.assertAlmostEqual(pulse['age'],.02)
        self.assertGreater(counts['fixed_weak'],20)
        self.assertEqual(counts['auto_weak'],0)
        self.assertEqual(counts['auto_strong'],16)
        self.assertGreater(auto.effective_threshold,2.9)
        self.assertEqual(fixed.effective_threshold,1.75)

    def test_loud_sparse_and_fast_even_percussion_do_not_raise_gate(self):
        for interval,score in ((.5,12),(.16,2.5)):
            scheduler=PulseScheduler()
            hits=0
            for i in range(1,81):
                now=i*interval
                scheduler.ingest(dict(sequence=i,hit=True,age_ms=0,bands=[score,0,0],level=.8),now)
                hits+=bool(scheduler.due(now))
            self.assertEqual(hits,80)
            self.assertEqual(scheduler.effective_threshold,1.75)

    def test_adaptation_recovers_and_resets_on_track_pause_and_silence(self):
        scheduler=PulseScheduler()
        for i in range(1,101):
            scheduler.ingest(dict(sequence=i,hit=True,age_ms=0,bands=[8 if i%5==0 else 2.5,0,0],level=.1),i*.1)
            scheduler.due(i*.1)
        noisy=scheduler.effective_threshold
        self.assertGreater(noisy,2.9)
        # Non-hit heartbeats let old noise expire even without new attacks.
        for i in range(101,161):
            scheduler.ingest(dict(sequence=i,hit=False,age_ms=0,bands=[0,0,0],level=.1),10+(i-100)*.25)
        self.assertLess(scheduler.effective_threshold,2)
        scheduler.reset(26)
        self.assertEqual(scheduler.adaptation.threshold(1.75),1.75)
        self.assertTrue(scheduler.adaptation.learning)
        for i in range(161,261):
            scheduler.ingest(dict(sequence=i,hit=True,age_ms=0,bands=[8 if i%5==0 else 2.5,0,0],level=.1),26+(i-160)*.1)
            scheduler.due(26+(i-160)*.1)
        self.assertGreater(scheduler.effective_threshold,2.9)
        for i in range(261,267):
            scheduler.ingest(dict(sequence=i,hit=False,age_ms=0,bands=[0,0,0],level=0),36+(i-260)*.25)
        self.assertEqual(scheduler.adaptation.threshold(1.75),1.75)
        self.assertIsNone(scheduler.due(38))

    def test_stale_and_duplicate_candidates_do_not_train_adaptation(self):
        scheduler=PulseScheduler()
        for i in range(1,101):
            scheduler.ingest(dict(sequence=i,hit=True,age_ms=250,bands=[8,0,0],level=.2),i*.1)
        self.assertEqual(len(scheduler.adaptation.events),0)
        scheduler.ingest(dict(sequence=101,hit=True,age_ms=0,bands=[8,0,0],level=.2),11)
        for i in range(20):
            scheduler.ingest(dict(sequence=101,hit=True,age_ms=0,bands=[8,0,0],level=.2),11+i*.1)
        self.assertEqual(len(scheduler.adaptation.events),1)

    def test_manual_base_and_disable_take_effect_without_forgetting_noise(self):
        scheduler=PulseScheduler()
        for i in range(1,101):
            scheduler.ingest(dict(sequence=i,hit=True,age_ms=0,bands=[8 if i%5==0 else 2.5,0,0],level=.1),i*.1)
            scheduler.due(i*.1)
        extra=scheduler.adaptation.extra
        scheduler.reset(10,reset_adaptation=False)
        self.assertEqual(scheduler.adaptation.extra,extra)
        self.assertAlmostEqual(scheduler.adaptation.threshold(2.75)-scheduler.adaptation.threshold(1.75),1)
        scheduler.ingest(dict(sequence=101,hit=True,age_ms=0,bands=[2.5,0,0],level=.1),10.3,adaptive=False)
        self.assertIsNotNone(scheduler.due(10.3))
        self.assertEqual(scheduler.effective_threshold,1.75)

    def test_dense_stronger_clutter_also_adapts(self):
        scheduler=PulseScheduler()
        weak_hits=strong_hits=0
        for i in range(1,161):
            strong=i%5==0
            now=i*.1
            scheduler.ingest(dict(sequence=i,hit=True,age_ms=0,bands=[12 if strong else 6,0,0],level=.4),now)
            pulse=scheduler.due(now)
            if pulse and now>8:
                if strong:
                    strong_hits+=1
                else:
                    weak_hits+=1
        self.assertEqual(weak_hits,0)
        self.assertEqual(strong_hits,16)


if __name__ == "__main__":
    unittest.main()
