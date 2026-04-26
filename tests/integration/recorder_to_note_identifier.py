from pipeline.threaded_consumer import ThreadedConsumer
from pipeline.threaded_consumer_producer import ThreadedConsumerProducer
from pipeline.threaded_producer import ThreadedProducer
from processes.frequency_extractor import FrequencyExtractor
from processes.console_printer import ConsolePrinter
from processes.note_identifier import NoteIdentifier
from processes.recorder import Recorder


def main():
    console_printer = ThreadedConsumer(10, ConsolePrinter())
    note_identifier = ThreadedConsumerProducer(10, console_printer, NoteIdentifier())
    freq_extractor = ThreadedConsumerProducer(10, note_identifier, FrequencyExtractor())
    record_producer = ThreadedProducer(freq_extractor, Recorder(2500, 0.5))
    record_producer.start()


if __name__ == '__main__':
    main()
