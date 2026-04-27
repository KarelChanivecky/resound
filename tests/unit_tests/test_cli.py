"""
Tests for CLI argument parsing and source-selection logic in main.py.

These tests import private helpers (_parse_args, _build_audio_source) directly
rather than launching a subprocess, keeping them fast and deterministic.
"""

import threading
import time
import unittest
from unittest.mock import patch

from main import _parse_args, _build_audio_source, main
from processes.recorder import Recorder
from processes.synthesizer import Synthesizer
from processes.frequency_extractor import FrequencyExtractor
from processes.note_identifier import NoteIdentifier


class TestParseArgs(unittest.TestCase):

    def test_no_args_defaults_to_recorder(self):
        args = _parse_args([])
        self.assertEqual(args.source, 'recorder')
        self.assertIsNone(args.notes)

    def test_synth_source_with_notes(self):
        args = _parse_args(['--source', 'synth', '--notes', 'A45'])
        self.assertEqual(args.source, 'synth')
        self.assertEqual(args.notes, 'A45')

    def test_synth_without_notes_exits(self):
        with self.assertRaises(SystemExit):
            _parse_args(['--source', 'synth'])

    def test_fft_size_parsed(self):
        args = _parse_args(['--fft-size', '4096'])
        self.assertEqual(args.fft_size, 4096)

    def test_fft_size_zero_rejected(self):
        with self.assertRaises(SystemExit):
            _parse_args(['--fft-size', '0'])

    def test_zscore_parsed(self):
        args = _parse_args(['--zscore', '4.5'])
        self.assertEqual(args.zscore, 4.5)

    def test_zscore_negative_rejected(self):
        with self.assertRaises(SystemExit):
            _parse_args(['--zscore', '-1'])

    def test_snr_parsed(self):
        args = _parse_args(['--source', 'synth', '--notes', 'A45', '--snr', '15'])
        self.assertEqual(args.snr, 15.0)

    def test_window_default_is_hann(self):
        args = _parse_args([])
        self.assertEqual(args.window, 'hann')

    def test_window_kaiser_parsed(self):
        args = _parse_args(['--window', 'kaiser', '--beta', '8.0'])
        self.assertEqual(args.window, 'kaiser')
        self.assertEqual(args.beta, 8.0)

    def test_window_tukey_parsed(self):
        args = _parse_args(['--window', 'tukey', '--alpha', '0.3'])
        self.assertEqual(args.window, 'tukey')
        self.assertEqual(args.alpha, 0.3)

    def test_fft_norm_parsed(self):
        args = _parse_args(['--fft-norm', 'ortho'])
        self.assertEqual(args.fft_norm, 'ortho')

    def test_invalid_window_rejected(self):
        with self.assertRaises(SystemExit):
            _parse_args(['--window', 'invalid'])


class TestBuildAudioSource(unittest.TestCase):

    def test_recorder_source(self):
        args = _parse_args([])
        source = _build_audio_source(args)
        self.assertIsInstance(source, Recorder)

    def test_synth_source(self):
        args = _parse_args(['--source', 'synth', '--notes', 'A45'])
        source = _build_audio_source(args)
        self.assertIsInstance(source, Synthesizer)


class TestCLIPipeline(unittest.TestCase):
    """
    Verify that arguments passed through the CLI produce the correct note at
    the end of the pipeline.  Uses Synthesizer as source so no hardware is needed.
    """

    def _run(self, cli_args):
        args = _parse_args(cli_args)
        source = _build_audio_source(args)
        norm = None if args.fft_norm == 'backward' else args.fft_norm
        extractor = FrequencyExtractor(
            fft_size=args.fft_size,
            target_z_score=args.zscore,
            norm=norm,
        )
        sample = source.run()
        freq = extractor.run(sample)
        return NoteIdentifier().run(freq)

    def test_synth_a4_identified(self):
        note = self._run(['--source', 'synth', '--notes', 'A45'])
        self.assertEqual(note.get_semitone(), 0)
        self.assertEqual(note.get_octave(), 4)

    def test_synth_c4_identified(self):
        note = self._run(['--source', 'synth', '--notes', 'C45'])
        self.assertEqual(note.get_semitone(), 3)   # C = 3 semitones above A
        self.assertEqual(note.get_octave(), 4)

    def test_synth_larger_fft_size(self):
        note = self._run(['--source', 'synth', '--notes', 'A45', '--fft-size', '4096'])
        self.assertEqual(note.get_semitone(), 0)
        self.assertEqual(note.get_octave(), 4)

    def test_synth_with_noise(self):
        note = self._run(['--source', 'synth', '--notes', 'A45', '--snr', '10'])
        self.assertEqual(note.get_semitone(), 0)
        self.assertEqual(note.get_octave(), 4)

    def test_synth_kaiser_window(self):
        note = self._run(['--source', 'synth', '--notes', 'A45',
                          '--window', 'kaiser', '--beta', '5'])
        self.assertEqual(note.get_semitone(), 0)
        self.assertEqual(note.get_octave(), 4)


class TestMainBlocks(unittest.TestCase):
    """
    Verify that main() blocks until signalled and then stops the pipeline.

    All pipeline threads are daemon threads, so main() must not return until
    explicitly stopped — otherwise the process exits and kills them immediately.
    The test injects a threading.Event via main()'s optional _stop_event parameter
    so it can unblock main() from the outside without sending real signals.
    """

    def test_main_blocks_and_stops_on_event(self):
        import main as main_module

        call_log = []

        class _TrackingProducer:
            def start(self):
                call_log.append('start')

            def stop(self):
                call_log.append('stop')

        def _fake_threaded_producer(upstream, source):
            return _TrackingProducer()

        stop_event = threading.Event()

        with patch.object(main_module, 'ThreadedProducer', _fake_threaded_producer), \
             patch('sys.argv', ['resound', '--source', 'synth', '--notes', 'A45']):

            main_thread = threading.Thread(
                target=lambda: main_module.main(stop_event), daemon=True)
            main_thread.start()

            time.sleep(0.05)
            self.assertTrue(main_thread.is_alive(),
                            'main() returned before being unblocked — it does not block')

            stop_event.set()
            main_thread.join(timeout=1.0)
            self.assertFalse(main_thread.is_alive(), 'main() did not return after event was set')

        self.assertIn('start', call_log)
        self.assertIn('stop', call_log)
        self.assertLess(call_log.index('start'), call_log.index('stop'))
