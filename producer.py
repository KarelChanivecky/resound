
class Producer:
    """
    Models a threaded producer.
    """
    def __init__(self):
        self.consumer = None

    def set_consumer(self, consumer):
        """
        Set the consumer for this producer
        :param consumer: a Consumer
        """
        self.consumer = consumer

    def start_producing(self):
        """
        Start producing. Ensure to set consumer to start consuming.
        """
        pass

    def stop_producing(self):
        """
        Stop producing. Ensure to set consumer to stop consuming
        """
        pass

    def __give_to_consumer(self, obj):
        """
        Give object to consumer
        :param obj: any
        """
        pass

    def __await_consumer(self):
        """
        Await for consumer to avoid buffer overflow.
        """
        pass