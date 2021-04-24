from abstracts_interfaces.abstract_consumer import AbstractConsumer
from abstracts_interfaces.abstract_producer import AbstractProducer
from abstracts_interfaces.process import Process


class AbstractConsumerProducer(AbstractConsumer, AbstractProducer):
    """
    Models an consumer/producer that can be chained with other AbstractConsumerProducer or AbstractConsumer or
    AbstractProducer
    """

    def __init__(self, buffer_size, consumer: AbstractConsumer, process: Process) -> None:
        AbstractConsumer.__init__(self, buffer_size, process)
        AbstractProducer.__init__(self, consumer, process)
        self._consumer = consumer

    def give(self, obj):
        super().give(obj)

    def _consume(self):
        super()._run()

    def start(self):
        super().start()

    def stop(self):
        super().stop()

    def set_consumer(self, consumer):
        super().set_consumer(consumer)
