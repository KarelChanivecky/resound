import threading

from abstracts_interfaces.abstract_consumer import AbstractConsumer
from abstracts_interfaces.abstract_consumer_producer import AbstractConsumerProducer
from abstracts_interfaces.process_interface import ProcessInterface


class ThreadedConsumerProducer(AbstractConsumerProducer):
    def __init__(self, buffer_size, consumer: AbstractConsumer, process: ProcessInterface) -> None:
        super().__init__(buffer_size, consumer, process)
        self._thread = threading.Thread(target=self._consume, daemon=True)

    def _consume(self):
        while self._consuming:
            self._producer_semaphore.acquire()
            item = self._buffer.get()
            obj = self._process.run(item)
            self._consumer_semaphore.release()

            self._consumer.give(obj)

    def start(self):
        self._consuming = True
        self._thread.start()

    def stop(self):
        self._consuming = False

    def set_consumer(self, consumer):
        super().set_consumer(consumer)

