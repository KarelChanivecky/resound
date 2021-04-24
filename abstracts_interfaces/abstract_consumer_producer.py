from abstract_consumer import AbstractConsumer
from abstract_producer import AbstractProducer
from process_interface import ProcessInterface


class AbstractConsumerProducer(AbstractConsumer, AbstractProducer):
    """

    """

    def __init__(self, buffer_size, process: ProcessInterface) -> None:
        super().__init__(buffer_size, process)

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


