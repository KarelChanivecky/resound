import queue
import threading


class Consumer:
    """
    Models a threaded consumer.
    """
    def __init__(self, buffer_size):
        self.buffer = queue.Queue()
        self.producer_semaphore = threading.Semaphore()
        self.consumer_semaphore = threading.Semaphore(buffer_size)

    def start_consuming(self):
        """
        Start consuming. To be called by producer.
        """
        pass

    def stop_consuming(self):
        """
        Stop consuming. To be called by producer.
        """
        pass

    def give(self, obj):
        """
        Give an object to this consumer. Must post to producer_semaphore
        :param obj: any
        """
        pass

    def verify(self):
        """
        Verify that consumer is ready to accept. Must wait on consumer_semaphore.
        """
        pass

    def __consume(self):
        """
        Consume from buffer. Must first wait on producer_semaphore. Once done, post to producer_semaphore.
        """
        pass
