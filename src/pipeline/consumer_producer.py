from interfaces.abstract_consumer import AbstractConsumer
from interfaces.abstract_producer import AbstractProducer
from interfaces.process import Process


class ConsumerProducer(AbstractProducer):
    """
    A synchronous consumer-producer that processes items inline.

    Unlike ThreadedConsumerProducer, this stage runs entirely in the caller's
    thread: give() processes the item immediately and forwards the result to
    the downstream consumer before returning.  No buffer or semaphore is needed
    because there is no inter-thread handoff at this stage.

    Use this for lightweight transforms that do not warrant their own thread.
    Chain multiple ConsumerProducers together to compose a synchronous sub-pipeline
    that sits between two threaded stages.
    """

    def __init__(self, consumer: AbstractConsumer, process: Process) -> None:
        AbstractProducer.__init__(self, consumer, process)

    def give(self, item):
        result = self._process.run(item)
        self._consumer.give(result)

    def start(self):
        self._running = True
        self._consumer.start()

    def stop(self):
        self._running = False
        self._consumer.stop()
