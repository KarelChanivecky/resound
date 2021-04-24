import threading

from abstracts_interfaces.abstract_consumer import AbstractConsumer
from abstracts_interfaces.abstract_producer import AbstractProducer
from abstracts_interfaces.process import Process


class ThreadedConsumerProducer(AbstractConsumer, AbstractProducer):
    def __init__(self, buffer_size, consumer: AbstractConsumer, process: Process) -> None:
        AbstractConsumer.__init__(self, buffer_size, process)
        AbstractProducer.__init__(self, consumer, process)
        self._thread = threading.Thread(target=self._consume, daemon=True)

    def _consume(self):
        while self._running:
            self._producer_semaphore.acquire()
            item = self._buffer.get()
            obj = self._process.run(item)
            self._consumer_semaphore.release()

            self._consumer.give(obj)

    def start(self):
        self._running = True
        self._consumer.start()
        self._thread.start()

    def stop(self):
        self._running = False

    def set_consumer(self, consumer):
        super().set_consumer(consumer)
