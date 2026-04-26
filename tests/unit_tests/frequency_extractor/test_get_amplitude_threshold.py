from unittest import TestCase
import numpy.random as np_rd
from processes import frequency_extractor
from processes.frequency_extractor import FrequencyExtractor


class TestGetAmplitudeThreshold(TestCase):
    def test_get_amplitude_threshold(self):
        mean = 10
        sd = 1
        normal_samples = np_rd.normal(loc=mean, scale=sd, size=100)
        normal_samples += [100]
        threshold = FrequencyExtractor()._FrequencyExtractor__get_amplitude_threshold(normal_samples)
        self.assertGreater(threshold, frequency_extractor.DEFAULT_TARGET_Z_SCORE * sd + mean)
