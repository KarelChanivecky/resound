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
from SoundSample import SoundSample
from consumer import Consumer
from producer import Producer
import threading as th

# constants:
FFT_SIZE = 2048
TARGET_Z_SCORE = 3


def get_amplitude_threshold(amplitudes):
    """
    Evaluate a threshold for the amplitudes.

    The assumption is that the source of interest is recorded over noise with a Gaussian distribution
    :param amplitudes: A list of amplitudes
    :return: the threshold
    """
    mean = np.mean(amplitudes)
    sd = np.std(amplitudes)
    return TARGET_Z_SCORE * sd + mean


def select_peaks(amplitudes):
    """
    Select the indexes of the peak amplitudes 

    :param amplitudes: A list of tuples: (freq, amp)
    :return: The peaks.  A list of tuples: (freq, amp)
    """
    amplitude_threshold = get_amplitude_threshold(amplitudes)
    peaks = []
    for fft_bin in range(0, len(amplitudes)):
        if amplitude_threshold < amplitudes[fft_bin]:
            peaks.append(fft_bin)
    return peaks


def get_fft_time_resolution(sample_rate):
    """
    Evaluate the size of the time window evaluated in the fft.

    :param sample_rate: The number of samples per second
    :return: a real number
    """
    return FFT_SIZE / sample_rate


def get_fft_freq_resolution(sample_rate):
    """
    Evaluate the difference in frequency between each fft bin.

    :param sample_rate: The number of samples per second
    :return: a real number
    """
    return sample_rate / FFT_SIZE


def gaussian_interpolation(amplitudes, target_amplitude, fft_freq_resolution):
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


def normalize_32b(amplitudes):
    """
    Increase the amplitudes proportionally to optimize use of 32b range

    :param amplitudes: A list of real numbers
    :return: A list of real numbers. the normalized amplitudes
    """
    max_amp = max(amplitudes.max(), abs(amplitudes.min()))
    half_range = (2 ** 32 - 1) // 2
    return [(amp / max_amp) * half_range for amp in amplitudes]


def window_samples(amplitudes):
    """
    Apply a window to the given sample

    :param amplitudes: A list of real numbers
    """
    window = scipy_win.hann(FFT_SIZE, sym=False)
    return amplitudes * window


def get_spectrum(samples):
    """
    Get the frequency spectrum of the sample

    :return: A list of real numbers, the values of amplitude across frequency in an instant
    """
    complex_amplitudes = np.fft.rfft(samples, n=FFT_SIZE)
    complex_amplitudes[1:] = 2 * complex_amplitudes[1:]
    real_amplitudes = np.abs(complex_amplitudes)
    return real_amplitudes


def get_fundamental_frequency(sound_sample: SoundSample):
    """
    Evaluate the fundamental frequency contained in a sample.

    :param sound_sample: A SoundSample
    :return: A double, The fundamental frequency
    """
    samples = sound_sample.get_samples()
    cropped_samples = samples[:FFT_SIZE]
    normalized_samples = normalize_32b(cropped_samples)
    windowed_samples = window_samples(normalized_samples)
    amplitudes = get_spectrum(windowed_samples)
    peaks = select_peaks(amplitudes)
    return gaussian_interpolation(amplitudes, peaks[0], get_fft_freq_resolution(sound_sample.get_sample_rate()))


class FrequencyExtractor(Producer, Consumer):
    """
    A consumer that extracts the base frequency in a SoundSample
    """

    CONSUMER_BUFFER_SIZE = 1024

    def __init__(self, consumer):
        """
        Construct instance of Frequency FrequencyExtractor.

        This class is a producer/consumer.

        :param consumer: The consumer of the data produced by this class
        """
        Producer.__init__(self, consumer)
        Consumer.__init__(self, 1024)
        self.thread = th.Thread(target=self._consume)
        self.producing = False
        self.consuming = False

    def _consume(self):
        """
        Consume from buffer.
        """
        # Consume the whole buffer when stopping
        while self.consuming or not (self._buffer.empty() and self.producing):
            self._producer_semaphore.acquire()
            sound_sample = self._buffer.get()
            self._produce(get_fundamental_frequency(sound_sample))
            self._consumer_semaphore.release()
        self.stop_producing()

    def start_producing(self):
        self.producing = True
        self.thread.start()
        self._consumer.start_consuming()

    def stop_producing(self):
        self.producing = False
        self._consumer.stop_consuming()

    def start_consuming(self):
        self.consuming = True
        self.start_producing()
        self.thread.start()

    def stop_consuming(self):
        self.consuming = False
