
class Producer:
    """
    Models a threaded producer.

    1- User instantiates consumer
    2- Instantiates producer by passing consumer
    3- Invoke start_producing
        within:
        a) Invoke consumer.verify()
        b) Invoke your own logic
        c) pass produced object to produce
    """
    def __init__(self, consumer):
        self.consumer = consumer

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

    def __produce(self, obj):
        """
        Pass an object to consumer.
        :param obj: any
        """
        self.consumer.give(obj)

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