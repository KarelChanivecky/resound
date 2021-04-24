import threading as th
import sounddevice as soundd
from abstracts_interfaces.process import Process
from sound_sample import SoundSample


class RecorderProcess(Process):
    """
    Models an audio recorder. A threaded producer.

    Produces a SoundSample per production cycle.
    """
    __CHANNELS = 1
    __SAMPLE_TYPE = 'int32'

    def __init__(self, target_frequency_max=3000, sample_duration=1):
        """
        Construct an instance of recorder.

        Will determine sample rate from the given target_target_frequency_max as according to Nyquist's theorem.
        :param target_frequency_max: in Hz
        """
        self.__sample_rate = target_frequency_max * 2
        self.__sample_duration = sample_duration

    def run(self, _=None):
        """
        Record sound and pass to consumer.

        To be run threaded.
        :param _: unused
        """
        return self.get_sample()

    def get_sample(self):
        return SoundSample(self.__sample_rate, self.__sample_duration,
                           soundd.rec(int(self.__sample_rate * self.__sample_duration),
                                      self.__sample_rate, RecorderProcess.__CHANNELS,
                                      RecorderProcess.__SAMPLE_TYPE, blocking=True)[:, 0])
