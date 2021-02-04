from time import sleep

from consumer import Consumer
from producer import Producer
import threading as th


class ConcreteProducerConsumer(Producer, Consumer):
    def __init__(self, consumer: Consumer, consumption_buffer_size, sleep_time):
        Producer.__init__(self, consumer)
        Consumer.__init__(self, consumption_buffer_size)
        self._thread = th.Thread(target=self._consume, daemon=True)
        self._producing = False
        self._consuming = False
        self._sleep_time = sleep_time

    def start_producing(self):
        self._producing = True

    def start_consuming(self):
        self._consuming = True
        self.start_producing()
        self._thread.start()
        self._consumer.start_consuming()

    def _consume(self):
        while self._consuming or self._producing and not len(self._buffer.empty()):
            self._producer_semaphore.acquire()
            times = self._buffer.get()
            sleep(self._sleep_time)
            print(f"consumer/producer did it {times}")
            self._consumer.give(times)
            self._consumer_semaphore.release()
        self.stop_producing()

    def stop_consuming(self):
        self._consuming = False

    def stop_producing(self):
        self._producing = False
        self._consumer.stop_consuming()
