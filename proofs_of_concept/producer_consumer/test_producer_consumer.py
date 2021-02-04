import io
import sys
import unittest.mock
from time import sleep
from unittest import TestCase

from proofs_of_concept.producer_consumer.concrete_consumer import ConcreteConsumer
from proofs_of_concept.producer_consumer.concrete_producer import ConcreteProducer

CONSUMER_BUFFER = 3


class TestProducerConsumer(TestCase):
    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_fast_producer_slow_consumer(self, mock_stdout):
        consumer = ConcreteConsumer(CONSUMER_BUFFER, 1)
        producer = ConcreteProducer(consumer, 0.1)
        producer.start_producing()
        expected_ten_lines = """Producer did it 1 times
Producer did it 2 times
Producer did it 3 times
Consumer did it 1 times
Producer did it 4 times
Consumer did it 2 times
Producer did it 5 times
Consumer did it 3 times
Producer did it 6 times
Consumer did it 4 times
"""
        sleep(6)
        producer.stop_producing()
        produced_out = mock_stdout.getvalue()[0:len(expected_ten_lines)]
        self.assertEqual(expected_ten_lines, produced_out)

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_slow_producer_fast_consumer(self, mock_stdout):
        consumer = ConcreteConsumer(CONSUMER_BUFFER, 0.1)
        producer = ConcreteProducer(consumer, 1)
        producer.start_producing()
        expected_ten_lines = """Producer did it 1 times
Consumer did it 1 times
Producer did it 2 times
Consumer did it 2 times
Producer did it 3 times
Consumer did it 3 times
Producer did it 4 times
Consumer did it 4 times
Producer did it 5 times
Consumer did it 5 times
"""
        sleep(6)
        producer.stop_producing()
        produced_out = mock_stdout.getvalue()[0:len(expected_ten_lines)]
        sys.stderr.write(f"expected:\n {expected_ten_lines}\n")
        sys.stderr.write(f"produced:\n {produced_out}\n")
        self.assertEqual(expected_ten_lines, produced_out)
        pass
