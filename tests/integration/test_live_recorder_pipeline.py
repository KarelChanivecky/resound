import os
import unittest

import numpy as np
import scipy.signal.windows as scipy_win

from processes.recorder import Recorder, _SOUNDDEVICE_AVAILABLE
from processes.spectrum_analyzer import SpectrumAnalyzer
from processes.windower import Windower

_HARDWARE_AVAILABLE = bool(os.environ.get('HARDWARE_TESTS'))
_TARGET_FREQUENCY_MAX = 2500
_SAMPLE_DURATION = 0.05
_FFT_SIZE = 2048
_SAMPLE_RATE = _TARGET_FREQUENCY_MAX * 2
_STEP_FRAMES = int(_SAMPLE_RATE * _SAMPLE_DURATION)


@unittest.skipUnless(_SOUNDDEVICE_AVAILABLE, 'sounddevice requires PortAudio (libportaudio2)')
@unittest.skipUnless(_HARDWARE_AVAILABLE, 'set HARDWARE_TESTS=1 to run microphone tests')
class TestLiveRecorderPipeline(unittest.TestCase):

    def _make_recorder(self):
        return Recorder(_TARGET_FREQUENCY_MAX, _SAMPLE_DURATION, _FFT_SIZE)

    def _successive_samples(self):
        recorder = self._make_recorder()
        first = recorder.run()
        second = recorder.run()
        self._skip_if_silent(first.get_samples(), second.get_samples())
        return first, second

    def _skip_if_silent(self, *sample_arrays):
        combined = np.concatenate(sample_arrays)
        if np.max(np.abs(combined)) == 0:
            self.skipTest('microphone input is silent')

    def test_recorder_successive_windows_are_different(self):
        first, second = self._successive_samples()

        self.assertFalse(np.array_equal(first.get_samples(), second.get_samples()))

    def test_recorder_successive_windows_slide_by_step_duration(self):
        first, second = self._successive_samples()

        np.testing.assert_array_equal(
            first.get_samples()[_STEP_FRAMES:],
            second.get_samples()[:-_STEP_FRAMES],
        )

    def test_windower_successive_raw_samples_are_different(self):
        first, second = self._successive_samples()
        windower = Windower(
            fft_size=_FFT_SIZE,
            window=scipy_win.hann(_FFT_SIZE, sym=False),
        )

        first_windowed = windower.run(first)
        second_windowed = windower.run(second)

        self.assertFalse(np.array_equal(first_windowed.raw_samples,
                                        second_windowed.raw_samples))

    def test_windower_successive_windowed_samples_are_different(self):
        first, second = self._successive_samples()
        windower = Windower(
            fft_size=_FFT_SIZE,
            window=scipy_win.hann(_FFT_SIZE, sym=False),
        )

        first_windowed = windower.run(first)
        second_windowed = windower.run(second)

        self.assertFalse(np.array_equal(first_windowed.samples,
                                        second_windowed.samples))

    def test_spectrum_successive_amplitudes_are_different_before_peak_extraction(self):
        first, second = self._successive_samples()
        windower = Windower(
            fft_size=_FFT_SIZE,
            window=scipy_win.hann(_FFT_SIZE, sym=False),
        )
        analyzer = SpectrumAnalyzer()

        first_spectrum = analyzer.run(windower.run(first))
        second_spectrum = analyzer.run(windower.run(second))

        self.assertFalse(np.array_equal(first_spectrum.amplitudes,
                                        second_spectrum.amplitudes))
