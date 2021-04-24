import queue
import threading

from abstracts_interfaces.process import Process
from abstracts_interfaces.runnable import Runnable


class AbstractConsumer(Runnable):
    """
    Interface for a consumer
    """

    def __init__(self, buffer_size, process: Process) -> None:
        """
        Initialize a consumer.

        :param buffer_size: The size of the queue buffer for objects awaiting to be consumed
        :param process: The process by which the objects are consumed
        """
        Runnable.__init__(self, process)
        self._buffer = queue.Queue()
        self._producer_semaphore = threading.Semaphore()
        self._consumer_semaphore = threading.Semaphore(buffer_size)

    def give(self, obj):
        """
        Give an object for processing to this consumer.

        May block if the buffer is full
        :param obj: any
        """
        self._consumer_semaphore.acquire()
        self._buffer.put(obj)
        self._producer_semaphore.release()
