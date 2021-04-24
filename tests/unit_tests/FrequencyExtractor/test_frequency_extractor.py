from unittest import TestCase
import numpy as np
from processes import frequency_extraction_process
from processes.frequency_extraction_process import FrequencyExtractionProcess
from sound_sample import SoundSample


class Test(TestCase):
    def test_get_fundamental_frequency(self):
        """
        The purpose of this test is to demonstrate the capability to detect a note over a noisy environment.
        This is expected to fail at certain times due to the random nature of the noise.
        """
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
        sound_sample = SoundSample(sample_rate, length, A_wave)
        identified_freq = FrequencyExtractionProcess().run(sound_sample)
        self.assertAlmostEqual(identified_freq, A_frequency, delta=2)
