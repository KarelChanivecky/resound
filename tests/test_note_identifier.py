from unittest import TestCase

from musical_note import MusicalNote
from note_identifier import get_note, get_semitone_diff


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
        got = get_note(freq, 440)
        self.assertTrue(expected == got)

    def test_get_note_above_A4(self):
        # C5 , 3, 5, +-0
        expected = MusicalNote(3, 5, 0)
        freq = 523.25
        got = get_note(freq, 440)
        self.assertTrue(expected == got)

    def test_get_note_delta_to_next_octave(self):
        # C5-0.1 , 3, 4, -0.1
        expected = MusicalNote(3, 5, -0.1)
        freq = 520.2374
        got = get_note(freq, 440)
        self.assertTrue(expected == got)

    def test_get_note_delta_under_point_five(self):
        # A4-0.1 , 0, 4, -0.1
        expected = MusicalNote(0, 4, -0.1)
        freq = 437.46578
        got = get_note(freq, 440)
        self.assertTrue(expected == got)

    def test_get_note_delta_above_point_five(self):
        # A4+0.1 , 0, 4, 0.1
        expected = MusicalNote(0, 4, 0.1)
        freq = 442.54889
        got = get_note(freq, 440)
        self.assertTrue(expected == got)
