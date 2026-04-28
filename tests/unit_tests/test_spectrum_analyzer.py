import unittest

import numpy as np

from processes.windower import Windower
from processes.spectrum_analyzer import SpectrumAnalyzer
from sound_sample import SoundSample
from spectrum import Spectrum

_SAMPLE_RATE = 44100
_N = 4096


def _windowed(freq=440.0, n=_N, sample_rate=_SAMPLE_RATE, fft_size=_N):
    t = np.arange(n) / sample_rate
    samples = (np.sin(2 * np.pi * freq * t) * (2 ** 31 - 1)).astype(np.int32)
    sound = SoundSample(sample_rate, n / sample_rate, samples)
    return Windower(fft_size=fft_size).run(sound)


class TestSpectrumAnalyzer(unittest.TestCase):

    def test_output_is_spectrum(self):
        result = SpectrumAnalyzer().run(_windowed())
        self.assertIsInstance(result, Spectrum)

    def test_freq_resolution(self):
        result = SpectrumAnalyzer().run(_windowed())
        self.assertAlmostEqual(result.freq_resolution, _SAMPLE_RATE / _N)

    def test_amplitudes_are_non_negative(self):
        result = SpectrumAnalyzer().run(_windowed())
        self.assertTrue(np.all(result.amplitudes >= 0))

    def test_peak_bin_near_440hz(self):
        result = SpectrumAnalyzer().run(_windowed(440.0))
        peak_bin = int(np.argmax(result.amplitudes))
        peak_freq = peak_bin * result.freq_resolution
        self.assertAlmostEqual(peak_freq, 440.0, delta=result.freq_resolution * 1.5)

    def test_set_norm_ortho_changes_amplitudes(self):
        ws = _windowed()
        default_result = SpectrumAnalyzer(norm=None).run(ws)
        ortho_result = SpectrumAnalyzer(norm='ortho').run(ws)
        self.assertFalse(np.allclose(default_result.amplitudes, ortho_result.amplitudes))

    def test_set_norm_updates_at_runtime(self):
        ws = _windowed()
        sa = SpectrumAnalyzer(norm=None)
        default_max = sa.run(ws).amplitudes.max()
        sa.set_norm('ortho')
        ortho_max = sa.run(ws).amplitudes.max()
        self.assertNotAlmostEqual(float(default_max), float(ortho_max), places=3)
