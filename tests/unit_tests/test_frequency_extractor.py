import unittest

import numpy as np

from processes.frequency_extractor import FrequencyExtractor, _gaussian_interpolation
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
