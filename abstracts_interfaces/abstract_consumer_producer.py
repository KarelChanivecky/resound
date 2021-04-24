from abstract_consumer import AbstractConsumer
from abstract_producer import AbstractProducer
from process_interface import ProcessInterface


class AbstractConsumerProducer(AbstractConsumer, AbstractProducer):
    """
    Models an consumer/producer that can be chained with other AbstractConsumerProducer or AbstractConsumer or
    AbstractProducer
    """

    def __init__(self, buffer_size, consumer: AbstractConsumer, process: ProcessInterface) -> None:
        super().__init__(buffer_size, process)
        self._consumer = consumer

    def give(self, obj):
        super().give(obj)

    def _consume(self):
        super()._consume()

    def start(self):
        super().start()

    def stop(self):
        super().stop()

    def set_consumer(self, consumer):
        super().set_consumer(consumer)


