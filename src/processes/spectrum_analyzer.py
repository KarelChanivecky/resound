import threading

import numpy as np

from interfaces.process import Process
from data_models.spectrum import Spectrum
from data_models.windowed_sample import WindowedSample


class SpectrumAnalyzer(Process):
    """
    Converts a WindowedSample into a real-valued amplitude Spectrum via rfft.

    The DC bin is kept as-is; all other bins are doubled to account for the
    energy in the discarded negative-frequency mirror.  freq_resolution
    (Hz per bin) is computed from the sample rate and fft_size carried in the
    WindowedSample.

    The norm parameter can be updated at runtime via set_norm().
    """

    def __init__(self, norm=None):
        self.__norm = norm
        self.__lock = threading.Lock()

    def set_norm(self, norm) -> None:
        """Set the numpy.fft normalisation mode ('backward', 'ortho', 'forward', or None)."""
        with self.__lock:
            self.__norm = norm

    def run(self, windowed_sample: WindowedSample = None) -> Spectrum:
        with self.__lock:
            norm = self.__norm

        complex_amps = np.fft.rfft(windowed_sample.samples,
                                   n=windowed_sample.fft_size,
                                   norm=norm)
        complex_amps[1:] = 2 * complex_amps[1:]
        amplitudes = np.abs(complex_amps)
        freq_resolution = windowed_sample.sample_rate / windowed_sample.fft_size
        return Spectrum(amplitudes, freq_resolution, windowed_sample)
