"""
Extracts the fundamental frequency from a SoundSample by chaining four stages:

    1. Windower        — crop, normalize, apply window function
    2. SpectrumAnalyzer — rfft → real amplitude spectrum
    3. PeakDetector    — z-score threshold + cluster peak selection
    4. FrequencyInterpolator — Gaussian sub-bin interpolation

See each stage's module for algorithmic details.

Bibliography:
    Improving FFT resolution, J. Marsar. 2015.
    http://www.add.ece.ufl.edu/4511/references/ImprovingFFTResoltuion.pdf

    Improving FFT frequency measurement resolution by parabolic and gaussian interpolation,
    M. Gasior, J.L. Gonzalez. 2004.
    https://mgasior.web.cern.ch/pap/FFT_resol_note.pdf
"""

import scipy.signal.windows as scipy_win

from interfaces.process import Process
from processes.frequency_interpolator import FrequencyInterpolator
from processes.peak_detector import PeakDetector, DEFAULT_TARGET_Z_SCORE
from processes.spectrum_analyzer import SpectrumAnalyzer
from processes.windower import Windower, DEFAULT_FFT_SIZE


class FrequencyExtractor(Process):
    """
    Facade that chains Windower → SpectrumAnalyzer → PeakDetector → FrequencyInterpolator.

    Accepts the same keyword arguments and exposes the same set_* interface as before,
    delegating each setter to the appropriate sub-stage.  Each sub-stage is individually
    thread-safe, so no additional lock is needed here.
    """

    def __init__(self, **kwargs) -> None:
        fft_size = kwargs.get('fft_size', DEFAULT_FFT_SIZE)
        target_z_score = kwargs.get('target_z_score', DEFAULT_TARGET_Z_SCORE)
        norm = kwargs.get('norm', None)
        window = kwargs.get('window', scipy_win.hann(fft_size, sym=False))

        self._windower = Windower(fft_size=fft_size, window=window)
        self._spectrum_analyzer = SpectrumAnalyzer(norm=norm)
        self._peak_detector = PeakDetector(target_z_score=target_z_score)
        self._interpolator = FrequencyInterpolator()

    # ------------------------------------------------------------------ #
    # Live parameter setters — delegate to the owning sub-stage           #
    # ------------------------------------------------------------------ #

    def set_fft_size(self, fft_size: int) -> None:
        self._windower.set_fft_size(fft_size)

    def set_window(self, window) -> None:
        self._windower.set_window(window)

    def set_target_z_score(self, z_score: float) -> None:
        self._peak_detector.set_target_z_score(z_score)

    def set_norm(self, norm) -> None:
        self._spectrum_analyzer.set_norm(norm)

    # ------------------------------------------------------------------ #
    # Process interface                                                    #
    # ------------------------------------------------------------------ #

    def run(self, sound_sample=None):
        windowed = self._windower.run(sound_sample)
        spectrum = self._spectrum_analyzer.run(windowed)
        peaks = self._peak_detector.run(spectrum)
        return self._interpolator.run(peaks)
