import numpy as np

from interfaces.process import Process
from note_spec import NoteSpec, note_frequency
from sound_sample import SoundSample


class Synthesizer(Process):
    """
    Generates a synthetic SoundSample by summing sine waves for each NoteSpec.

    Optionally adds Gaussian noise at a specified SNR (dB).  snr=0 produces a
    clean signal with no noise.
    """

    def __init__(
            self,
            notes: list[NoteSpec],
            sample_rate: int,
            sample_duration: float = 0.5,
            snr: float = 0.0,
            a4_frequency: float = 440.0,
            seed: int | None = None,
    ) -> None:
        self.__notes = notes
        self.__sample_rate = sample_rate
        self.__sample_duration = sample_duration
        self.__snr = snr
        self.__a4_frequency = a4_frequency
        self.__rng = np.random.default_rng(seed)
        self.__sample_index = 0

    def run(self, _=None) -> SoundSample:
        return self._generate()

    def _generate(self) -> SoundSample:
        n = int(self.__sample_rate * self.__sample_duration)
        t = (np.arange(n) + self.__sample_index) / self.__sample_rate
        self.__sample_index += n

        signal = np.zeros(n, dtype=np.float64)
        for spec in self.__notes:
            freq = note_frequency(spec, self.__a4_frequency)
            amplitude = spec.intensity / 10.0
            signal += amplitude * np.sin(2.0 * np.pi * freq * t)

        if self.__snr > 0:
            signal_rms = np.sqrt(np.mean(signal ** 2))
            if signal_rms > 0:
                noise_rms = signal_rms / (10.0 ** (self.__snr / 20.0))
                signal += self.__rng.normal(0.0, noise_rms, n)

        max_amp = np.max(np.abs(signal))
        if max_amp > 0:
            signal /= max_amp

        samples = (signal * np.iinfo(np.int32).max).astype(np.int32)
        return SoundSample(self.__sample_rate, self.__sample_duration, samples)
