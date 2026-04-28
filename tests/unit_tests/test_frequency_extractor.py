import threading
import unittest

import numpy as np
import scipy.signal.windows as scipy_win

from processes.frequency_extractor import FrequencyExtractor
from processes.frequency_interpolator import _gaussian_interpolation
from sound_sample import SoundSample

_SAMPLE_RATE = 44100
_N = 4096


def _sine_sample(freq=440.0, n=_N, sample_rate=_SAMPLE_RATE):
    t = np.arange(n) / sample_rate
    samples = (np.sin(2 * np.pi * freq * t) * (2 ** 31 - 1)).astype(np.int32)
    return SoundSample(sample_rate, n / sample_rate, samples)


class TestFrequencyExtractor(unittest.TestCase):

    def test_extracts_known_frequency(self):
        sample = _sine_sample(440.0)
        freq = FrequencyExtractor(fft_size=_N).run(sample)
        self.assertAlmostEqual(freq, 440.0, delta=2.0)

    def test_no_peaks_returns_negative_one(self):
        sample = _sine_sample(440.0)
        freq = FrequencyExtractor(fft_size=_N, target_z_score=1000.0).run(sample)
        self.assertEqual(freq, -1)

    def test_custom_fft_size(self):
        sample = _sine_sample(440.0, n=8192)
        freq = FrequencyExtractor(fft_size=4096).run(sample)
        self.assertAlmostEqual(freq, 440.0, delta=2.0)

    def test_gaussian_interpolation_at_bin_zero_returns_negative_one(self):
        amps = np.ones(16)
        result = _gaussian_interpolation(amps, 0, 10.0)
        self.assertEqual(result, -1)

    def test_gaussian_interpolation_at_last_bin_returns_negative_one(self):
        amps = np.ones(16)
        result = _gaussian_interpolation(amps, 15, 10.0)
        self.assertEqual(result, -1)


class TestFrequencyExtractorSetters(unittest.TestCase):

    def test_set_fft_size_updates_result(self):
        sample = _sine_sample(440.0, n=8192)
        fe = FrequencyExtractor(fft_size=_N)
        fe.set_fft_size(8192)
        freq = fe.run(sample)
        self.assertAlmostEqual(freq, 440.0, delta=2.0)

    def test_set_fft_size_regenerates_window(self):
        fe = FrequencyExtractor(fft_size=_N)
        fe.set_fft_size(512)
        sample = _sine_sample(440.0, n=512)
        freq = fe.run(sample)
        self.assertAlmostEqual(freq, 440.0, delta=2.0)

    def test_set_window_accepts_custom_array(self):
        fe = FrequencyExtractor(fft_size=_N)
        fe.set_window(scipy_win.blackman(_N, sym=False))
        freq = fe.run(_sine_sample(440.0))
        self.assertAlmostEqual(freq, 440.0, delta=2.0)

    def test_set_window_infers_fft_size(self):
        fe = FrequencyExtractor(fft_size=_N)
        new_window = scipy_win.hann(2048, sym=False)
        fe.set_window(new_window)
        sample = _sine_sample(440.0, n=4096)
        freq = fe.run(sample)
        self.assertAlmostEqual(freq, 440.0, delta=2.0)

    def test_set_target_z_score_high_suppresses_peaks(self):
        fe = FrequencyExtractor(fft_size=_N)
        fe.set_target_z_score(1000.0)
        freq = fe.run(_sine_sample(440.0))
        self.assertEqual(freq, -1)

    def test_set_target_z_score_low_finds_peak(self):
        fe = FrequencyExtractor(fft_size=_N, target_z_score=1000.0)
        fe.set_target_z_score(3.0)
        freq = fe.run(_sine_sample(440.0))
        self.assertAlmostEqual(freq, 440.0, delta=2.0)

    def test_set_norm_ortho_still_detects_frequency(self):
        fe = FrequencyExtractor(fft_size=_N)
        fe.set_norm('ortho')
        freq = fe.run(_sine_sample(440.0))
        self.assertAlmostEqual(freq, 440.0, delta=2.0)

    def test_set_norm_none_still_detects_frequency(self):
        fe = FrequencyExtractor(fft_size=_N, norm='ortho')
        fe.set_norm(None)
        freq = fe.run(_sine_sample(440.0))
        self.assertAlmostEqual(freq, 440.0, delta=2.0)

    def test_concurrent_set_fft_size_does_not_raise(self):
        fe = FrequencyExtractor(fft_size=_N)
        sample = _sine_sample(440.0, n=8192)
        errors = []

        def setter_loop():
            for size in [_N, 2048, _N, 2048]:
                try:
                    fe.set_fft_size(size)
                except Exception as exc:
                    errors.append(exc)

        def runner_loop():
            for _ in range(8):
                try:
                    fe.run(sample)
                except Exception as exc:
                    errors.append(exc)

        threads = [threading.Thread(target=setter_loop),
                   threading.Thread(target=runner_loop)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
