class WindowedSample:
    def __init__(self, samples, fft_size, sample_rate, raw_samples=None):
        self.samples = samples  # normalized + windowed
        self.fft_size = fft_size
        self.sample_rate = sample_rate
        self.raw_samples = raw_samples  # cropped input before normalization/windowing
