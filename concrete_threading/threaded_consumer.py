import threading

from abstracts_interfaces.abstract_consumer import AbstractConsumer


class ThreadedConsumer(AbstractConsumer):
    """
        Models a consumer.

        The purpose of this class is to implement a consumer that controls
        a buffer from overflowing or under-flowing.

        You could just override _consume, but you probably want to override _consume,
        start_consuming, and stop_consuming.
        """

    def __init__(self, buffer_size, process):
        """
        Initializes the consumer.

        :param buffer_size: The consumption buffer size
        :param process:  A ProcessInterface
        """
        super().__init__(buffer_size, process)
        self._thread = threading.Thread(target=self._consume, daemon=True)

    def _consume(self):
        while self._consuming:
            self._producer_semaphore.acquire()
            item = self._buffer.get()
            self._process.run(item)
            self._consumer_semaphore.release()

    def start(self):
        self._consuming = True
        self._thread.start()

    def stop(self):
        self._consuming = False
