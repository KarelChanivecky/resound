class WindowedSample:
    def __init__(self, samples, fft_size, sample_rate):
        self.samples = samples
        self.fft_size = fft_size
        self.sample_rate = sample_rate
