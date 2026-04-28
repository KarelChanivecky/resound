import unittest

import numpy as np

from processes.windower import Windower
from processes.spectrum_analyzer import SpectrumAnalyzer
from processes.peak_detector import PeakDetector
from processes.frequency_interpolator import FrequencyInterpolator, _gaussian_interpolation
from sound_sample import SoundSample
from detected_peaks import DetectedPeaks

_SAMPLE_RATE = 44100
_N = 4096


def _chain(freq=440.0):
    t = np.arange(_N) / _SAMPLE_RATE
    samples = (np.sin(2 * np.pi * freq * t) * (2 ** 31 - 1)).astype(np.int32)
    sound = SoundSample(_SAMPLE_RATE, _N / _SAMPLE_RATE, samples)
    windowed = Windower(fft_size=_N).run(sound)
    spectrum = SpectrumAnalyzer().run(windowed)
    return PeakDetector().run(spectrum)


class TestFrequencyInterpolator(unittest.TestCase):

    def test_440hz_within_tolerance(self):
        peaks = _chain(440.0)
        result = FrequencyInterpolator().run(peaks)
        self.assertAlmostEqual(result, 440.0, delta=2.0)

    def test_no_peaks_returns_negative_one(self):
        amps = np.ones(64)
        no_peaks = DetectedPeaks(amps, [-1], freq_resolution=10.0)
        result = FrequencyInterpolator().run(no_peaks)
        self.assertEqual(result, -1)

    def test_various_frequencies(self):
        for freq in [220.0, 330.0, 880.0]:
            with self.subTest(freq=freq):
                peaks = _chain(freq)
                result = FrequencyInterpolator().run(peaks)
                self.assertAlmostEqual(result, freq, delta=2.0)


class TestGaussianInterpolation(unittest.TestCase):

    def test_bin_zero_returns_negative_one(self):
        self.assertEqual(_gaussian_interpolation(np.ones(16), 0, 10.0), -1)

    def test_last_bin_returns_negative_one(self):
        self.assertEqual(_gaussian_interpolation(np.ones(16), 15, 10.0), -1)

    def test_interior_bin_returns_positive_frequency(self):
        amps = np.array([1.0, 2.0, 4.0, 2.0, 1.0])
        result = _gaussian_interpolation(amps, 2, 10.0)
        self.assertGreater(result, 0)
