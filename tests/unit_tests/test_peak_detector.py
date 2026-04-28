import unittest

import numpy as np

from processes.windower import Windower
from processes.spectrum_analyzer import SpectrumAnalyzer
from processes.peak_detector import PeakDetector
from sound_sample import SoundSample
from spectrum import Spectrum
from detected_peaks import DetectedPeaks

_SAMPLE_RATE = 44100
_N = 4096


def _spectrum(freq=440.0, n=_N, sample_rate=_SAMPLE_RATE):
    t = np.arange(n) / sample_rate
    samples = (np.sin(2 * np.pi * freq * t) * (2 ** 31 - 1)).astype(np.int32)
    sound = SoundSample(sample_rate, n / sample_rate, samples)
    windowed = Windower(fft_size=n).run(sound)
    return SpectrumAnalyzer().run(windowed)


class TestPeakDetector(unittest.TestCase):

    def test_output_is_detected_peaks(self):
        result = PeakDetector().run(_spectrum())
        self.assertIsInstance(result, DetectedPeaks)

    def test_freq_resolution_carried_through(self):
        spec = _spectrum()
        result = PeakDetector().run(spec)
        self.assertEqual(result.freq_resolution, spec.freq_resolution)

    def test_no_signal_returns_minus_one_bin(self):
        # Uniform spectrum — no statistical outliers — nothing clears the threshold.
        uniform = Spectrum(np.ones(100), freq_resolution=10.0)
        result = PeakDetector(target_z_score=3.0).run(uniform)
        self.assertEqual(result.peak_bins, [-1])

    def test_440hz_sine_detected(self):
        spec = _spectrum(440.0)
        result = PeakDetector().run(spec)
        self.assertNotEqual(result.peak_bins, [-1])
        peak_freq = result.peak_bins[0] * spec.freq_resolution
        self.assertAlmostEqual(peak_freq, 440.0, delta=spec.freq_resolution * 2)

    def test_high_zscore_suppresses_peaks(self):
        result = PeakDetector(target_z_score=1000.0).run(_spectrum())
        self.assertEqual(result.peak_bins, [-1])

    def test_set_target_z_score_low_finds_peaks(self):
        pd = PeakDetector(target_z_score=1000.0)
        pd.set_target_z_score(3.0)
        result = pd.run(_spectrum(440.0))
        self.assertNotEqual(result.peak_bins, [-1])

    def test_cluster_peak_is_highest_amplitude_bin(self):
        spec = _spectrum(440.0)
        result = PeakDetector().run(spec)
        for bin_idx in result.peak_bins:
            if bin_idx == -1:
                continue
            # Neighbours (if they exist) should not be higher than the representative bin.
            if bin_idx > 0:
                self.assertGreaterEqual(spec.amplitudes[bin_idx],
                                        spec.amplitudes[bin_idx - 1])
            if bin_idx < len(spec.amplitudes) - 1:
                self.assertGreaterEqual(spec.amplitudes[bin_idx],
                                        spec.amplitudes[bin_idx + 1])
