"""
Tests for CLI argument parsing and source-selection logic in main.py.

These tests import private helpers (_parse_args, _build_audio_source) directly
rather than launching a subprocess, keeping them fast and deterministic.
"""

import unittest

from main import _parse_args, _build_audio_source
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
        self.assertAlmostEqual(args.zscore, 4.5)

    def test_zscore_negative_rejected(self):
        with self.assertRaises(SystemExit):
            _parse_args(['--zscore', '-1'])

    def test_snr_parsed(self):
        args = _parse_args(['--source', 'synth', '--notes', 'A45', '--snr', '15'])
        self.assertAlmostEqual(args.snr, 15.0)

    def test_window_default_is_hann(self):
        args = _parse_args([])
        self.assertEqual(args.window, 'hann')

    def test_window_kaiser_parsed(self):
        args = _parse_args(['--window', 'kaiser', '--beta', '8.0'])
        self.assertEqual(args.window, 'kaiser')
        self.assertAlmostEqual(args.beta, 8.0)

    def test_window_tukey_parsed(self):
        args = _parse_args(['--window', 'tukey', '--alpha', '0.3'])
        self.assertEqual(args.window, 'tukey')
        self.assertAlmostEqual(args.alpha, 0.3)

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
