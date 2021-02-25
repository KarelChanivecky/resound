from frequency_extractor import FrequencyExtractor
from mock_consumer import MockConsumer
from recorder import Recorder


def main():
    mock_consumer = MockConsumer(100, 0)
    freq_extractor = FrequencyExtractor(mock_consumer)
    recorder = Recorder(freq_extractor, 2500, 0.5)
    recorder.start_producing()


if __name__ == '__main__':
    main()
