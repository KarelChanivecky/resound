import threading

import numpy as np

try:
    import sounddevice as soundd
    _SOUNDDEVICE_AVAILABLE = True
except OSError:
    soundd = None
    _SOUNDDEVICE_AVAILABLE = False

from interfaces.process import Process
from ring_buffer import RingBuffer
from sound_sample import SoundSample

DEFAULT_SAMPLE_DURATION = 0.05
DEFAULT_FFT_SIZE = 2048


class Recorder(Process):
    """
    Records audio from the microphone.

    Produces one SoundSample per call to run().
    Requires PortAudio (libportaudio2) at runtime; raises RuntimeError if unavailable.
    """
    __CHANNELS = 1
    __SAMPLE_TYPE = 'int32'

    def __init__(self, target_frequency_max=3000, sample_duration=DEFAULT_SAMPLE_DURATION,
                 fft_size=DEFAULT_FFT_SIZE):
        """
        Construct a Recorder.

        Determines the sample rate from target_frequency_max per Nyquist's theorem.
        :param target_frequency_max: highest frequency to capture, in Hz
        :param sample_duration: recording length per blocking step, in seconds
        :param fft_size: minimum number of samples returned for FFT processing
        """
        self.__lock = threading.Lock()
        self.__target_frequency_max = target_frequency_max
        self.__sample_duration = sample_duration
        self.__fft_size = fft_size
        self.__stream = None
        self.__configure_buffers()

    def run(self, _=None):
        return self.get_sample()

    def set_target_frequency_max(self, target_frequency_max):
        with self.__lock:
            self.__close_stream()
            self.__target_frequency_max = target_frequency_max
            self.__configure_buffers()

    def set_sample_duration(self, sample_duration):
        with self.__lock:
            self.__close_stream()
            self.__sample_duration = sample_duration
            self.__configure_buffers()

    def set_fft_size(self, fft_size):
        with self.__lock:
            self.__fft_size = fft_size
            self.__configure_buffers()

    def get_sample(self):
        if not _SOUNDDEVICE_AVAILABLE:
            raise RuntimeError(
                'Recorder requires PortAudio. '
                'Install it with: sudo apt-get install libportaudio2'
            )

        with self.__lock:
            if not self.__ring.is_full():
                while not self.__ring.is_full():
                    self.__record_step()
            else:
                self.__record_step()

            samples = self.__ring.snapshot()
            sample_duration = len(samples) / self.__sample_rate
            return SoundSample(self.__sample_rate, sample_duration, samples)

    def close(self):
        with self.__lock:
            self.__close_stream()

    def __configure_buffers(self):
        self.__sample_rate = self.__target_frequency_max * 2
        self.__step_frames = max(1, int(self.__sample_rate * self.__sample_duration))
        self.__ring_frames = max(self.__step_frames, self.__fft_size)
        self.__recording = np.zeros((self.__step_frames, Recorder.__CHANNELS),
                                    dtype=Recorder.__SAMPLE_TYPE)
        self.__ring = RingBuffer(self.__ring_frames, dtype=Recorder.__SAMPLE_TYPE)

    def __record_step(self):
        self.__start_stream()
        block, _overflowed = self.__stream.read(self.__step_frames)
        self.__recording[:] = block
        self.__ring.write(self.__recording[:, 0])

    def __start_stream(self):
        if self.__stream is None:
            self.__stream = soundd.InputStream(
                samplerate=self.__sample_rate,
                channels=Recorder.__CHANNELS,
                dtype=Recorder.__SAMPLE_TYPE,
                blocksize=self.__step_frames,
            )
            self.__stream.start()

    def __close_stream(self):
        if self.__stream is not None:
            self.__stream.stop()
            self.__stream.close()
            self.__stream = None
