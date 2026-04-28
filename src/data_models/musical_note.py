import math

DELTA_EQ_TOLERANCE = 0.001

# Semitone index 0 = A, 1 = A#, 2 = B, 3 = C, ... (relative to the octave's A)
_NOTE_NAMES = ['A', 'A#', 'B', 'C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#']


class MusicalNote:
    """
    Models a musical note where the note value is given as the number of semitones above
    the previous A octave.

    Hence:
    where note is given as semitones, octave
    A5 is given as 0, 5
    C5 is given as 3, 5
    G#3 is given as 11, 3
    """

    def __init__(self, note, octave, delta) -> None:
        self._note = note
        self._octave = octave
        self._delta = delta

    def get_semitone(self):
        return self._note

    def get_octave(self):
        return self._octave

    def get_delta(self):
        return self._delta

    def __eq__(self, o) -> bool:
        if o.__class__ != self.__class__:
            return False
        if self._note != o.get_semitone():
            return False
        if self._octave != o.get_octave():
            return False
        if not math.isclose(self._delta, o.get_delta(), abs_tol=DELTA_EQ_TOLERANCE):
            return False
        return True

    def get_name(self) -> str:
        return f'{_NOTE_NAMES[self._note]}{self._octave}'

    def __str__(self) -> str:
        delta_cents = round(self._delta * 100)
        sign = '+' if delta_cents >= 0 else ''
        return f'{self.get_name()} ({sign}{delta_cents} cents)'
