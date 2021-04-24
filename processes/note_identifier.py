import math

from abstracts_interfaces.abstract_consumer import AbstractConsumer
from musical_note import MusicalNote
from abstracts_interfaces.abstract_producer import AbstractProducer
import threading as th

SEMITONE_FREQ_RATIO = math.pow(2, 1 / 12)
SEMITONES_IN_SCALE = 12
INITIAL_OCTAVE = 4
DEFAULT_A4_FREQ = 440


def get_semitone_diff(freq, reference_freq):
    """
    Get the number of semitones away from freq1 relative to freq2.

    :param freq: float
    :param reference_freq: float
    :return: float
    """
    freq_ratio = freq / reference_freq
    return math.log(freq_ratio, SEMITONE_FREQ_RATIO)


def get_note(freq, A4_frequency):
    """
    Get a MusicalNote for a given frequency.

    :param freq: a double greater than 0
    :param A4_frequency: The frequency of A4
    :return: a MusicalNote
    """
    if freq < 0:
        return

    semitones_diff = get_semitone_diff(freq, A4_frequency)
    octave = INITIAL_OCTAVE
    full_octaves_from_A4 = int(semitones_diff / SEMITONES_IN_SCALE)
    octave += full_octaves_from_A4
    semitones_diff -= full_octaves_from_A4 * SEMITONES_IN_SCALE
    if semitones_diff < 0:
        octave -= 1
        semitones_diff = 12 + semitones_diff

    delta = semitones_diff - int(semitones_diff)
    semitones_diff = int(semitones_diff)
    if 0.5 < delta:
        delta = delta - 1
        semitones_diff += 1

    if 3 <= semitones_diff:
        octave += 1

    if semitones_diff == 12:
        semitones_diff = 0
    return MusicalNote(semitones_diff, octave, delta)


class NoteIdentifier(AbstractProducer, AbstractConsumer):
    """
    A consumer that identifies a musical note given a frequency.

    This NoteIdentifier uses the equal tempered scale of 12 semitones.
    The notes identified in reference to the frequency of A4, which by default is 440Hz.

    The difference in semitones between the given note and the reference is determined by the formula:
    diff(frG) = log(frG / frR) / log(2^(1/12))

    """

    CONSUMER_BUFFER_SIZE = 1024

    def __init__(self, consumer, A4_frequency=DEFAULT_A4_FREQ, buffer_size=CONSUMER_BUFFER_SIZE):
        """
        Construct instance of Frequency FrequencyExtractor.

        This class is a producer/consumer.

        :param consumer: The consumer of the data produced by this class
        """
        AbstractProducer.__init__(self, consumer)
        AbstractConsumer.__init__(self, buffer_size)
        self.__thread = th.Thread(target=self._consume)
        self.producing = False
        self.consuming = False
        self.A4_frequency = A4_frequency

    def _consume(self):
        """
        Consume from buffer.
        """
        # Consume the whole buffer when stopping
        while self.consuming or not (self._buffer.empty() and self.producing):
            self._producer_semaphore.acquire()
            freq = self._buffer.get()
            self._produce(get_note(freq, self.A4_frequency))
            self._consumer_semaphore.release()
        self.stop()

    def set_A4_frequency(self, new_A4_frequency):
        self.A4_frequency = new_A4_frequency

    def start(self):
        self.producing = True
        self._consumer.start()

    def stop(self):
        self.producing = False
        self._consumer.stop()

    def start(self):
        self.consuming = True
        self.start()
        self.__thread.start()

    def stop(self):
        self.consuming = False
