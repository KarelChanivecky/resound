import threading

import numpy as np

from interfaces.process import Process
from spectrum import Spectrum

DEFAULT_EXPONENT = 1.0

# Maximum exponent applied per iteration.  Each step normalises the values to
# [0, 1] first, so there is no overflow risk, but capping the step at this
# value means the loop runs in bounded iterations and each step performs a
# well-defined "squaring-like" compression rather than one arbitrarily large
# power that would drive almost every bin to machine zero in a single shot.
_MAX_STEP = 2.0


def _iterated_exp(amplitudes: np.ndarray, exponent: float) -> np.ndarray:
    """
    Apply *exponent* to *amplitudes* via iterated normalise-then-exponentiate.

    Algorithm for each iteration:
      1. Normalise the current values to [0, 1] — safe against overflow regardless
         of the step size, since any positive power of a value in [0, 1] stays in
         [0, 1].
      2. Raise to min(remaining_exponent, _MAX_STEP).
      3. Subtract the applied step from the remaining exponent.
    Repeat until the full exponent has been consumed, then rescale the output so
    its peak equals the input peak.
    """
    orig_peak = float(amplitudes.max())
    if orig_peak == 0.0:
        return amplitudes

    result = amplitudes.astype(np.float64)
    remaining = float(exponent)

    while remaining > 1e-12:
        peak = float(result.max())
        if peak > 0.0:
            result = result / peak          # normalise to [0, 1]
        step = min(remaining, _MAX_STEP)
        result = result ** step             # safe: input in [0, 1], output in [0, 1]
        remaining -= step

    # Restore the original amplitude scale so downstream z-score thresholding
    # sees the same absolute range it would without this stage.
    out_peak = float(result.max())
    if out_peak > 0.0:
        result *= orig_peak / out_peak
    return result


class AmplitudeExponentiator(Process):
    """
    Exponentiates each amplitude bin to compress or expand spectral dynamic range.

    Given an exponent e > 1, peaks become relatively stronger against the noise
    floor; e < 1 softens the contrast.  The transformation is applied via
    _iterated_exp so that arbitrarily large exponents are numerically safe.

    The exponent can be updated at runtime via set_exponent().
    """

    def __init__(self, exponent: float = DEFAULT_EXPONENT):
        self.__exponent = float(exponent)
        self.__lock = threading.Lock()

    def set_exponent(self, exponent: float) -> None:
        """Thread-safe setter. Any non-negative float is accepted."""
        with self.__lock:
            self.__exponent = float(exponent)

    def run(self, spectrum: Spectrum = None) -> Spectrum:
        with self.__lock:
            exponent = self.__exponent

        if exponent == 1.0:
            return spectrum

        amplitudes = _iterated_exp(spectrum.amplitudes, exponent)
        return Spectrum(amplitudes, spectrum.freq_resolution, spectrum.windowed_sample)
