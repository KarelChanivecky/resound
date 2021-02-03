"""
This extractor targets frequencies between 16Hz (C0) and 8000Hz (B8)

    Rationale:
    1- The consumer is given an array of samples
    2- An FFT is applied to obtain the frequency spectrum
    3- Bins with outlier amplitudes are selected
        Sine plus harmonics resounding over white noise
        with Gaussian distribution are selected by targeting
        amplitudes over a certain z-score coefficient
    4- The amplitude peaks are correlated to frequency bins
    5- The peaks are grouped by relative frequency
        next_group(peaks)
        group = [peaks.pop_head()]
        for each peak in samples
            mean_group_frequency = mean(group.frequencies)
            if mean_group_frequency * COEFF < peak.frequency
                return group
            group = [peaks.pop_head()]
    6- For each group, select 3 higher amplitudes, apply Gaussian interpolation
    7- Produce frequency

    Bibliography:
    Improving FFT resolution, J. Marsar. 2015. http://www.add.ece.ufl.edu/4511/references/ImprovingFFTResoltuion.pdf
    Improving FFT frequency measurement resolution by parabolic and gaussian interpolation,
    M. Gasior, J.L. Gonzalez. 2004. https://mgasior.web.cern.ch/pap/FFT_resol_note.pdf
"""

import numpy as np
from scipy.signal.windows import gaussian
from SoundSample import SoundSample
from consumer import Consumer
from producer import Producer
import threading as th

# constants:
HIGHPASS_FILTER_BOUND = 16
FREQ_INDEX = 0
AMP_INDEX = 1
TARGET_Z_SCORE = 3


# FFT_SIZE = 256


def contains_dissimilar_frequency(samples):
    """
    Evaluate if a set of samples contains a frequency significantly different from the rest.

    :param samples: A list of tuples: (freq, amp)
    :return: True if a dissimilar frequency is found, else false
    """
    print(f'@outliers: {samples}')
    threshold = samples[0] * 1.1
    print(f'threshold: {threshold}')
    print(f'{samples}')
    for sample in samples:
        if threshold < sample:
            print(f'outlier found: {sample}')
            return True
    return False


def get_next_group(samples):
    """
    Extract next group from samples.

    :param samples: A list of tuples: (freq, amp)
    :return: The next group. A list of tuples: (freq, amp)
    """
    if len(samples) == 0:
        return None
    next_group = [samples.pop(0)]
    while 0 < len(samples) and not contains_dissimilar_frequency(next_group[:] + [samples[0]]):
        next_group.append(samples.pop(0))
        print(f'accepted samples {next_group}')
    return np.mean(next_group)


def split(samples):
    """
    Split samples into groups.

    :param samples: A list of tuples: (freq, amp)
    :return: A list of groups of sample tuples
    """
    groups = []
    while next_group := get_next_group(samples) is not None:
        groups += [next_group]
    return groups


def highpass_filter(samples):
    """
    Remove data below a certain threshold.

    :param samples: A list of tuples: (freq, amp)
    """
    while 0 < len(samples) and samples[0][FREQ_INDEX] < HIGHPASS_FILTER_BOUND:
        samples.pop(0)


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


def select_peaks(samples):
    """
    Select the peaks in the sample

    :param samples: A list of tuples: (freq, amp)
    :return: The peaks.  A list of tuples: (freq, amp)
    """
    amplitude_low_bound = get_amplitude_threshold([amp for freq, amp in samples])
    peaks = [(freq, amp) for freq, amp in samples if amplitude_low_bound < amp]
    if len(peaks) == 0:
        return -1
    print(f'resonant freqs: {peaks}')
    return peaks


def gaussian_interpolation(samples, frequency_resolution):
    """
    Perform gaussian interpolation.

    :param frequency_resolution: The difference in frequency between bins of the FFT
    :param samples: A list of tuples: (freq, amp). Must be length == 3, with max peak in the center
    :return: The frequency of the peak
    """
    MAX_VAL_INDEX = 1
    top = np.log(samples[MAX_VAL_INDEX + 1][AMP_INDEX] / samples[MAX_VAL_INDEX - 1][AMP_INDEX])
    bottom = 2 * np.log(samples[MAX_VAL_INDEX][AMP_INDEX] ** 2 /
                        samples[MAX_VAL_INDEX + 1][AMP_INDEX] - samples[MAX_VAL_INDEX - 1][AMP_INDEX])
    delta = top / bottom
    return frequency_resolution * delta + samples[MAX_VAL_INDEX][FREQ_INDEX]


def gaussian_window(samples):
    """
    Apply a Gaussian Window

    :param samples: A list of tuples: (freq, amp)
    """
    SIGMA = 7
    window = gaussian(len(samples), SIGMA)
    for sample, point in zip(samples, window):
        sample[AMP_INDEX] *= point


def get_spectrum(sound_sample: SoundSample, fft_size):
    """
    Get the frequency spectrum of the sample

    :param fft_size: an int, the number of bins to split the fft in
    :param sound_sample: a SoundSample instance
    :return: A list of tuples: (freq, amp)
    """
    sample_rate = sound_sample.get_sample_rate()
    samples = sound_sample.get_samples()
    sample_count = len(samples)
    complex_amplitudes = np.fft.rfft(samples[:, 0], n=fft_size)[0:int(sample_count / 2)] / sample_count
    complex_amplitudes[1:] = 2 * complex_amplitudes[1:]
    amplitudes_real = np.abs(complex_amplitudes)
    freqs = sample_rate * np.arange(sample_count / 2) / sample_count
    return list(zip(freqs, amplitudes_real))


def get_peak_bin_index(samples):
    """
    Get the index of the bin containing the highest amplitude.

    :param samples: A list of tuples: (freq, amp)
    :return: An int, the index of the bin containing the highest amplitude
    """
    maximum = -1
    max_index = -1
    for i in range(0, len(samples)):
        if maximum < samples[i][AMP_INDEX]:
            maximum = samples[i][AMP_INDEX]
            max_index = i
    return max_index


def interpolate_group(samples, frequency_resolution=1):
    """
    Evaluate frequency contained in samples by Gaussian interpolation.

    :param frequency_resolution: The difference in frequency between consecutive bins
    :param samples: A list of tuples: (freq, amp)
    :return: A double, the fundamental frequency
    """
    max_index = get_peak_bin_index(samples)
    if max_index == 0 or max_index == len(samples) - 1:
        return samples[max_index][FREQ_INDEX]
    return gaussian_interpolation(
        [samples[max_index - 1], samples[max_index], samples[max_index + 1]],
        frequency_resolution)


def get_fundamental_frequency(sound_sample: SoundSample):
    """
    Evaluate the fundamental frequency contained in a sample.

    :param sound_sample: A SoundSample
    :return: A double, The fundamental frequency
    """
    samples = sound_sample.get_samples()
    gaussian_window(samples)

    fft_size = len(samples)
    spectrum = get_spectrum(samples, fft_size)
    highpass_filter(spectrum)
    peaks = select_peaks(samples)
    peak_groups = split(peaks)
    return interpolate_group(peak_groups[0], 1)


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
        self.thread = th.Thread(target=self.factory)
        self.producing = False
        self.consuming = False

    def factory(self):
        """
        Consume from buffer.
        """

        # Consume the whole buffer when stopping
        while self.consuming or not (super().__buffer.empty() and not self.producing):
            super().__producer_semaphore.acquire()
            sound_sample = super().__buffer.get()

            super().__produce(get_fundamental_frequency(sound_sample))
            super().__consumer_semaphore.release()

    def start_producing(self):
        self.producing = True
        self.thread.start()

    def stop_producing(self):
        self.producing = False

    def start_consuming(self):
        self.consuming = True
        self.start_producing()

    def stop_consuming(self):
        self.consuming = False

    def give(self, obj):
        super().__buffer.put(obj)
        super().__producer_semaphore.release()

    def verify(self):
        super().verify()
