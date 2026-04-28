import unittest
from unittest.mock import patch, MagicMock

import numpy as np

from processes.playback import Playback, _SOUNDDEVICE_AVAILABLE
from sound_sample import SoundSample


def _make_sample(sample_rate=5000, n_samples=100):
    samples = (np.random.default_rng(0).integers(
        -2 ** 31, 2 ** 31, size=n_samples, dtype=np.int32))
    return SoundSample(sample_rate, n_samples / sample_rate, samples)


def _patched_playback(sample):
    """Run Playback.run(sample) with soundd fully mocked; return (mock_sd, mock_stream)."""
    mock_sd = MagicMock()
    mock_stream = MagicMock()
    mock_stream.active = True
    mock_sd.OutputStream.return_value = mock_stream
    with patch('processes.playback.soundd', mock_sd):
        Playback().run(sample)
    return mock_sd, mock_stream


@unittest.skipUnless(_SOUNDDEVICE_AVAILABLE, 'sounddevice requires PortAudio (libportaudio2)')
class TestPlayback(unittest.TestCase):

    def test_run_opens_stream_and_writes(self):
        mock_sd, mock_stream = _patched_playback(_make_sample())
        mock_sd.OutputStream.assert_called_once()
        mock_stream.start.assert_called_once()
        mock_stream.write.assert_called_once()

    def test_run_normalises_samples_to_float32(self):
        _, mock_stream = _patched_playback(_make_sample())
        data = mock_stream.write.call_args[0][0]
        self.assertEqual(data.dtype, np.float32)
        self.assertLessEqual(np.max(np.abs(data)), 1.0 + 1e-6)

    def test_run_passes_sample_rate_to_stream(self):
        sample = _make_sample(sample_rate=8000)
        mock_sd, _ = _patched_playback(sample)
        _, kwargs = mock_sd.OutputStream.call_args
        self.assertEqual(kwargs['samplerate'], 8000)

    def test_stream_reused_across_calls(self):
        mock_sd = MagicMock()
        mock_stream = MagicMock()
        mock_stream.active = True
        mock_sd.OutputStream.return_value = mock_stream
        sample = _make_sample()
        with patch('processes.playback.soundd', mock_sd):
            p = Playback()
            p.run(sample)
            p.run(sample)
        mock_sd.OutputStream.assert_called_once()
        self.assertEqual(mock_stream.write.call_count, 2)

    def test_run_with_none_does_not_open_stream(self):
        mock_sd, mock_stream = _patched_playback(None)
        mock_sd.OutputStream.assert_not_called()
        mock_stream.write.assert_not_called()

    def test_hardware_error_propagates(self):
        mock_sd = MagicMock()
        mock_stream = MagicMock()
        mock_stream.write.side_effect = RuntimeError('no output device')
        mock_sd.OutputStream.return_value = mock_stream
        with patch('processes.playback.soundd', mock_sd):
            with self.assertRaises(RuntimeError):
                Playback().run(_make_sample())


class TestPlaybackWithoutSounddevice(unittest.TestCase):

    def test_raises_runtime_error_when_unavailable(self):
        with patch('processes.playback._SOUNDDEVICE_AVAILABLE', False):
            with self.assertRaises(RuntimeError):
                Playback().run(_make_sample())
