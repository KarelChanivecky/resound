import threading

from abstracts_interfaces.abstract_consumer import AbstractConsumer
from abstracts_interfaces.abstract_producer import AbstractProducer


class ThreadedProducer(AbstractProducer):
    """
    Models a threaded producer.
    """
    def __init__(self, consumer: AbstractConsumer, process):
        """
        Initializes a producer.

        :param consumer: A consumer to for the items produced
        :param process: a function that produces one item at a time
        """
        super().__init__(consumer, process)
        self.__thread = threading.Thread(target=self._produce, daemon=True)

    def start(self):
        """
        Start producing. Ensure to set consumer to start consuming.
        """
        self._running = True
        self.__thread.start()
        self._consumer.start()

    def stop(self):
        """
        Stop producing. Ensure to set consumer to stop consuming
        """
        self._running = False

    def _produce(self):
        """
        Produce items
        """
        while self._running:
            obj = self._process.run()
            self._consumer.give(obj)
