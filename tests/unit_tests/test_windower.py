import unittest

import numpy as np
import scipy.signal.windows as scipy_win

from processes.windower import Windower
from sound_sample import SoundSample
from windowed_sample import WindowedSample

_SAMPLE_RATE = 44100
_N = 4096


def _make_sample(n=_N, sample_rate=_SAMPLE_RATE, freq=440.0):
    t = np.arange(n) / sample_rate
    samples = (np.sin(2 * np.pi * freq * t) * (2 ** 31 - 1)).astype(np.int32)
    return SoundSample(sample_rate, n / sample_rate, samples)


class TestWindower(unittest.TestCase):

    def test_output_is_windowed_sample(self):
        result = Windower(fft_size=_N).run(_make_sample())
        self.assertIsInstance(result, WindowedSample)

    def test_samples_cropped_to_fft_size(self):
        result = Windower(fft_size=512).run(_make_sample(n=2048))
        self.assertEqual(len(result.samples), 512)

    def test_fft_size_carried_in_output(self):
        result = Windower(fft_size=512).run(_make_sample(n=2048))
        self.assertEqual(result.fft_size, 512)

    def test_sample_rate_carried_in_output(self):
        result = Windower(fft_size=_N).run(_make_sample(sample_rate=22050))
        self.assertEqual(result.sample_rate, 22050)

    def test_windowing_zeros_first_sample(self):
        # The periodic Hann window (sym=False) sets w[0]=0 exactly.
        result = Windower(fft_size=_N).run(_make_sample())
        self.assertAlmostEqual(float(result.samples[0]), 0.0, delta=1.0)

    def test_set_fft_size_updates_output_length(self):
        w = Windower(fft_size=_N)
        w.set_fft_size(512)
        result = w.run(_make_sample(n=2048))
        self.assertEqual(len(result.samples), 512)
        self.assertEqual(result.fft_size, 512)

    def test_set_window_accepts_custom_array(self):
        w = Windower(fft_size=_N)
        w.set_window(scipy_win.blackman(_N, sym=False))
        result = w.run(_make_sample())
        self.assertEqual(len(result.samples), _N)

    def test_set_window_infers_fft_size(self):
        w = Windower(fft_size=_N)
        w.set_window(scipy_win.hann(1024, sym=False))
        result = w.run(_make_sample(n=_N))
        self.assertEqual(result.fft_size, 1024)
        self.assertEqual(len(result.samples), 1024)
