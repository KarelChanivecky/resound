import numpy as np

from interfaces.process import Process


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


class FrequencyInterpolator(Process):
    """
    Applies Gaussian interpolation to the lowest-frequency peak in a DetectedPeaks
    to produce a sub-bin-accurate fundamental frequency estimate.
    """

    def run(self, detected_peaks=None):
        return _gaussian_interpolation(
            detected_peaks.amplitudes,
            detected_peaks.peak_bins[0],
            detected_peaks.freq_resolution,
        )
