import os
import unittest
from unittest.mock import patch
import numpy as np

from processes.recorder import Recorder, _SOUNDDEVICE_AVAILABLE
from sound_sample import SoundSample

_HARDWARE_AVAILABLE = bool(os.environ.get('HARDWARE_TESTS'))


@unittest.skipUnless(_SOUNDDEVICE_AVAILABLE, 'sounddevice requires PortAudio (libportaudio2)')
class TestRecorder(unittest.TestCase):

    def _make_raw_audio(self, n_frames):
        """Return a 2-D int32 array as sounddevice would."""
        return np.zeros((n_frames, 1), dtype='int32')

    def test_sample_rate_follows_nyquist(self):
        with patch('processes.recorder.soundd.rec') as mock_rec:
            mock_rec.return_value = self._make_raw_audio(6000)
            Recorder(target_frequency_max=3000, sample_duration=1).get_sample()
        mock_rec.assert_called_once_with(6000, 6000, 1, 'int32', blocking=True)

    def test_get_sample_returns_sound_sample(self):
        with patch('processes.recorder.soundd.rec') as mock_rec:
            mock_rec.return_value = self._make_raw_audio(6000)
            result = Recorder(3000, 1).get_sample()
        self.assertIsInstance(result, SoundSample)

    def test_get_sample_correct_sample_rate(self):
        with patch('processes.recorder.soundd.rec') as mock_rec:
            mock_rec.return_value = self._make_raw_audio(6000)
            result = Recorder(3000, 1).get_sample()
        self.assertEqual(result.get_sample_rate(), 6000)

    def test_get_sample_correct_duration(self):
        with patch('processes.recorder.soundd.rec') as mock_rec:
            mock_rec.return_value = self._make_raw_audio(6000)
            result = Recorder(3000, 1).get_sample()
        self.assertEqual(result.get_sample_duration(), 1)

    def test_get_sample_flattens_channel_axis(self):
        raw = np.arange(6000).reshape((6000, 1)).astype('int32')
        with patch('processes.recorder.soundd.rec') as mock_rec:
            mock_rec.return_value = raw
            result = Recorder(3000, 1).get_sample()
        np.testing.assert_array_equal(result.get_samples(), raw[:, 0])

    def test_run_delegates_to_get_sample(self):
        with patch('processes.recorder.soundd.rec') as mock_rec:
            mock_rec.return_value = self._make_raw_audio(6000)
            recorder = Recorder(3000, 1)
            self.assertEqual(
                recorder.run().get_sample_rate(),
                recorder.get_sample().get_sample_rate()
            )


@unittest.skipUnless(_HARDWARE_AVAILABLE, 'set HARDWARE_TESTS=1 to run hardware tests')
class TestRecorderHardware(unittest.TestCase):

    def test_get_sample_returns_nonzero_audio(self):
        sample = Recorder(target_frequency_max=3000, sample_duration=0.1).get_sample()
        self.assertIsInstance(sample, SoundSample)
        self.assertGreater(len(sample.get_samples()), 0)
