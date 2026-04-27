import threading
import typing

from interfaces.abstract_consumer import AbstractConsumer
from interfaces.process import Process


class ThreadedTProducerProcess(Process):
    """
    Internal broadcast strategy for ThreadedTConsumerProducer.

    Calls give() on every downstream consumer with the same item, implementing
    the fan-out leg of the T-junction.
    """

    def __init__(self, consumers: typing.Iterable[AbstractConsumer]) -> None:
        """
        :param consumers: All consumers that should receive each broadcast item.
        """
        self._consumers = consumers

    def run(self, item=None):
        """
        Give item to every consumer and return it unchanged.

        :param item: The item to broadcast.
        :return: item (pass-through).
        """
        for consumer in self._consumers:
            consumer.give(item)
        return item


class ThreadedTConsumerProducer(AbstractConsumer):
    """
    A T-junction pipeline stage: consumes items from an upstream producer and
    broadcasts each item unchanged to all downstream consumers.

    Runs on a single daemon thread.  All downstream consumers share the same
    item; none is designated as primary.  start() and stop() propagate to every
    downstream consumer.
    """

    def __init__(self, buffer_size, *consumers: AbstractConsumer) -> None:
        """
        :param buffer_size: Capacity of the input queue (number of unprocessed items
                            that can be held before back-pressure is applied to the
                            upstream producer).
        :param consumers:   One or more downstream consumers that will each receive
                            every item.
        """
        proc = ThreadedTProducerProcess(consumers)
        AbstractConsumer.__init__(self, buffer_size, proc)
        self._thread = threading.Thread(target=self._consume, daemon=True)
        self._t_consumers = consumers

    def _consume(self):
        """Daemon-thread body: drain the buffer and broadcast each item."""
        while self._running:
            self._producer_semaphore.acquire()
            item = self._buffer.get()
            self._process.run(item)
            self._consumer_semaphore.release()

    def start(self):
        """Start all downstream consumers, then begin consuming."""
        self._running = True
        for c in self._t_consumers:
            c.start()
        self._thread.start()

    def stop(self):
        """Stop all downstream consumers and halt the consume loop."""
        self._running = False
        for c in self._t_consumers:
            c.stop()
