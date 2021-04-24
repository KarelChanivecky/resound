from unittest import TestCase
import numpy as np
from processes import frequency_extraction_process


class Test(TestCase):
    def test_get_fundamental_frequency(self):
        # this is expected to fail at certain times due to the random nature of the noise
        sample_rate = 5000
        A_frequency = 440
        length = 1
        A_amplitude = 10
        time_space = np.linspace(0, length, sample_rate * length)
        A_wave = np.sin(A_frequency * 2 * np.pi * time_space)
        A_wave *= A_amplitude
        noise_amplitude = 1
        noise = np.random.normal(size=sample_rate * length, scale=1, loc=noise_amplitude)
        A_wave *= noise
        sound_sample = sound_sample.SoundSample(sample_rate, length, A_wave)
        identified_freq = frequency_extraction_process.__get_fundamental_frequency(sound_sample)
        self.assertAlmostEqual(identified_freq, A_frequency, delta=2)
