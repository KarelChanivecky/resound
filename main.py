from processes.frequency_extraction_process import FrequencyExtractionProcess
from processes.mock_consumer import MockConsumerProcess
from processes.note_identifier import NoteIdentifierProcess
from processes.recorder_process import RecorderProcess


def main():
    mock_consumer = MockConsumerProcess(100, 0)
    note_identifier = NoteIdentifierProcess(mock_consumer)
    freq_extractor = FrequencyExtractionProcess(note_identifier)
    recorder = RecorderProcess(freq_extractor, 2500, 0.5)
    recorder.start()


if __name__ == '__main__':
    main()
