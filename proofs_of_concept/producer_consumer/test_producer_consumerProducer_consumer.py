"""
These tests are meant for illustration purposes only.

The tests will fail a considerable amount of times due to the nature of multi-threading.
Careful analysis of the produced output will result in the affirmation of proper principle of functioning
"""


import io
import sys
import unittest.mock
from time import sleep
from unittest import TestCase

from proofs_of_concept.producer_consumer.concrete_consumer import ConcreteConsumer
from proofs_of_concept.producer_consumer.concrete_producer import ConcreteProducer
from proofs_of_concept.producer_consumer.concrete_producer_consumer import ConcreteProducerConsumer

CONSUMER_BUFFER = 3


class TestProducerConsumer(TestCase):
    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_fast_producer_slow_consumerProducer_fast_consumer(self, mock_stdout):
        consumer = ConcreteConsumer(CONSUMER_BUFFER, 0.1)
        producer_consumer = ConcreteProducerConsumer(consumer, CONSUMER_BUFFER, 1)
        producer = ConcreteProducer(producer_consumer, 0.1)
        producer.start_producing()
        expected_ten_lines = """Producer did it 1 times
Producer did it 2 times
Producer did it 3 times
consumer/producer did it 1
Producer did it 4 times
Consumer did it 1 times
consumer/producer did it 2
Consumer did it 2 times
Producer did it 5 times
consumer/producer did it 3
Consumer did it 3 times
Producer did it 6 times
consumer/producer did it 4
Consumer did it 4 times
Producer did it 7 times
consumer/producer did it 5
Consumer did it 5 times
Producer did it 8 times
"""
        sleep(6)
        producer.stop_producing()
        produced_out = mock_stdout.getvalue()
        produced_out_cropped = produced_out[0:len(expected_ten_lines)]
        sys.stderr.write(f"produced:\n {produced_out}\n")
        self.assertEqual(expected_ten_lines, produced_out_cropped)

    @unittest.mock.patch('sys.stdout', new_callable=io.StringIO)
    def test_slow_producer_fast_consumerProducer_fast_consumer(self, mock_stdout):
        consumer = ConcreteConsumer(CONSUMER_BUFFER, 0.1)
        producer_consumer = ConcreteProducerConsumer(consumer, CONSUMER_BUFFER, 0.1)
        producer = ConcreteProducer(producer_consumer, 1)
        producer.start_producing()
        expected_ten_lines = """Producer did it 1 times
consumer/producer did it 1
Consumer did it 1 times
Producer did it 2 times
consumer/producer did it 2
Consumer did it 2 times
Producer did it 3 times
consumer/producer did it 3
Consumer did it 3 times
Producer did it 4 times
consumer/producer did it 4
Consumer did it 4 times
Producer did it 5 times
consumer/producer did it 5
Consumer did it 5 times
Producer did it 6 times
consumer/producer did it 6
Consumer did it 6 times"""
        sleep(6)
        producer.stop_producing()
        produced_out = mock_stdout.getvalue()
        produced_out_cropped = produced_out[0:len(expected_ten_lines)]
        sys.stderr.write(f"expected:\n {expected_ten_lines}\n")
        sys.stderr.write(f"produced:\n {produced_out}\n")
        self.assertEqual(expected_ten_lines, produced_out_cropped)
