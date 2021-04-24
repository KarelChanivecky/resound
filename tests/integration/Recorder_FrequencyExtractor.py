from concrete_threading.threaded_consumer import ThreadedConsumer
from concrete_threading.threaded_consumer_producer import ThreadedConsumerProducer
from concrete_threading.threaded_producer import ThreadedProducer
from processes.frequency_extraction_process import FrequencyExtractionProcess
from processes.mock_consumer import MockConsumerProcess
from processes.recorder_process import RecorderProcess


def main():
    mock_consumer = ThreadedConsumer(10, MockConsumerProcess())
    freq_extractor = ThreadedConsumerProducer(10, mock_consumer, FrequencyExtractionProcess())
    recorder_process = RecorderProcess(2500, 0.5)
    record_producer = ThreadedProducer(freq_extractor, recorder_process)
    record_producer.start()


if __name__ == '__main__':
    main()
