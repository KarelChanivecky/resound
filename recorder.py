import threading as th
import sounddevice as soundd
from producer import Producer
from SoundSample import SoundSample


class Recorder(Producer):
    """
    Models an audio recorder. A threaded producer.

    Produces a SoundSample per production cycle.
    """
    __CHANNELS = 1
    __SAMPLE_TYPE = 'int32'

    def __init__(self, consumer, target_frequency_max=3000, sample_duration=1):
        """
        Construct an instance.

        Will determine sample rate from the given target_target_frequency_max as according to Nyquist's theorem.
        :param consumer: a Consumer
        :param target_frequency_max: in Hz
        """
        super().__init__(consumer)
        self.__sample_rate = target_frequency_max * 2
        self.__sample_duration = sample_duration
        self.__thread = th.Thread(target=self.record, daemon=True)

    def set_consumer(self, consumer):
        super().set_consumer(consumer)

    def start_producing(self):
        self._producing = True
        self.__thread.start()
        self._consumer.start_consuming()

    def stop_producing(self):
        self._producing = False

    def record(self):
        """
        Record sound and pass to consumer.

        To be run threaded.
        """
        while self._producing:
            self._consumer.give(self.get_sample())

    def get_sample(self):
        return SoundSample(self.__sample_rate, self.__sample_duration,
                           soundd.rec(int(self.__sample_rate * self.__sample_duration),
                                      self.__sample_rate, Recorder.__CHANNELS,
                                      Recorder.__SAMPLE_TYPE, blocking=True)[:, 0])
