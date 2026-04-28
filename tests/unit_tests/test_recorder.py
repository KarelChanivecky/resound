import os
import unittest
from unittest.mock import patch

import numpy as np

from processes.recorder import Recorder, _SOUNDDEVICE_AVAILABLE
from sound_sample import SoundSample

_HARDWARE_AVAILABLE = bool(os.environ.get('HARDWARE_TESTS'))


@unittest.skipUnless(_SOUNDDEVICE_AVAILABLE, 'sounddevice requires PortAudio (libportaudio2)')
class TestRecorder(unittest.TestCase):

    class _FakeInputStream:
        def __init__(self, samplerate, channels, dtype, blocksize):
            self.samplerate = samplerate
            self.channels = channels
            self.dtype = dtype
            self.blocksize = blocksize
            self.started = False
            self.stopped = False
            self.closed = False
            self.next_frame = 0
            self.read_blocks = []

        def start(self):
            self.started = True

        def read(self, frames):
            self.read_blocks.append(frames)
            block = np.arange(self.next_frame, self.next_frame + frames,
                              dtype=self.dtype).reshape((frames, 1))
            self.next_frame += frames
            return block, False

        def stop(self):
            self.stopped = True

        def close(self):
            self.closed = True

    def _patch_input_stream(self):
        streams = []

        def make_stream(*, samplerate, channels, dtype, blocksize):
            stream = self._FakeInputStream(samplerate, channels, dtype, blocksize)
            streams.append(stream)
            return stream

        return patch('processes.recorder.soundd.InputStream', side_effect=make_stream), streams

    def test_sample_rate_follows_nyquist(self):
        input_stream_patch, streams = self._patch_input_stream()
        with input_stream_patch as mock_input_stream:
            Recorder(target_frequency_max=3000, sample_duration=1, fft_size=6000).get_sample()

        mock_input_stream.assert_called_once_with(
            samplerate=6000,
            channels=1,
            dtype='int32',
            blocksize=6000,
        )
        self.assertTrue(streams[0].started)

    def test_get_sample_returns_sound_sample(self):
        input_stream_patch, _streams = self._patch_input_stream()
        with input_stream_patch:
            result = Recorder(3000, 1, fft_size=6000).get_sample()

        self.assertIsInstance(result, SoundSample)

    def test_get_sample_correct_sample_rate(self):
        input_stream_patch, _streams = self._patch_input_stream()
        with input_stream_patch:
            result = Recorder(3000, 1, fft_size=6000).get_sample()

        self.assertEqual(result.get_sample_rate(), 6000)

    def test_fft_size_sets_window_duration_when_larger_than_step(self):
        input_stream_patch, _streams = self._patch_input_stream()
        with input_stream_patch:
            result = Recorder(target_frequency_max=10, sample_duration=0.25, fft_size=12).get_sample()

        self.assertEqual(result.get_sample_duration(), 0.6)
        np.testing.assert_array_equal(result.get_samples(), np.arange(3, 15))

    def test_sample_duration_sets_window_when_larger_than_fft_size(self):
        input_stream_patch, _streams = self._patch_input_stream()
        with input_stream_patch:
            result = Recorder(target_frequency_max=10, sample_duration=1, fft_size=12).get_sample()

        self.assertEqual(result.get_sample_duration(), 1)
        np.testing.assert_array_equal(result.get_samples(), np.arange(20))

    def test_get_sample_slides_window_after_initial_fill(self):
        input_stream_patch, _streams = self._patch_input_stream()
        with input_stream_patch:
            recorder = Recorder(target_frequency_max=10, sample_duration=0.25, fft_size=12)
            recorder.get_sample()
            result = recorder.get_sample()

        np.testing.assert_array_equal(result.get_samples(), np.arange(8, 20))

    def test_get_sample_slides_window_when_step_does_not_divide_fft_size(self):
        input_stream_patch, _streams = self._patch_input_stream()
        with input_stream_patch:
            recorder = Recorder(target_frequency_max=500, sample_duration=0.05, fft_size=128)
            recorder.get_sample()
            result = recorder.get_sample()

        np.testing.assert_array_equal(result.get_samples(), np.arange(72, 200))

    def test_returned_sample_is_not_mutated_by_next_run(self):
        input_stream_patch, _streams = self._patch_input_stream()
        with input_stream_patch:
            recorder = Recorder(target_frequency_max=10, sample_duration=0.25, fft_size=12)
            first = recorder.get_sample()
            first_samples = first.get_samples()
            recorder.get_sample()

        np.testing.assert_array_equal(first_samples, np.arange(3, 15))

    def test_get_sample_reuses_recording_buffer(self):
        input_stream_patch, streams = self._patch_input_stream()
        with input_stream_patch:
            recorder = Recorder(target_frequency_max=10, sample_duration=0.25, fft_size=5)
            recorder.get_sample()
            recorder.get_sample()

        self.assertEqual(streams[0].read_blocks, [5, 5])

    def test_set_sample_duration_resizes_step_and_window(self):
        input_stream_patch, streams = self._patch_input_stream()
        with input_stream_patch:
            recorder = Recorder(target_frequency_max=10, sample_duration=0.25, fft_size=12)
            recorder.set_sample_duration(1)
            result = recorder.get_sample()

        self.assertEqual(result.get_sample_duration(), 1)
        self.assertEqual(streams[0].blocksize, 20)

    def test_set_fft_size_resizes_window(self):
        input_stream_patch, _streams = self._patch_input_stream()
        with input_stream_patch:
            recorder = Recorder(target_frequency_max=10, sample_duration=0.25, fft_size=12)
            recorder.set_fft_size(20)
            result = recorder.get_sample()

        self.assertEqual(result.get_sample_duration(), 1)
        self.assertEqual(len(result.get_samples()), 20)

    def test_set_target_frequency_max_resizes_sample_rate(self):
        input_stream_patch, streams = self._patch_input_stream()
        with input_stream_patch:
            recorder = Recorder(target_frequency_max=10, sample_duration=0.25, fft_size=12)
            recorder.set_target_frequency_max(20)
            result = recorder.get_sample()

        self.assertEqual(result.get_sample_rate(), 40)
        self.assertEqual(streams[0].samplerate, 40)

    def test_set_target_frequency_max_closes_existing_stream(self):
        input_stream_patch, streams = self._patch_input_stream()
        with input_stream_patch:
            recorder = Recorder(target_frequency_max=10, sample_duration=0.25, fft_size=12)
            recorder.get_sample()
            recorder.set_target_frequency_max(20)

        self.assertTrue(streams[0].stopped)
        self.assertTrue(streams[0].closed)

    def test_close_stops_and_closes_stream(self):
        input_stream_patch, streams = self._patch_input_stream()
        with input_stream_patch:
            recorder = Recorder(target_frequency_max=10, sample_duration=0.25, fft_size=12)
            recorder.get_sample()
            recorder.close()

        self.assertTrue(streams[0].stopped)
        self.assertTrue(streams[0].closed)

    def test_run_delegates_to_get_sample(self):
        input_stream_patch, _streams = self._patch_input_stream()
        with input_stream_patch:
            recorder = Recorder(3000, 1, fft_size=6000)
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
