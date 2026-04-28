import threading
from unittest import TestCase

from data_models.musical_note import MusicalNote
from processes.note_identifier import identify_note, get_semitone_diff, NoteIdentifier


class TestNoteIdentifier(TestCase):

    def test_get_semitone_diff_above_A4(self):
        # C2
        expected = -33
        freq = 65.406
        self.assertAlmostEqual(expected, get_semitone_diff(freq, 440), places=3)

    def test_get_semitone_diff_below_A4(self):
        # E7
        expected = 31
        freq = 2637.0204
        self.assertAlmostEqual(expected, get_semitone_diff(freq, 440), places=3)

    def test_get_note_below_A4(self):
        # G#4 , 11, 4, +-0
        freq = 415.30
        expected = MusicalNote(11, 4, 0)
        got = identify_note(freq, 440)
        self.assertTrue(expected == got)

    def test_get_note_above_A4(self):
        # C5 , 3, 5, +-0
        expected = MusicalNote(3, 5, 0)
        freq = 523.25
        got = identify_note(freq, 440)
        self.assertTrue(expected == got)

    def test_get_note_delta_to_next_octave(self):
        # C5-0.1 , 3, 4, -0.1
        expected = MusicalNote(3, 5, -0.1)
        freq = 520.2374
        got = identify_note(freq, 440)
        self.assertTrue(expected == got)

    def test_get_note_delta_under_point_five(self):
        # A4-0.1 , 0, 4, -0.1
        expected = MusicalNote(0, 4, -0.1)
        freq = 437.46578
        got = identify_note(freq, 440)
        self.assertTrue(expected == got)

    def test_get_note_delta_above_point_five(self):
        # A4+0.1 , 0, 4, 0.1
        expected = MusicalNote(0, 4, 0.1)
        freq = 442.54889
        got = identify_note(freq, 440)
        self.assertTrue(expected == got)

    def test_negative_frequency_returns_none(self):
        self.assertIsNone(identify_note(-1, 440))

    def test_zero_frequency_returns_none(self):
        self.assertIsNone(identify_note(0, 440))

    def test_note_identifier_run_a4(self):
        note = NoteIdentifier().run(440)
        self.assertEqual(note.get_semitone(), 0)
        self.assertEqual(note.get_octave(), 4)

    def test_set_a4_frequency(self):
        ni = NoteIdentifier()
        ni.set_a4_frequency(432)
        note = ni.run(432)
        self.assertEqual(note.get_semitone(), 0)

    def test_concurrent_set_a4_frequency_does_not_raise(self):
        ni = NoteIdentifier()
        errors = []

        def setter_loop():
            for freq in [432, 440, 432, 440]:
                try:
                    ni.set_a4_frequency(freq)
                except Exception as exc:
                    errors.append(exc)

        def runner_loop():
            for _ in range(16):
                try:
                    ni.run(440)
                except Exception as exc:
                    errors.append(exc)

        threads = [threading.Thread(target=setter_loop),
                   threading.Thread(target=runner_loop)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(errors, [])
