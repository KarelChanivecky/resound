from concrete_threading.threaded_consumer import ThreadedConsumer
from concrete_threading.threaded_consumer_producer import ThreadedConsumerProducer
from concrete_threading.threaded_producer import ThreadedProducer
from processes.frequency_extraction_process import FrequencyExtractionProcess
from processes.mock_consumer import MockConsumerProcess
from processes.note_identifier import NoteIdentifierProcess
from processes.recorder_process import RecorderProcess


def main():
    mock_consumer = ThreadedConsumer(10, MockConsumerProcess())
    note_identifier = ThreadedConsumerProducer(10, mock_consumer, NoteIdentifierProcess())
    freq_extractor = ThreadedConsumerProducer(10, note_identifier, FrequencyExtractionProcess())
    record_producer = ThreadedProducer(freq_extractor, RecorderProcess(2500, 0.5))
    record_producer.start()


if __name__ == '__main__':
    main()
