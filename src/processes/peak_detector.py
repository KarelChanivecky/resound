import threading

import numpy as np

from data_models.detected_peaks import DetectedPeaks
from interfaces.process import Process
from data_models.spectrum import Spectrum

DEFAULT_TARGET_Z_SCORE = 3


class PeakDetector(Process):
    """
    Identifies spectral peaks in a Spectrum using z-score thresholding.

    Bins whose amplitude exceeds (mean + z * std) are considered above-threshold.
    Adjacent above-threshold bins are grouped into clusters; the highest-amplitude
    bin within each cluster is returned as the representative peak, avoiding bias
    from spectral leakage widening a peak across multiple bins.

    Returns DetectedPeaks with peak_bins=[-1] when no bins clear the threshold.

    The target_z_score can be updated at runtime via set_target_z_score().
    """

    def __init__(self, target_z_score=DEFAULT_TARGET_Z_SCORE):
        self.__target_z_score = target_z_score
        self.__lock = threading.Lock()

    def set_target_z_score(self, z_score: float) -> None:
        with self.__lock:
            self.__target_z_score = z_score

    def run(self, spectrum: Spectrum = None) -> DetectedPeaks:
        with self.__lock:
            target_z_score = self.__target_z_score

        amplitudes = spectrum.amplitudes
        threshold = np.mean(amplitudes) + target_z_score * np.std(amplitudes)
        above = [b for b in range(len(amplitudes)) if amplitudes[b] > threshold]

        ws = spectrum.windowed_sample

        if not above:
            return DetectedPeaks(amplitudes, [-1], spectrum.freq_resolution,
                                 threshold=threshold, windowed_sample=ws)

        peak_bins = []
        cluster = [above[0]]
        for i in range(1, len(above)):
            if above[i] == above[i - 1] + 1:
                cluster.append(above[i])
            else:
                peak_bins.append(max(cluster, key=lambda b: amplitudes[b]))
                cluster = [above[i]]
        peak_bins.append(max(cluster, key=lambda b: amplitudes[b]))

        return DetectedPeaks(amplitudes, peak_bins, spectrum.freq_resolution,
                             threshold=threshold, windowed_sample=ws)
