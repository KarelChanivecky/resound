import math

from interfaces.process import Process
from musical_note import MusicalNote

SEMITONE_FREQ_RATIO = math.pow(2, 1 / 12)
SEMITONES_IN_SCALE = 12
INITIAL_OCTAVE = 4
DEFAULT_A4_FREQ = 440


def get_semitone_diff(freq, reference_freq):
    """
    Get the number of semitones away from freq relative to reference_freq.

    :param freq: float
    :param reference_freq: float
    :return: float
    """
    freq_ratio = freq / reference_freq
    return math.log(freq_ratio, SEMITONE_FREQ_RATIO)


def identify_note(freq, a4_frequency):
    """
    Get a MusicalNote for a given frequency.

    :param freq: a double greater than 0
    :param a4_frequency: The frequency of A4
    :return: a MusicalNote
    """
    if freq < 0:
        return

    semitones_diff = get_semitone_diff(freq, a4_frequency)
    octave = INITIAL_OCTAVE
    full_octaves_from_a4 = int(semitones_diff / SEMITONES_IN_SCALE)
    octave += full_octaves_from_a4
    semitones_diff -= full_octaves_from_a4 * SEMITONES_IN_SCALE
    if semitones_diff < 0:
        octave -= 1
        semitones_diff = 12 + semitones_diff

    delta = semitones_diff - int(semitones_diff)
    semitones_diff = int(semitones_diff)
    if 0.5 < delta:
        delta = delta - 1
        semitones_diff += 1

    if 3 <= semitones_diff:
        octave += 1

    if semitones_diff == 12:
        semitones_diff = 0
    return MusicalNote(semitones_diff, octave, delta)


class NoteIdentifier(Process):
    """
    Identifies the musical note corresponding to a given frequency.

    Uses the equal-tempered scale of 12 semitones, with notes identified
    relative to A4 (440 Hz by default).

    The semitone distance from A4 is computed as:
    diff(f) = log(f / f_A4) / log(2^(1/12))
    """

    def __init__(self, a4_frequency=DEFAULT_A4_FREQ):
        """
        Construct a NoteIdentifier.

        :param a4_frequency: The reference frequency for A4 in Hz
        """
        self.a4_frequency = a4_frequency

    def run(self, freq=None):
        return identify_note(freq, self.a4_frequency)

    def set_a4_frequency(self, a4_frequency):
        self.a4_frequency = a4_frequency
