import threading

from interfaces.process import Process
from spectrum import Spectrum

DEFAULT_EXPONENT = 1.0


class AmplitudeExponentiator(Process):
    """
    Exponentiates each amplitude bin to compress or expand spectral dynamic range.

    Given an exponent e, computes amplitudes ** e then rescales so that the peak
    amplitude remains at its original magnitude.  This sharpens peaks when e > 1
    (expanding contrast) and softens them when 0 < e < 1 (compressing contrast),
    without shifting the absolute scale that downstream z-score thresholding sees.

    The exponent can be updated at runtime via set_exponent().
    """

    def __init__(self, exponent: float = DEFAULT_EXPONENT):
        self.__exponent = exponent
        self.__lock = threading.Lock()

    def set_exponent(self, exponent: float) -> None:
        """Thread-safe setter. Accepts any positive float."""
        with self.__lock:
            self.__exponent = exponent

    def run(self, spectrum: Spectrum = None) -> Spectrum:
        with self.__lock:
            exponent = self.__exponent

        if exponent == 1.0:
            return spectrum

        original_max = spectrum.amplitudes.max()
        amplitudes = spectrum.amplitudes ** exponent
        new_max = amplitudes.max()

        if new_max == 0:
            return spectrum

        rescaled = amplitudes / new_max * original_max
        return Spectrum(rescaled, spectrum.freq_resolution, spectrum.windowed_sample)
