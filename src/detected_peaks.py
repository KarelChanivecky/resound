class DetectedPeaks:
    def __init__(self, amplitudes, peak_bins, freq_resolution,
                 threshold=None, windowed_sample=None):
        self.amplitudes = amplitudes
        self.peak_bins = peak_bins
        self.freq_resolution = freq_resolution
        self.threshold = threshold  # computed z-score amplitude threshold
        self.windowed_sample = windowed_sample  # carries raw_samples and windowed samples
