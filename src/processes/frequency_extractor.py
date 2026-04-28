"""
This extractor targets frequencies between 16Hz (C0) and 8000Hz (B8)

    Rationale:
    1- The consumer is given an array of samples
    2- The samples are normalized over a 32b range
    3- A Hann window is applied to the samples to improve accuracy, frequency resolution and decrease spectral leakage
    4- An FFT is applied to obtain the frequency spectrum
    5- Bins with outlier(right lobe of amplitude distribution only) amplitudes are selected.
        The fundamental frequency plus harmonics resounding over white noise
        with Gaussian distribution are selected by targeting
        amplitudes over a certain z-score coefficient.
        This is applicable since a high signal to noise ratio(SNR) is required.
        Adjacent above-threshold bins are grouped into clusters; the highest-amplitude
        bin within each cluster is taken as the representative peak, avoiding bias
        from spectral leakage widening the peak across multiple bins.
    6- Given that we are only interested in the fundamental frequency, we select the peak that appears first
    7- The frequency of the peak is determined using Gaussian interpolation


    Bibliography:
    Improving FFT resolution, J. Marsar. 2015. http://www.add.ece.ufl.edu/4511/references/ImprovingFFTResoltuion.pdf
    Improving FFT frequency measurement resolution by parabolic and gaussian interpolation,
    M. Gasior, J.L. Gonzalez. 2004. https://mgasior.web.cern.ch/pap/FFT_resol_note.pdf
"""

import threading

import numpy as np
import scipy.signal.windows as scipy_win

from interfaces.process import Process
from sound_sample import SoundSample

# constants:
DEFAULT_FFT_SIZE = 2048
DEFAULT_TARGET_Z_SCORE = 3


def _gaussian_interpolation(amplitudes, peak_bin, fft_freq_resolution):
    """
    Interpolate the frequency of the peak bin.

    :param amplitudes: A list of real numbers
    :param peak_bin: The index of the peak bin for which to interpolate the frequency
    :param fft_freq_resolution: The difference in frequency between each fft bin
    :return: The frequency of the peak. -1 if peak_bin < 1 or out of range
    """
    if peak_bin < 1 or len(amplitudes) - 1 <= peak_bin:
        return -1

    top = np.log(amplitudes[peak_bin + 1] / amplitudes[peak_bin - 1])
    bottom = 2 * np.log(amplitudes[peak_bin] ** 2 /
                        (amplitudes[peak_bin + 1] * amplitudes[peak_bin - 1]))
    delta = top / bottom
    return fft_freq_resolution * (delta + peak_bin)


def _normalize_32b(amplitudes):
    """
    Increase the amplitudes proportionally to optimize use of 32b range

    :param amplitudes: A list of real numbers
    :return: A list of real numbers. the normalized amplitudes
    """
    max_amp = max(amplitudes.max(), abs(amplitudes.min()))
    half_range = (2 ** 32 - 1) // 2
    return [(amp / max_amp) * half_range for amp in amplitudes]


class FrequencyExtractor(Process):
    """
    Extracts the fundamental frequency from a SoundSample.

    Parameters can be updated at runtime via the set_* methods.  Each setter
    acquires an internal lock so changes are safe to call from a GUI thread
    while the pipeline thread is running.  run() snapshots the current
    parameters under the same lock before releasing it for the computation,
    so a parameter update never races with an in-progress analysis.
    """

    def __init__(self, **kwargs) -> None:
        self.__fft_size = kwargs.get("fft_size", DEFAULT_FFT_SIZE)
        self.__target_z_score = kwargs.get("target_z_score", DEFAULT_TARGET_Z_SCORE)
        self.__norm = kwargs.get("norm", None)
        # Default window matches fft_size so resizing fft_size never produces a mismatch.
        self.__window = kwargs.get("window", scipy_win.hann(self.__fft_size, sym=False))
        self.__lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # Live parameter setters — safe to call from any thread               #
    # ------------------------------------------------------------------ #

    def set_fft_size(self, fft_size: int) -> None:
        """Set FFT size and regenerate a Hann window of matching length."""
        with self.__lock:
            self.__fft_size = fft_size
            self.__window = scipy_win.hann(fft_size, sym=False)

    def set_window(self, window: np.ndarray) -> None:
        """Set a custom window array; fft_size is inferred from its length."""
        with self.__lock:
            self.__window = np.asarray(window, dtype=np.float64)
            self.__fft_size = len(self.__window)

    def set_target_z_score(self, z_score: float) -> None:
        """Set the z-score threshold used for peak detection."""
        with self.__lock:
            self.__target_z_score = z_score

    def set_norm(self, norm) -> None:
        """Set the numpy.fft normalisation mode ('backward', 'ortho', 'forward', or None)."""
        with self.__lock:
            self.__norm = norm

    # ------------------------------------------------------------------ #
    # Process interface                                                    #
    # ------------------------------------------------------------------ #

    def run(self, sound_sample=None):
        # Snapshot parameters while holding the lock so no setter can mutate
        # them mid-read; release before the computation so GUI updates are not
        # blocked for the duration of the FFT.
        with self.__lock:
            fft_size = self.__fft_size
            target_z_score = self.__target_z_score
            norm = self.__norm
            window = self.__window

        return self.__get_fundamental_frequency(sound_sample, fft_size, target_z_score, norm, window)

    # ------------------------------------------------------------------ #
    # Private computation methods                                         #
    # ------------------------------------------------------------------ #

    def __get_amplitude_threshold(self, amplitudes, target_z_score):
        """
        Evaluate a threshold for the amplitudes.

        The assumption is that the source of interest is recorded over noise with a Gaussian distribution
        :param amplitudes: A list of amplitudes
        :param target_z_score: The z-score multiplier for the threshold
        :return: the threshold
        """
        mean = np.mean(amplitudes)
        sd = np.std(amplitudes)
        return target_z_score * sd + mean

    def __select_peaks(self, amplitudes, target_z_score):
        """
        Select the indexes of the peak amplitudes.

        Above-threshold bins are grouped into clusters of consecutive indexes.
        The bin with the highest amplitude within each cluster is returned as the
        representative peak, avoiding the bias that spectral leakage introduces
        when the left edge of a wide cluster is naively taken as the peak.

        :param amplitudes: A list of amplitude values
        :param target_z_score: The z-score multiplier for the threshold
        :return: A list of bin indexes, one per above-threshold cluster
        """
        amplitude_threshold = self.__get_amplitude_threshold(amplitudes, target_z_score)
        above = [b for b in range(len(amplitudes)) if amplitudes[b] > amplitude_threshold]
        if not above:
            return [-1]

        peaks = []
        cluster = [above[0]]
        for i in range(1, len(above)):
            if above[i] == above[i - 1] + 1:
                cluster.append(above[i])
            else:
                peaks.append(max(cluster, key=lambda b: amplitudes[b]))
                cluster = [above[i]]
        peaks.append(max(cluster, key=lambda b: amplitudes[b]))
        return peaks

    def __get_spectrum(self, samples, fft_size, norm):
        """
        Get the frequency spectrum of the sample.

        :return: A list of real numbers, the values of amplitude across frequency in an instant
        """
        complex_amplitudes = np.fft.rfft(samples, n=fft_size, norm=norm)
        complex_amplitudes[1:] = 2 * complex_amplitudes[1:]
        real_amplitudes = np.abs(complex_amplitudes)
        return real_amplitudes

    def __get_fundamental_frequency(self, sound_sample: SoundSample, fft_size, target_z_score, norm, window):
        """
        Evaluate the fundamental frequency contained in a sample.

        :param sound_sample: A SoundSample
        :return: A double, The fundamental frequency
        """
        samples = sound_sample.get_samples()
        cropped_samples = samples[:fft_size]
        normalized_samples = _normalize_32b(cropped_samples)
        windowed_samples = normalized_samples * window
        amplitudes = self.__get_spectrum(windowed_samples, fft_size, norm)
        peaks = self.__select_peaks(amplitudes, target_z_score)
        freq_resolution = sound_sample.get_sample_rate() / fft_size
        return _gaussian_interpolation(amplitudes, peaks[0], freq_resolution)
