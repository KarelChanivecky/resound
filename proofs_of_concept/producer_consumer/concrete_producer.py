import sys
from time import sleep

from producer import Producer
import threading as th


class ConcreteProducer(Producer):
    def __init__(self, consumer, sleep_time):
        super().__init__(consumer)
        self._thread = th.Thread(target=self.factory, daemon=True)
        self._sleep_time = sleep_time

    def start_producing(self):
        self._producing = True
        self._thread.start()
        self._consumer.start_consuming()

    def stop_producing(self):
        self._producing = False
        self._consumer.stop_consuming()

    def factory(self):
        index = 1
        while self._producing:
            sleep(self._sleep_time)
            self._consumer.give(index)
            print(f"Producer did it {index} times")
            index += 1

