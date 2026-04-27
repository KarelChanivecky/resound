import numpy as np

try:
    import sounddevice as soundd
    _SOUNDDEVICE_AVAILABLE = True
except OSError:
    soundd = None
    _SOUNDDEVICE_AVAILABLE = False

from interfaces.process import Process
from sound_sample import SoundSample


class Playback(Process):
    """
    Plays SoundSamples through the default audio output device as a continuous stream.

    Opens one OutputStream on the first call and writes subsequent samples into
    the same stream, eliminating the gap that would occur if a new stream were
    opened for every chunk.

    Requires PortAudio (libportaudio2).  Raises RuntimeError if the library is
    unavailable; raises whatever sounddevice raises if no output device can be
    opened.
    """

    def __init__(self):
        self._stream = None

    def run(self, sound_sample: SoundSample = None):
        if not _SOUNDDEVICE_AVAILABLE:
            raise RuntimeError(
                'Playback requires PortAudio. '
                'Install it with: sudo apt-get install libportaudio2'
            )
        if sound_sample is None:
            return
        samples = sound_sample.get_samples().astype(np.float32) / np.iinfo(np.int32).max
        if self._stream is None:
            self._stream = soundd.OutputStream(
                samplerate=sound_sample.get_sample_rate(),
                channels=1,
                dtype='float32',
            )
            self._stream.start()
        self._stream.write(samples)

    def __del__(self):
        if self._stream is not None and self._stream.active:
            self._stream.close()
