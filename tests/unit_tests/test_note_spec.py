import unittest

from misc.note_spec import NoteSpec, parse_note_specs, note_frequency


class TestParseNoteSpecs(unittest.TestCase):

    def test_single_note_no_detune(self):
        specs = parse_note_specs('A45')
        self.assertEqual(specs, [NoteSpec('A', 4, 5, 1)])

    def test_single_note_with_detune(self):
        specs = parse_note_specs('C#37:5')
        self.assertEqual(specs, [NoteSpec('C#', 3, 7, 5)])

    def test_detune_10(self):
        specs = parse_note_specs('E46:10')
        self.assertEqual(specs, [NoteSpec('E', 4, 6, 10)])

    def test_multiple_notes(self):
        specs = parse_note_specs('A45,C#37:5,E46')
        self.assertEqual(specs, [
            NoteSpec('A', 4, 5, 1),
            NoteSpec('C#', 3, 7, 5),
            NoteSpec('E', 4, 6, 1),
        ])

    def test_intensity_10(self):
        specs = parse_note_specs('A410')
        self.assertEqual(specs, [NoteSpec('A', 4, 10, 1)])

    def test_octave_10(self):
        specs = parse_note_specs('A105')
        self.assertEqual(specs, [NoteSpec('A', 10, 5, 1)])

    def test_octave_10_intensity_10(self):
        specs = parse_note_specs('A1010')
        self.assertEqual(specs, [NoteSpec('A', 10, 10, 1)])

    def test_whitespace_around_commas(self):
        specs = parse_note_specs('A45 , B35')
        self.assertEqual(specs, [NoteSpec('A', 4, 5, 1), NoteSpec('B', 3, 5, 1)])

    def test_invalid_format_raises(self):
        with self.assertRaises(ValueError):
            parse_note_specs('X45')

    def test_invalid_note_with_sharp_raises(self):
        with self.assertRaises(ValueError):
            parse_note_specs('B#45')

    def test_invalid_octave_zero_raises(self):
        with self.assertRaises(ValueError):
            parse_note_specs('A05')

    def test_empty_string_returns_empty(self):
        self.assertEqual(parse_note_specs(''), [])


class TestNoteFrequency(unittest.TestCase):

    def _freq(self, spec_str):
        return note_frequency(parse_note_specs(spec_str)[0])

    def test_a4_is_440(self):
        self.assertAlmostEqual(self._freq('A45'), 440.0, places=3)

    def test_a3_is_220(self):
        self.assertAlmostEqual(self._freq('A35'), 220.0, places=3)

    def test_a5_is_880(self):
        self.assertAlmostEqual(self._freq('A55'), 880.0, places=3)

    def test_c4_is_middle_c(self):
        self.assertAlmostEqual(self._freq('C45'), 261.626, places=2)

    def test_detune_1_is_no_shift(self):
        self.assertAlmostEqual(self._freq('A45'), self._freq('A41:1'), places=6)

    def test_detune_10_is_25_cents_sharp(self):
        base = self._freq('A41')
        detuned = note_frequency(parse_note_specs('A41:10')[0])
        expected_ratio = 2 ** (25 / 1200)
        self.assertAlmostEqual(detuned / base, expected_ratio, places=5)
