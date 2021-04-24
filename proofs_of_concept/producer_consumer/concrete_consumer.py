from time import sleep
from abstracts_interfaces.abstract_consumer import AbstractConsumer
import threading as th


class ConcreteConsumer(AbstractConsumer):
    def __init__(self, buffer_size, sleep_time):
        AbstractConsumer.__init__(self, buffer_size)
        self.thread = th.Thread(target=self._consume, daemon=True)
        self.sleep_time = sleep_time

    def _consume(self):
        while self._consuming:
            self._producer_semaphore.acquire()
            sleep(self.sleep_time)
            item = self._buffer.get()
            print(f"Consumer did it {item} times")
            self._consumer_semaphore.release()

    def start(self):
        self._consuming = True
        self.thread.start()
