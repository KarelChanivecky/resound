"""
This extractor targets frequencies between 16Hz (C0) and 8000Hz (B8)

    Rationale:
    1- The consumer is given an array of samples
    2- The samples are normalized over a 32b range
    3- A Hann window is applied to the samples to improve accuracy, frequency resolution and decrease spectral leakage
    4- An FFT is applied to obtain the frequency spectrum
    5- Bins with outlier(right lobe of amplitude distribution only) amplitudes in are selected
        The fundamental frequency plus harmonics resounding over white noise
        with Gaussian distribution are selected by targeting
        amplitudes over a certain z-score coefficient.
        This is applicable since a high signal to noise ratio(SNR) is required
    6- Given that we are only interested in the fundamental frequency, we select the peak that appears first
    7- The frequency of the peak is determined using Gaussian interpolation


    Bibliography:
    Improving FFT resolution, J. Marsar. 2015. http://www.add.ece.ufl.edu/4511/references/ImprovingFFTResoltuion.pdf
    Improving FFT frequency measurement resolution by parabolic and gaussian interpolation,
    M. Gasior, J.L. Gonzalez. 2004. https://mgasior.web.cern.ch/pap/FFT_resol_note.pdf
"""

import numpy as np
import scipy.signal.windows as scipy_win

from abstracts_interfaces.process import Process
from sound_sample import SoundSample

# constants:
DEFAULT_FFT_SIZE = 2048
DEFAULT_TARGET_Z_SCORE = 3


def _gaussian_interpolation(amplitudes, target_amplitude, fft_freq_resolution):
    """
    Interpolate the frequency of the target_amplitude.

    :param amplitudes: A list of real numbers
    :param target_amplitude: The index of the amplitude for which to interpolate the frequency
    :param fft_freq_resolution: The difference in frequency between each fft bin
    :return: The frequency of the peak. -1 if 1 <= target_amplitude
    """
    if target_amplitude < 1 or len(amplitudes) <= target_amplitude:
        return -1

    top = np.log(amplitudes[target_amplitude + 1] / amplitudes[target_amplitude - 1])
    bottom = 2 * np.log(amplitudes[target_amplitude] ** 2 /
                        (amplitudes[target_amplitude + 1] * amplitudes[target_amplitude - 1]))
    delta = top / bottom
    return fft_freq_resolution * (delta + target_amplitude)


def _normalize_32b(amplitudes):
    """
    Increase the amplitudes proportionally to optimize use of 32b range

    :param amplitudes: A list of real numbers
    :return: A list of real numbers. the normalized amplitudes
    """
    max_amp = max(amplitudes.max(), abs(amplitudes.min()))
    half_range = (2 ** 32 - 1) // 2
    return [(amp / max_amp) * half_range for amp in amplitudes]


class FrequencyExtractionProcess(Process):
    """
    A consumer that extracts the base frequency in a SoundSample
    """

    def __init__(self, **kwargs) -> None:
        K_FFT_SIZE = "fft_size"
        K_TARGET_Z_SCORE = "target_z_score"
        K_WINDOW = "window"
        default_kwargs = {
            K_FFT_SIZE: DEFAULT_FFT_SIZE,
            K_TARGET_Z_SCORE: DEFAULT_TARGET_Z_SCORE,
            K_WINDOW: scipy_win.hann(DEFAULT_FFT_SIZE, sym=False)
        }
        kwargs = {**default_kwargs, **kwargs}
        self.__fft_size = kwargs[K_FFT_SIZE]
        self.__target_z_score = kwargs[K_TARGET_Z_SCORE]
        self.__window = kwargs[K_WINDOW]

    def run(self, sound_sample=None):
        """
        Consume from buffer.
        """
        return self.__get_fundamental_frequency(sound_sample)

    def __get_amplitude_threshold(self, amplitudes):
        """
        Evaluate a threshold for the amplitudes.

        The assumption is that the source of interest is recorded over noise with a Gaussian distribution
        :param amplitudes: A list of amplitudes
        :return: the threshold
        """
        mean = np.mean(amplitudes)
        sd = np.std(amplitudes)
        return self.__target_z_score * sd + mean

    def __select_peaks(self, amplitudes):
        """
        Select the indexes of the peak amplitudes

        :param amplitudes: A list of tuples: (freq, amp)
        :return: The peaks.  A list of tuples: (freq, amp)
        """
        amplitude_threshold = self.__get_amplitude_threshold(amplitudes)
        peaks = []
        for fft_bin in range(0, len(amplitudes)):
            if amplitude_threshold < amplitudes[fft_bin]:
                peaks.append(fft_bin)
        if len(peaks) == 0:
            return [-1]
        return peaks

    def __get_fft_time_resolution(self, sample_rate):
        """
        Evaluate the size of the time window evaluated in the fft.

        :param sample_rate: The number of samples per second
        :return: a real number
        """
        return self.__fft_size / sample_rate

    def __get_fft_freq_resolution(self, sample_rate):
        """
        Evaluate the difference in frequency between each fft bin.

        :param sample_rate: The number of samples per second
        :return: a real number
        """
        return sample_rate / self.__fft_size

    def __window_samples(self, amplitudes):
        """
        Apply a window to the given sample

        :param amplitudes: A list of real numbers
        """
        return amplitudes * self.__window

    def __get_spectrum(self, samples):
        """
        Get the frequency spectrum of the sample

        :return: A list of real numbers, the values of amplitude across frequency in an instant
        """
        complex_amplitudes = np.fft.rfft(samples, n=self.__fft_size)
        complex_amplitudes[1:] = 2 * complex_amplitudes[1:]
        real_amplitudes = np.abs(complex_amplitudes)
        return real_amplitudes

    def __get_fundamental_frequency(self, sound_sample: SoundSample):
        """
        Evaluate the fundamental frequency contained in a sample.

        :param sound_sample: A SoundSample
        :return: A double, The fundamental frequency
        """
        samples = sound_sample.get_samples()
        cropped_samples = samples[:DEFAULT_FFT_SIZE]
        normalized_samples = _normalize_32b(cropped_samples)
        windowed_samples = self.__window_samples(normalized_samples)
        amplitudes = self.__get_spectrum(windowed_samples)
        peaks = self.__select_peaks(amplitudes)
        return _gaussian_interpolation(amplitudes, peaks[0],
                                       self.__get_fft_freq_resolution(sound_sample.get_sample_rate()))
