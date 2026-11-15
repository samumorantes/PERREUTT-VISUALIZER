import unittest
import numpy as np
from percussion import PercussionDetector, classify_genres


class PercussionTests(unittest.TestCase):
    RATE = 48000
    HOP = 512

    def analyze(self, signal):
        detector = PercussionDetector(self.RATE, self.HOP)
        results = []
        for start in range(0, len(signal) - self.HOP + 1, self.HOP):
            results.append(detector.process(signal[start:start+self.HOP], (start+self.HOP/2)/self.RATE))
        return results

    def drums(self, seconds, beats):
        signal = np.zeros(int(seconds*self.RATE))
        rng = np.random.default_rng(42)
        t = np.arange(int(.065*self.RATE))/self.RATE
        hit = (.7*np.sin(2*np.pi*90*t) + .25*rng.normal(size=len(t))) * np.exp(-t*65)
        for at in beats:
            index = int(at*self.RATE)
            signal[index:index+len(hit)] += hit[:len(signal)-index]
        return signal

    def test_silence_and_sustained_tone_are_not_beats(self):
        silence = np.zeros(self.RATE*5)
        self.assertFalse(any(r['hit'] for r in self.analyze(silence)))
        tone = .3*np.sin(2*np.pi*440*np.arange(self.RATE*5)/self.RATE)
        results = self.analyze(tone)
        self.assertFalse(any(r['hit'] for r in results[100:]))

    def test_known_beats_keep_phase_and_estimate_tempo(self):
        for bpm in (90, 120, 150):
            beats = np.arange(.7, 10, 60/bpm)
            results = self.analyze(self.drums(11, beats))
            hits = [r['at'] for r in results if r['hit']]
            for at in beats:
                self.assertLess(min(abs(at-h) for h in hits), .06)
            self.assertLessEqual(len(hits), len(beats)+2)
            estimate = [r['bpm'] for r in results if r['bpm']][-1]
            self.assertLess(abs(estimate-bpm), 4)

    def test_syncopation_is_not_quantized_and_silence_stops(self):
        beats = [.7, 1.2, 1.575, 1.95, 2.2, 2.7, 3.075, 3.45, 3.7]
        signal = self.drums(6, beats)
        # Anti-phase stereo must still yield hits.
        results = self.analyze(np.column_stack((signal, -signal)))
        hits = [r['at'] for r in results if r['hit']]
        for at in beats:
            self.assertLess(min(abs(at-h) for h in hits), .06)
        self.assertFalse(any(r['hit'] for r in results if r['at'] > 4))
        self.assertIsNone(results[-1]['bpm'])
        self.assertFalse(any(r['drop_candidate'] for r in results))

    def test_genres_use_evidence_and_allow_mixtures(self):
        self.assertEqual(classify_genres(['reggaetón', 'latin pop'])['genre'], 'reggaeton')
        self.assertEqual(classify_genres(['bachata', 'salsa'])['genre'], 'mixed')
        self.assertEqual(classify_genres(['latin', 'urban'])['genre'], 'unknown')
        self.assertEqual(classify_genres([])['confidence'], 'unknown')
        self.assertEqual(classify_genres(['salsa'])['confidence'], 'suggested')


if __name__ == '__main__':
    unittest.main()
