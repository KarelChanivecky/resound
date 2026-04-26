import re
from dataclasses import dataclass

# Semitone distance above C within an octave (C=0 … B=11).
_SEMITONES_FROM_C = {
    'C': 0, 'C#': 1, 'D': 2, 'D#': 3, 'E': 4, 'F': 5,
    'F#': 6, 'G': 7, 'G#': 8, 'A': 9, 'A#': 10, 'B': 11,
}

_DETUNE_MAX_CENTS = 25.0
_DETUNE_RANGE = 9.0      # denominator: (10 - 1)

# Octave and intensity each range 1-10.  "10" must be tried before "[1-9]" so the
# regex engine matches the two-digit value greedily where present (e.g. "10" in
# "A105" is read as octave=10, not octave=1 + leftover "0").
_FIELD = r'(10|[1-9])'
_PATTERN = re.compile(rf'([A-G]#?){_FIELD}{_FIELD}(?::{_FIELD})?')


@dataclass(frozen=True)
class NoteSpec:
    note: str       # letter(s): 'A' … 'G', optionally followed by '#'
    octave: int     # 1–10
    intensity: int  # 1–10; maps linearly to amplitude 0.1 … 1.0
    detune: int     # 1–10; 1 = on-pitch, 10 = +25 cents sharp


def parse_note_specs(s: str) -> list[NoteSpec]:
    """
    Parse a comma-separated note-spec string into a list of NoteSpec objects.

    Format per note: <A-G>[#]<octave:1-10><intensity:1-10>[:<detune:1-10>]
    Examples: 'A45', 'C#310:5', 'A1010:10'
    """
    specs = []
    for token in s.split(','):
        token = token.strip()
        if not token:
            continue
        m = _PATTERN.fullmatch(token)
        if not m:
            raise ValueError(
                f'invalid note spec {token!r}; '
                f'expected <A-G>[#]<octave:1-10><intensity:1-10>[:<detune:1-10>]'
            )
        note = m.group(1)
        if note not in _SEMITONES_FROM_C:
            raise ValueError(
                f'unknown note {note!r}; '
                f'valid notes: C C# D D# E F F# G G# A A# B'
            )
        specs.append(NoteSpec(
            note=note,
            octave=int(m.group(2)),
            intensity=int(m.group(3)),
            detune=int(m.group(4)) if m.group(4) else 1,
        ))
    return specs


def note_frequency(spec: NoteSpec, a4_frequency: float = 440.0) -> float:
    """Return the frequency in Hz for a NoteSpec, including any detune offset."""
    semitone_from_a4 = (_SEMITONES_FROM_C[spec.note] - 9) + (spec.octave - 4) * 12
    detune_cents = (spec.detune - 1) / _DETUNE_RANGE * _DETUNE_MAX_CENTS
    total_semitones = semitone_from_a4 + detune_cents / 100.0
    return a4_frequency * (2.0 ** (total_semitones / 12.0))
