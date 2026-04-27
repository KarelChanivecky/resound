import threading
import unittest

from pipeline.threaded_t_producer_consumer import ThreadedTConsumerProducer


class _CollectingConsumer:
    """
    Test double for AbstractConsumer.

    Captures every item passed to give() and records start()/stop() calls.
    Uses a threading.Event to allow tests to block until expected items arrive.
    """

    def __init__(self):
        self.items = []
        self.started = False
        self.stopped = False
        self._lock = threading.Lock()
        self._event = threading.Event()

    def give(self, item):
        with self._lock:
            self.items.append(item)
        self._event.set()

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True

    def wait_for(self, count, timeout=1.0):
        """Block until at least count items have been collected, or timeout."""
        deadline = threading.Event()
        deadline.wait(timeout)  # used only as a clock; we poll below
        import time
        end = time.monotonic() + timeout
        while True:
            with self._lock:
                if len(self.items) >= count:
                    return
            if time.monotonic() >= end:
                raise AssertionError(
                    f'expected {count} item(s) within {timeout}s; '
                    f'got {len(self.items)}'
                )
            self._event.wait(timeout=0.005)
            self._event.clear()


class TestThreadedTConsumerProducer(unittest.TestCase):

    def _make_t(self, *consumers, buffer_size=10):
        return ThreadedTConsumerProducer(buffer_size, *consumers)

    # ------------------------------------------------------------------ #
    # Broadcast correctness                                                #
    # ------------------------------------------------------------------ #

    def test_single_consumer_receives_item(self):
        consumer = _CollectingConsumer()
        t = self._make_t(consumer)
        t.start()
        t.give('hello')
        consumer.wait_for(1)
        t.stop()
        self.assertEqual(consumer.items, ['hello'])

    def test_all_consumers_receive_item(self):
        a, b, c = _CollectingConsumer(), _CollectingConsumer(), _CollectingConsumer()
        t = self._make_t(a, b, c)
        t.start()
        t.give(42)
        for consumer in (a, b, c):
            consumer.wait_for(1)
        t.stop()
        self.assertEqual(a.items, [42])
        self.assertEqual(b.items, [42])
        self.assertEqual(c.items, [42])

    def test_each_consumer_receives_item_exactly_once(self):
        a, b = _CollectingConsumer(), _CollectingConsumer()
        t = self._make_t(a, b)
        t.start()
        t.give('x')
        a.wait_for(1)
        b.wait_for(1)
        t.stop()
        self.assertEqual(len(a.items), 1)
        self.assertEqual(len(b.items), 1)

    def test_sequence_of_items_delivered_in_order(self):
        items = [1, 2, 3, 4, 5]
        a, b = _CollectingConsumer(), _CollectingConsumer()
        t = self._make_t(a, b)
        t.start()
        for item in items:
            t.give(item)
        a.wait_for(len(items))
        b.wait_for(len(items))
        t.stop()
        self.assertEqual(a.items, items)
        self.assertEqual(b.items, items)

    # ------------------------------------------------------------------ #
    # Lifecycle propagation                                                #
    # ------------------------------------------------------------------ #

    def test_start_propagates_to_all_consumers(self):
        a, b, c = _CollectingConsumer(), _CollectingConsumer(), _CollectingConsumer()
        t = self._make_t(a, b, c)
        t.start()
        t.stop()
        self.assertTrue(a.started)
        self.assertTrue(b.started)
        self.assertTrue(c.started)

    def test_stop_propagates_to_all_consumers(self):
        a, b = _CollectingConsumer(), _CollectingConsumer()
        t = self._make_t(a, b)
        t.start()
        t.stop()
        self.assertTrue(a.stopped)
        self.assertTrue(b.stopped)
