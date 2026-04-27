# Roadmap

## Signal processing

- **Empirical optimisation of FFT parameters and z-score threshold** — systematic evaluation of how FFT size, window choice, and z-score coefficient affect detection accuracy; now feasible without hardware using `--source synth` with controlled SNR
- **Polyphonic detection** — identify multiple simultaneous notes rather than only the lowest-frequency peak

## Application

- **Basic tuner UI** — visual display of the identified note and cent deviation

## Done

- **Configurable FFT and window parameters** — FFT size, window function, and per-window shape parameters exposed via CLI (`--fft-size`, `--window`, `--beta`, `--alpha`, `--zscore`, `--fft-norm`)
