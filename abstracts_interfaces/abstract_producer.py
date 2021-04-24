from abstract_consumer import AbstractConsumer
from process_interface import ProcessInterface


class AbstractProducer:
    """
    Interface for producer
    """
    def __init__(self, consumer: AbstractConsumer, process: ProcessInterface):
        self._consumer = consumer
        self._producing = False
        self._process = process

    def set_consumer(self, consumer):
        """
        Set the consumer for this producer
        :param consumer: a Consumer
        """
        if self._producing:
            raise RuntimeError("Cannot change consumer while producing")
        self._consumer = consumer

    def start(self):
        """
        Start producing. Ensure to set consumer to start consuming.
        """
        pass

    def stop(self):
        """
        Stop producing. Ensure to set consumer to stop consuming
        """
        pass

    def _produce(self):
        """
        Pass an object to consumer.
        :param obj: any
        """
        pass
