from time import sleep

from abstracts_interfaces.abstract_consumer import AbstractConsumer
from abstracts_interfaces.abstract_producer import AbstractProducer
import threading as th


class ConcreteProducerConsumer(AbstractProducer, AbstractConsumer):
    def __init__(self, consumer: AbstractConsumer, consumption_buffer_size, sleep_time):
        AbstractProducer.__init__(self, consumer)
        AbstractConsumer.__init__(self, consumption_buffer_size)
        self._thread = th.Thread(target=self._consume, daemon=True)
        self._producing = False
        self._consuming = False
        self._sleep_time = sleep_time

    def start(self):
        self._producing = True

    def start(self):
        self._consuming = True
        self.start()
        self._thread.start()
        self._consumer.start()

    def _consume(self):
        while self._consuming or self._producing and not len(self._buffer.empty()):
            self._producer_semaphore.acquire()
            times = self._buffer.get()
            sleep(self._sleep_time)
            print(f"consumer/producer did it {times}")
            self._consumer.give(times)
            self._consumer_semaphore.release()
        self.stop()

    def stop(self):
        self._consuming = False

    def stop(self):
        self._producing = False
        self._consumer.stop()
