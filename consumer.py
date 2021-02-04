import queue
import threading


class Consumer:
    """
    Models a consumer.

    The purpose of this class is to implement a consumer that controls
    a buffer from overflowing or underflowing.

    You could just override _consume, but you probably want to override _consume and start_consuming.
    """

    def __init__(self, buffer_size):
        self._buffer = queue.Queue()
        self._producer_semaphore = threading.Semaphore()
        self._consumer_semaphore = threading.Semaphore(buffer_size)
        self._consuming = False

    def give(self, obj):
        """
        Give an object to this consumer. Must post to producer_semaphore
        :param obj: any
        """
        self._consumer_semaphore.acquire()
        self._buffer.put(obj)
        self._producer_semaphore.release()

    def _consume(self):
        """
        Consume from buffer. Must first wait on producer_semaphore. Once done, post to producer_semaphore.

        1- wait producer semaphore
        2- perform action
        3- post consumer semaphore
        """
        pass

    def start_consuming(self):
        self._consuming = True
        while self._consuming:
            self._producer_semaphore.acquire()
            self._consume()
            self._consumer_semaphore.release()

    def stop_consuming(self):
        self._consuming = False
