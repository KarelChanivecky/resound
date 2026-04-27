import unittest

from musical_note import MusicalNote


class TestMusicalNoteGetName(unittest.TestCase):

    def test_a4(self):
        self.assertEqual(MusicalNote(0, 4, 0.0).get_name(), 'A4')

    def test_sharp(self):
        self.assertEqual(MusicalNote(1, 4, 0.0).get_name(), 'A#4')

    def test_c5(self):
        self.assertEqual(MusicalNote(3, 5, 0.0).get_name(), 'C5')

    def test_g_sharp_3(self):
        self.assertEqual(MusicalNote(11, 3, 0.0).get_name(), 'G#3')


class TestMusicalNoteStr(unittest.TestCase):

    def test_in_tune(self):
        self.assertEqual(str(MusicalNote(0, 4, 0.0)), 'A4 (+0 cents)')

    def test_sharp_cents(self):
        self.assertEqual(str(MusicalNote(3, 5, 0.08)), 'C5 (+8 cents)')

    def test_flat_cents(self):
        self.assertEqual(str(MusicalNote(11, 3, -0.4)), 'G#3 (-40 cents)')
