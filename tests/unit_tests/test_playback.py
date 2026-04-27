import unittest
from unittest.mock import patch, MagicMock
import numpy as np

from processes.playback import Playback, _SOUNDDEVICE_AVAILABLE
from sound_sample import SoundSample


def _make_sample(sample_rate=5000, n_samples=100):
    samples = (np.random.default_rng(0).integers(
        -2**31, 2**31, size=n_samples, dtype=np.int32))
    return SoundSample(sample_rate, n_samples / sample_rate, samples)


@unittest.skipUnless(_SOUNDDEVICE_AVAILABLE, 'sounddevice requires PortAudio (libportaudio2)')
class TestPlayback(unittest.TestCase):

    def _run_with_mocked_sounddevice(self, sample):
        mock_sd = MagicMock()
        with patch('processes.playback.soundd', mock_sd):
            Playback().run(sample)
        return mock_sd

    def test_run_calls_play_and_wait(self):
        mock_sd = self._run_with_mocked_sounddevice(_make_sample())
        mock_sd.play.assert_called_once()
        mock_sd.wait.assert_called_once()

    def test_run_normalises_samples_to_float32(self):
        mock_sd = self._run_with_mocked_sounddevice(_make_sample())
        data = mock_sd.play.call_args[0][0]
        self.assertEqual(data.dtype, np.float32)
        self.assertLessEqual(np.max(np.abs(data)), 1.0 + 1e-6)

    def test_run_passes_sample_rate(self):
        sample = _make_sample(sample_rate=8000)
        mock_sd = self._run_with_mocked_sounddevice(sample)
        rate = mock_sd.play.call_args[0][1]
        self.assertEqual(rate, 8000)

    def test_run_with_none_does_not_call_play(self):
        mock_sd = self._run_with_mocked_sounddevice(None)
        mock_sd.play.assert_not_called()

    def test_hardware_error_propagates(self):
        with patch('processes.playback.soundd') as mock_sd:
            mock_sd.play.side_effect = RuntimeError('no output device')
            with self.assertRaises(RuntimeError):
                Playback().run(_make_sample())


class TestPlaybackWithoutSounddevice(unittest.TestCase):

    def test_raises_runtime_error_when_unavailable(self):
        with patch('processes.playback._SOUNDDEVICE_AVAILABLE', False):
            with self.assertRaises(RuntimeError):
                Playback().run(_make_sample())
