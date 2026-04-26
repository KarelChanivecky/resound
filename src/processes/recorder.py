try:
    import sounddevice as soundd
    _SOUNDDEVICE_AVAILABLE = True
except OSError:
    soundd = None
    _SOUNDDEVICE_AVAILABLE = False

from interfaces.process import Process
from sound_sample import SoundSample


class Recorder(Process):
    """
    Records audio from the microphone.

    Produces one SoundSample per call to run().
    Requires PortAudio (libportaudio2) at runtime; raises RuntimeError if unavailable.
    """
    __CHANNELS = 1
    __SAMPLE_TYPE = 'int32'

    def __init__(self, target_frequency_max=3000, sample_duration=1):
        """
        Construct a Recorder.

        Determines the sample rate from target_frequency_max per Nyquist's theorem.
        :param target_frequency_max: highest frequency to capture, in Hz
        :param sample_duration: recording length per sample, in seconds
        """
        self.__sample_rate = target_frequency_max * 2
        self.__sample_duration = sample_duration

    def run(self, _=None):
        return self.get_sample()

    def get_sample(self):
        if not _SOUNDDEVICE_AVAILABLE:
            raise RuntimeError(
                'Recorder requires PortAudio. '
                'Install it with: sudo apt-get install libportaudio2'
            )
        return SoundSample(self.__sample_rate, self.__sample_duration,
                           soundd.rec(int(self.__sample_rate * self.__sample_duration),
                                      self.__sample_rate, Recorder.__CHANNELS,
                                      Recorder.__SAMPLE_TYPE, blocking=True)[:, 0])
