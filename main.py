from frequency_extractor import FrequencyExtractor
from mock_consumer import MockConsumer
from note_identifier import NoteIdentifier
from recorder import Recorder


def main():
    mock_consumer = MockConsumer(100, 0)
    note_identifier = NoteIdentifier(mock_consumer)
    freq_extractor = FrequencyExtractor(note_identifier)
    recorder = Recorder(freq_extractor, 2500, 0.5)
    recorder.start_producing()


if __name__ == '__main__':
    main()
