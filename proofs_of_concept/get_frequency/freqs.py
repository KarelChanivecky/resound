import sounddevice as soundd
import numpy as np
import scipy.signal.windows as wins
import matplotlib.pyplot as plt

SAMPLE_RATE = 5000
FFT_SIZE = 1024
FFT_TIME_RESOLUTION = FFT_SIZE / SAMPLE_RATE
FFT_FREQ_RESOLUTION = 1 / FFT_TIME_RESOLUTION
CHANNELS = 1


def get_sample():
    return soundd.rec(FFT_SIZE, SAMPLE_RATE, CHANNELS, 'int32', blocking=True)


def play_sample(sample):
    soundd.play(sample, SAMPLE_RATE)


def normalize_32b(samples):
    max_amp = max(samples.max(), abs(samples.min()))
    half_range = (2 ** 32 - 1) // 2
    return [(amp / max_amp) * half_range for amp in samples]


def get_fft(signal):
    n = len(signal)
    samples = signal[:, 0]
    normalized_samples = normalize_32b(samples)
    # window = wins.gaussian(FFT_SIZE, std=7, sym=True)
    window = wins.hann(FFT_SIZE, sym=False)
    windowed_samples = normalized_samples * window
    amplitudes = np.fft.rfft(windowed_samples)
    amplitudes[1:] = 2 * amplitudes[1:]
    amplitudes_real = np.abs(amplitudes)
    freqs = np.fft.rfftfreq(FFT_SIZE, 1/SAMPLE_RATE)
    fig, ax = plt.subplots()
    plt.plot(freqs, amplitudes_real, linewidth=5)
    ax.set_xscale('log')
    ax.set_yscale('log')
    plt.ylabel('Amplitude')
    plt.xlabel('Frequency [Hz]')
    plt.show()
    return amplitudes_real


def has_outlier(samples):
    print(f'@outliers: {samples}')
    THRESHOLD = samples[0] * 1.1
    print(f'threshold: {THRESHOLD}')
    print(f'{samples}')
    for sample in samples:
        if THRESHOLD < sample:
            print(f'outlier found: {sample}')
            return True
    return False


def evaluate_base_freq_mean(samples):
    accepted_samples = [samples.pop(0)]
    while 0 < len(samples) and not has_outlier(accepted_samples[:] + [samples[0]]):
        accepted_samples.append(samples.pop(0))
        print(f'accepted samples {accepted_samples}')
    return np.mean(accepted_samples)


def get_amplitude_low_bound(amplitudes):
    mean = np.mean(amplitudes)
    sd = np.std(amplitudes)
    return TARGET_Z_SCORE * sd + mean


def highpass_filter(samples):
    LOW_BOUND = 64
    while 0 < len(samples) and samples[0] < LOW_BOUND:
        samples.pop(0)


def get_dominant_freqs(freqs, amps):
    amplitude_low_bound = get_amplitude_low_bound([amp for amp in amps])
    resonant_freqs = [freq for freq, amp in zip(freqs, amps) if amplitude_low_bound < amp]
    highpass_filter(resonant_freqs)
    if len(resonant_freqs) == 0:
        return -1
    print(f'resonant freqs: {resonant_freqs}')
    return evaluate_base_freq_mean(resonant_freqs)


def get_max_bin(samples):
    max_bin = samples[0]
    max_bin_index = 0
    for i in range(0, len(samples) ):
        if max_bin < samples[i]:
            max_bin = samples[i]
            max_bin_index = i
    return max_bin_index


def gaussian_interpolation(samples):
    """
    Perform gaussian interpolation.

    :param samples: A list of tuples: (freq, amp). Must be length == 3, with max peak in the center
    :return: The frequency of the peak
    """
    max_bin = get_max_bin(samples)
    if max_bin == 0 or max_bin == len(samples):
        return -1
    top = np.log(samples[max_bin + 1] / samples[max_bin - 1])
    bottom = 2 * np.log(samples[max_bin] ** 2 /
                        (samples[max_bin + 1] * samples[max_bin - 1]))
    delta = top / bottom
    return FFT_FREQ_RESOLUTION * (delta + max_bin)


def main():
    while True:
        sample = get_sample()
        amps = get_fft(sample)
        # play_sample(sample)
        base_freq = gaussian_interpolation(amps)
        print(f'note: {base_freq}')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
