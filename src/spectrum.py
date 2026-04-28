class Spectrum:
    def __init__(self, amplitudes, freq_resolution, windowed_sample=None):
        self.amplitudes = amplitudes
        self.freq_resolution = freq_resolution
        self.windowed_sample = windowed_sample
