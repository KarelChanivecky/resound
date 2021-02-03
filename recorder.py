import threading as th
import sounddevice as soundd
from producer import Producer


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
        Producer.__init__(self, consumer)
        self.sample_rate = target_frequency_max * 2
        self.sample_duration = sample_duration
        self.thread = th.Thread(target=self.record)
        self.running = False
        super().__produce("dsgsd")

    def set_consumer(self, consumer):
        super().set_consumer(consumer)

    def start_producing(self):
        self.consumer.start_consuming()

    def stop_producing(self):
        self.running = False

    def record(self):
        """
        Record sound and pass to consumer.

        To be run threaded.
        """
        while self.running:
            self.consumer.verify()
            super().__produce(self.get_sample())

    def get_sample(self):
        return soundd.rec((self.sample_rate * self.sample_duration),
                          self.sample_rate, Recorder.__CHANNELS,
                          Recorder.__SAMPLE_TYPE)
