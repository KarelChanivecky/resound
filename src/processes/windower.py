import threading

import numpy as np
import scipy.signal.windows as scipy_win

from interfaces.process import Process
from sound_sample import SoundSample
from windowed_sample import WindowedSample

DEFAULT_FFT_SIZE = 2048


def _normalize_32b(amplitudes):
    """Scale samples to fill the 32-bit signed range."""
    max_amp = max(amplitudes.max(), abs(amplitudes.min()))
    half_range = (2 ** 32 - 1) // 2
    return (amplitudes / max_amp) * half_range


class Windower(Process):
    """
    Crops a SoundSample to fft_size, normalizes to 32-bit range, and applies
    a window function to reduce spectral leakage.

    Parameters can be updated at runtime via set_fft_size() and set_window().
    Both setters are thread-safe for use alongside a running pipeline thread.
    """

    def __init__(self, fft_size=DEFAULT_FFT_SIZE, window=None):
        self.__fft_size = fft_size
        self.__window = window if window is not None else scipy_win.hann(fft_size, sym=False)
        self.__lock = threading.Lock()

    def set_fft_size(self, fft_size: int) -> None:
        """Set FFT size and regenerate a matching Hann window."""
        with self.__lock:
            self.__fft_size = fft_size
            self.__window = scipy_win.hann(fft_size, sym=False)

    def set_window(self, window: np.ndarray) -> None:
        """Set a custom window; fft_size is inferred from its length."""
        with self.__lock:
            self.__window = np.asarray(window, dtype=np.float64)
            self.__fft_size = len(self.__window)

    def run(self, sound_sample: SoundSample = None) -> WindowedSample:
        with self.__lock:
            fft_size = self.__fft_size
            window = self.__window

        samples = sound_sample.get_samples()
        cropped = samples[:fft_size]
        normalized = _normalize_32b(cropped)
        windowed = normalized * window
        return WindowedSample(windowed, fft_size, sound_sample.get_sample_rate())
