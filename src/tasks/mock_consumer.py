from time import sleep
from abstracts_interfaces.abstract_consumer import AbstractConsumer
import threading as th

from abstracts_interfaces.process import Process


class MockConsumerProcess(Process):

    def run(self, item: any = None) -> any:
        print(f"MOCK CONSUMER:\n{item}")
