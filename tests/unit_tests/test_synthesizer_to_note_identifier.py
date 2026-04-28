"""
End-to-end unit tests: Synthesizer → FrequencyExtractor → NoteIdentifier.

No microphone is involved; all audio is synthetic.

MusicalNote encoding used by NoteIdentifier (semitones above A within the octave):
  A=0  A#=1  B=2  C=3  C#=4  D=5  D#=6  E=7  F=8  F#=9  G=10  G#=11
Notes at semitone >= 3 (C and above) increment the octave by 1.
"""

import unittest

import numpy as np

from note_spec import parse_note_specs
from processes.frequency_extractor import FrequencyExtractor
from processes.note_identifier import NoteIdentifier
from processes.synthesizer import Synthesizer

_SAMPLE_RATE = 5000  # Hz; Nyquist covers up to 2500 Hz (octaves 3–7 for most notes)
_SAMPLE_DURATION = 1.0  # seconds; gives 5000 samples >> default fft_size=2048


def _chain(specs_str, snr=0.0, fft_size=2048, z_score=3.0, seed=None):
    """Run the full pipeline on a synthetic sample and return the MusicalNote."""
    synth = Synthesizer(
        parse_note_specs(specs_str),
        sample_rate=_SAMPLE_RATE,
        sample_duration=_SAMPLE_DURATION,
        snr=snr,
        seed=seed,
    )
    sample = synth.run()
    freq = FrequencyExtractor(fft_size=fft_size, target_z_score=z_score).run(sample)
    return NoteIdentifier().run(freq)


class TestSynthesizerToNoteIdentifier(unittest.TestCase):

    # ------------------------------------------------------------------ #
    # 1. Single note, no noise                                             #
    # ------------------------------------------------------------------ #
    def test_single_note_no_noise(self):
        note = _chain('A45')  # A4, intensity 5
        self.assertEqual(note.get_semitone(), 0)  # A
        self.assertEqual(note.get_octave(), 4)

    # ------------------------------------------------------------------ #
    # 2. Single note, high noise                                           #
    # The z-score algorithm should still isolate the peak over Gaussian   #
    # noise at SNR = 10 dB.                                               #
    # ------------------------------------------------------------------ #
    def test_single_note_high_noise(self):
        note = _chain('A45', snr=10, seed=42)
        self.assertEqual(note.get_semitone(), 0)
        self.assertEqual(note.get_octave(), 4)

    # ------------------------------------------------------------------ #
    # 3. Three notes, one prominent                                        #
    # A3 is the loudest (intensity 9) and the lowest-frequency note.      #
    # All peaks appear above the z-score threshold; the algorithm returns  #
    # the first (lowest-frequency) peak → A3.                             #
    # ------------------------------------------------------------------ #
    def test_three_notes_one_prominent(self):
        # A3=220 Hz (intensity 9), B3=246 Hz (1), C4=261 Hz (1)
        note = _chain('A39,B31,C41')
        self.assertEqual(note.get_semitone(), 0)  # A
        self.assertEqual(note.get_octave(), 3)

    # ------------------------------------------------------------------ #
    # 4. Three notes, target is less prominent                             #
    # A3 is quieter (intensity 3) than B3 and C4 (intensity 5), but it   #
    # is still the lowest-frequency note.  The algorithm returns the first #
    # detected peak, so A3 is identified regardless of its amplitude.     #
    # ------------------------------------------------------------------ #
    def test_three_notes_target_less_prominent(self):
        # A3=220 Hz (intensity 3), B3=246 Hz (5), C4=261 Hz (5)
        note = _chain('A33,B35,C45')
        self.assertEqual(note.get_semitone(), 0)  # A
        self.assertEqual(note.get_octave(), 3)

    # ------------------------------------------------------------------ #
    # 5. Five notes: same note across three octaves + two slightly        #
    #    detuned + noise                                                   #
    # A3/A4/A5 form a harmonic series.  The two detuned notes are slight  #
    # variants of A4 (≈ 5–11 cents sharp) that merge with the A4 FFT bin. #
    # The algorithm returns the lowest-frequency peak → A3.               #
    # ------------------------------------------------------------------ #
    def test_five_notes_harmonics_detuned_with_noise(self):
        # A3 (220 Hz), A4 (440 Hz), A5 (880 Hz) at intensity 5
        # Two A4 variants detuned 5.6 and 11.1 cents sharp at intensity 3
        note = _chain('A35,A45,A55,A43:3,A43:5', snr=20, seed=0)
        self.assertEqual(note.get_semitone(), 0)  # A
        self.assertEqual(note.get_octave(), 3)


class TestSynthesizerPhaseContinuity(unittest.TestCase):
    """The end-sample phase of chunk N must equal the start-sample phase of chunk N+1."""

    def test_phase_continuous_across_chunks(self):
        synth = Synthesizer(
            parse_note_specs('A45'),
            sample_rate=_SAMPLE_RATE,
            sample_duration=_SAMPLE_DURATION,
        )
        chunk_a = synth.run().get_samples().astype(np.float64)
        chunk_b = synth.run().get_samples().astype(np.float64)
        # The step from the last sample of chunk A to the first of chunk B should
        # be the same size as a normal within-chunk step.
        within_step = abs(float(chunk_a[-1]) - float(chunk_a[-2]))
        boundary_step = abs(float(chunk_b[0]) - float(chunk_a[-1]))
        # Boundary step should be in the same ballpark as a normal step,
        # not a large jump back to zero.
        self.assertLess(boundary_step, within_step * 10)
