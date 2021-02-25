from time import sleep
import sys
from consumer import Consumer
import threading as th


class MockConsumer(Consumer):
    def __init__(self, buffer_size, sleep_time):
        Consumer.__init__(self, buffer_size)
        self.thread = th.Thread(target=self._consume, daemon=True)
        self.sleep_time = sleep_time

    def _consume(self):
        while self._consuming:
            self._producer_semaphore.acquire()
            sleep(self.sleep_time)
            item = self._buffer.get()
            print(f"MOCK CONSUMER:\n{item}")
            self._consumer_semaphore.release()

    def start_consuming(self):
        self._consuming = True
        self.thread.start()
