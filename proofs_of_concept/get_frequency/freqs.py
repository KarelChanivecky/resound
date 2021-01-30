import sounddevice as soundd
import numpy as np
import matplotlib.pyplot as plt

SAMPLE_RATE = 5000
SAMPLE_DURATION = 1
CHANNELS = 1
TARGET_Z_SCORE = 3


def get_sample():
    return soundd.rec((SAMPLE_RATE * SAMPLE_DURATION), SAMPLE_RATE, CHANNELS, 'int32', blocking=True)


def play_sample(sample):
    soundd.play(sample, SAMPLE_RATE)


def get_fft(sample):
    n = len(sample)
    amplitudes = np.fft.fft(sample[:, 0])[0:int(n/2)] / n
    amplitudes[1:] = 2 * amplitudes[1:]
    amplitudes_real = np.abs(amplitudes)
    freqs = SAMPLE_RATE * np.arange((n / 2)) / n
    # fig, ax = plt.subplots()
    # plt.plot(freqs, amplitudes_real, linewidth=5)
    # ax.set_xscale('log')
    # ax.set_yscale('log')
    # plt.ylabel('Amplitude')
    # plt.xlabel('Frequency [Hz]')
    # plt.show()
    return freqs, amplitudes


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


def main():
    while True:
        sample = get_sample()
        freqs, amps = get_fft(sample)
        # play_sample(sample)
        base_freq = get_dominant_freqs(freqs, amps)
        print(f'note: {base_freq}')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
