import unittest

from pipeline.consumer_producer import ConsumerProducer
from interfaces.process import Process


class _Double(Process):
    def run(self, item=None):
        return item * 2


class _Identity(Process):
    def run(self, item=None):
        return item


class _CollectingConsumer:
    def __init__(self):
        self.items = []
        self.started = False
        self.stopped = False

    def give(self, item):
        self.items.append(item)

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True


class TestConsumerProducer(unittest.TestCase):

    # ------------------------------------------------------------------ #
    # give() — synchronous processing                                      #
    # ------------------------------------------------------------------ #

    def test_give_processes_item_and_forwards_result(self):
        sink = _CollectingConsumer()
        cp = ConsumerProducer(sink, _Double())
        cp.give(3)
        self.assertEqual(sink.items, [6])

    def test_give_forwards_none_result(self):
        sink = _CollectingConsumer()
        cp = ConsumerProducer(sink, _Identity())
        cp.give(None)
        self.assertEqual(sink.items, [None])

    def test_give_preserves_order(self):
        sink = _CollectingConsumer()
        cp = ConsumerProducer(sink, _Double())
        for n in [1, 2, 3, 4, 5]:
            cp.give(n)
        self.assertEqual(sink.items, [2, 4, 6, 8, 10])

    # ------------------------------------------------------------------ #
    # Lifecycle propagation                                                #
    # ------------------------------------------------------------------ #

    def test_start_propagates_to_downstream(self):
        sink = _CollectingConsumer()
        cp = ConsumerProducer(sink, _Identity())
        cp.start()
        self.assertTrue(sink.started)

    def test_stop_propagates_to_downstream(self):
        sink = _CollectingConsumer()
        cp = ConsumerProducer(sink, _Identity())
        cp.start()
        cp.stop()
        self.assertTrue(sink.stopped)

    # ------------------------------------------------------------------ #
    # Chaining                                                             #
    # ------------------------------------------------------------------ #

    def test_two_stages_chained(self):
        sink = _CollectingConsumer()
        second = ConsumerProducer(sink, _Double())
        first = ConsumerProducer(second, _Double())
        first.give(3)
        self.assertEqual(sink.items, [12])

    # ------------------------------------------------------------------ #
    # set_consumer                                                         #
    # ------------------------------------------------------------------ #

    def test_set_consumer_redirects_output(self):
        sink_a = _CollectingConsumer()
        sink_b = _CollectingConsumer()
        cp = ConsumerProducer(sink_a, _Identity())
        cp.give(1)
        cp.set_consumer(sink_b)
        cp.give(2)
        self.assertEqual(sink_a.items, [1])
        self.assertEqual(sink_b.items, [2])
