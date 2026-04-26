from unittest import TestCase
import numpy as np
from processes.frequency_extractor import FrequencyExtractor
from sound_sample import SoundSample


class TestFrequencyExtractor(TestCase):
    def test_get_fundamental_frequency(self):
        """
        Demonstrates the capability to detect a note over a noisy environment.
        May occasionally fail due to the random nature of the noise.
        """
        sample_rate = 5000
        a_frequency = 440
        length = 1
        a_amplitude = 10
        time_space = np.linspace(0, length, sample_rate * length)
        a_wave = np.sin(a_frequency * 2 * np.pi * time_space)
        a_wave *= a_amplitude
        noise_amplitude = 1
        noise = np.random.normal(size=sample_rate * length, scale=noise_amplitude)
        a_wave += noise
        sound_sample = SoundSample(sample_rate, length, a_wave)
        identified_freq = FrequencyExtractor().run(sound_sample)
        self.assertAlmostEqual(identified_freq, a_frequency, delta=2)
