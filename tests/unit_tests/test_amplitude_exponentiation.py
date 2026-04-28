import unittest

import numpy as np

from processes.amplitude_exponentiation import AmplitudeExponentiator
from data_models.spectrum import Spectrum


class TestAmplitudeExponentiator(unittest.TestCase):

    def _make_spectrum(self, amplitudes, windowed_sample=None):
        return Spectrum(np.array(amplitudes, dtype=np.float64),
                        freq_resolution=10.0,
                        windowed_sample=windowed_sample)

    def test_exponent_one_returns_same_amplitudes(self):
        exp = AmplitudeExponentiator(exponent=1.0)
        spectrum = self._make_spectrum([0.5, 1.0, 0.3])
        result = exp.run(spectrum)
        np.testing.assert_array_equal(result.amplitudes, spectrum.amplitudes)

    def test_exponent_two_sharpens_peaks(self):
        # Bin 1 is 2× bin 0.  After squaring the ratio should increase.
        exp = AmplitudeExponentiator(exponent=2.0)
        spectrum = self._make_spectrum([1.0, 2.0])
        result = exp.run(spectrum)
        original_ratio = spectrum.amplitudes[1] / spectrum.amplitudes[0]
        new_ratio = result.amplitudes[1] / result.amplitudes[0]
        self.assertGreater(new_ratio, original_ratio)

    def test_rescaling_preserves_peak_amplitude(self):
        exp = AmplitudeExponentiator(exponent=2.0)
        spectrum = self._make_spectrum([1.0, 3.0, 2.0])
        result = exp.run(spectrum)
        self.assertAlmostEqual(result.amplitudes.max(),
                               spectrum.amplitudes.max())

    def test_zero_amplitude_returns_unchanged(self):
        exp = AmplitudeExponentiator(exponent=2.0)
        spectrum = self._make_spectrum([0.0, 0.0, 0.0])
        result = exp.run(spectrum)
        np.testing.assert_array_equal(result.amplitudes, spectrum.amplitudes)

    def test_set_exponent_updates_at_runtime(self):
        exp = AmplitudeExponentiator(exponent=1.0)
        spectrum = self._make_spectrum([1.0, 2.0])
        # With exponent 1.0 ratio is unchanged
        result_before = exp.run(spectrum)
        ratio_before = result_before.amplitudes[1] / result_before.amplitudes[0]

        exp.set_exponent(2.0)
        result_after = exp.run(spectrum)
        ratio_after = result_after.amplitudes[1] / result_after.amplitudes[0]

        self.assertGreater(ratio_after, ratio_before)

    def test_windowed_sample_passed_through(self):
        sentinel = object()
        exp = AmplitudeExponentiator(exponent=2.0)
        spectrum = self._make_spectrum([1.0, 3.0], windowed_sample=sentinel)
        result = exp.run(spectrum)
        self.assertIs(result.windowed_sample, sentinel)

    def test_large_exponent_does_not_overflow(self):
        # Values that would overflow float64 with a direct ** call must stay finite
        # and preserve the peak via the iterative normalise-then-exponentiate approach.
        exp = AmplitudeExponentiator(exponent=1000.0)
        spectrum = self._make_spectrum([1e10, 2e10, 5e10])
        result = exp.run(spectrum)
        self.assertTrue(np.all(np.isfinite(result.amplitudes)))
        self.assertAlmostEqual(result.amplitudes.max(),
                               spectrum.amplitudes.max(), places=3)


if __name__ == '__main__':
    unittest.main()
