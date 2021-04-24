from unittest import TestCase
import numpy.random as np_rd
from processes import frequency_extraction_process
from processes.frequency_extraction_process import FrequencyExtractionProcess


class Test(TestCase):
    def test_select_peaks(self):
        mean = 10
        sd = 1
        normal_samples = list(np_rd.normal(loc=mean, scale=sd, size=100))
        normal_samples.insert(0, 100)
        normal_samples.insert(10, 200)
        normal_samples.insert(50, 300)
        normal_samples.insert(99, 15)
        peaks = FrequencyExtractionProcess()._FrequencyExtractionProcess__select_peaks(normal_samples)
        self.assertEqual(len(peaks), 2)
        self.assertEqual(peaks[0], 10)
        self.assertEqual(peaks[1], 50)
