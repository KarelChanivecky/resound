import queue
import threading

from process_interface import ProcessInterface


class AbstractConsumer:
    """
    Interface for a consumer
    """

    def __init__(self, buffer_size, process: ProcessInterface) -> None:
        super().__init__()
        self._buffer = queue.Queue()
        self._producer_semaphore = threading.Semaphore()
        self._consumer_semaphore = threading.Semaphore(buffer_size)
        self._consuming = False
        self.process = process

    def give(self, obj):
        self._consumer_semaphore.acquire()
        self._buffer.put(obj)
        self._producer_semaphore.release()

    def _consume(self):
        pass

    def start(self):
        pass

    def stop(self):
        pass
