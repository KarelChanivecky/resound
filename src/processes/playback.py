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
    Plays a SoundSample through the default audio output device.

    Requires PortAudio (libportaudio2).  Raises RuntimeError if the library is
    unavailable; raises whatever sounddevice raises if no output device can be
    opened.
    """

    def run(self, sound_sample: SoundSample = None):
        if not _SOUNDDEVICE_AVAILABLE:
            raise RuntimeError(
                'Playback requires PortAudio. '
                'Install it with: sudo apt-get install libportaudio2'
            )
        if sound_sample is None:
            return
        samples = sound_sample.get_samples().astype(np.float32) / np.iinfo(np.int32).max
        soundd.play(samples, sound_sample.get_sample_rate())
        soundd.wait()
