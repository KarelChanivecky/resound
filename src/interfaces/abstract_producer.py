from interfaces.abstract_consumer import AbstractConsumer
from interfaces.process import Process
from interfaces.runnable import Runnable


class AbstractProducer(Runnable):
    """
    Interface for producer
    """

    def __init__(self, consumer: AbstractConsumer, process: Process):
        Runnable.__init__(self, process)
        self._consumer = consumer

    def set_consumer(self, consumer):
        """
        Set the consumer for this producer
        :param consumer: a Consumer
        """
        if self._running:
            raise RuntimeError("Cannot change consumer while producing")
        self._consumer = consumer
