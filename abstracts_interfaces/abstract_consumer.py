import queue
import threading

from process_interface import ProcessInterface


class AbstractConsumer:
    """
    Interface for a consumer
    """

    def __init__(self, buffer_size, process: ProcessInterface) -> None:
        """
        Initialize a consumer.

        :param buffer_size: The size of the queue buffer for objects awaiting to be consumed
        :param process: The process by which the objects are consumed
        """
        super().__init__()
        self._buffer = queue.Queue()
        self._producer_semaphore = threading.Semaphore()
        self._consumer_semaphore = threading.Semaphore(buffer_size)
        self._consuming = False
        self._process = process

    def give(self, obj):
        """
        Give an object for processing to this consumer.

        May block if the buffer is full
        :param obj: any
        """
        self._consumer_semaphore.acquire()
        self._buffer.put(obj)
        self._producer_semaphore.release()

    def _consume(self):
        """
        Consume from buffer
        """
        pass

    def start(self):
        """
        Start consuming.
        """
        pass

    def stop(self):
        """
        Stop consuming
        """
        pass
