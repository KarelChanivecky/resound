# Resound

By: Karel Chanivecky Garcia

A Python project exploring **producer/consumer threading abstractions**, **statistical signal processing**, and **FFT-based frequency analysis** through the concrete problem of musical instrument tuning.

The tuner — recording audio, extracting the fundamental frequency, identifying the nearest note — is the vehicle for these learning goals, not an end in itself.

## What This Demonstrates

### Producer/consumer pipeline
Audio processing is decomposed into independent stages connected by semaphore-guarded queues. Each stage runs on its own thread. The pipeline infrastructure (`pipeline/`, `interfaces/`) is fully domain-agnostic: it knows nothing about audio, frequencies, or notes. Domain logic is injected via the Strategy pattern through the `Process` interface.

### Applied statistics
Frequency peaks are isolated by computing a z-score threshold against the background amplitude distribution, modelling the signal as a point source with high SNR over Gaussian noise. The candidate peak is then refined to sub-bin precision with Gaussian interpolation on the peak and its immediate neighbours.

### FFT and digital signal processing
A Hann window is applied to the sample before the FFT to reduce spectral leakage. The equal-tempered scale relationship between notes (a constant frequency ratio of 2^(1/12) per semitone) is used to map the identified frequency to the nearest note, with a cent-level delta for detuning.

## Architecture

```
src/
├── interfaces/    Abstract contracts — Process, Runnable, AbstractConsumer, AbstractProducer
├── pipeline/      Threaded pipeline — ThreadedConsumer, ThreadedProducer,
│                  ThreadedConsumerProducer, ThreadedTConsumerProducer
├── processes/     Domain strategies — FrequencyExtractor, NoteIdentifier,
│                  Recorder, Synthesizer, Playback, ConsolePrinter
├── musical_note.py    Data model (semitone index, octave, cent delta)
├── note_spec.py       Data model + parser for note-specification strings
├── sound_sample.py    Data model (raw samples, sample rate, duration)
└── main.py            Wires the pipeline
```

`pipeline/` and `interfaces/` have no imports from `processes/`. All domain-specific logic is encapsulated in `Process` subclasses and can be swapped without changing the threading layer.

`ThreadedTConsumerProducer` implements a T-junction: it consumes items from one upstream producer and fans them out unchanged to any number of downstream consumers. This is used to simultaneously feed the frequency-extraction chain and the audio playback consumer from the same audio source.

## Requirements

- Python 3.14t (free-threaded build, GIL disabled) — **recommended**; without it the pipeline stages share the GIL and the threaded implementation runs effectively single-threaded
- Python 3.11+ works for running the code but defeats the purpose of the threading model
- `libportaudio2` — required for microphone recording (`--source recorder`) and audio playback (`--playback`); install with `sudo apt-get install libportaudio2`. When absent, recorder and playback are disabled and raise `RuntimeError` at runtime; synth-only usage works without it.

## Installation

```bash
pip install -r requirements.txt
```

On Linux, also install the PortAudio system library if you need recorder or playback:

```bash
sudo apt-get install libportaudio2
```

## Usage

```bash
python src/main.py [options]
```

### Audio source

| Flag | Description |
|------|-------------|
| `--source recorder` | Record from the default microphone (default) |
| `--source synth` | Generate audio from a note specification (no hardware required) |
| `--notes SPEC` | Note spec for synth source — required with `--source synth` |
| `--snr DB` | Add Gaussian noise at this SNR in dB; `0` = no noise (default: `0`) |
| `--playback` | Play the synthesized audio through the default output device (synth only) |

**Note specification format:** `<note><octave><intensity>[:<detune>]`, comma-separated. Note is `A`–`G` with optional `#`; octave and intensity are `1`–`10`; detune is `1`–`10` (1 = no shift, 10 = 25 cents sharp).

```
A45           # A, octave 4, intensity 5, no detune
C#37:5        # C#, octave 3, intensity 7, mid detune
A45,C#37:5    # two notes played simultaneously
```

### Signal processing

| Flag | Default | Description |
|------|---------|-------------|
| `--fft-size N` | `2048` | FFT size in samples |
| `--zscore Z` | `3.0` | Z-score threshold for peak detection |
| `--fft-norm` | `backward` | `numpy.fft` normalisation: `backward`, `ortho`, or `forward` |
| `--window` | `hann` | Window function: `hann`, `hamming`, `blackman`, `blackmanharris`, `boxcar`, `flattop`, `kaiser`, `tukey` |
| `--beta BETA` | `5.0` | Shape parameter for the Kaiser window |
| `--alpha ALPHA` | `0.5` | Taper fraction for the Tukey window (0–1) |

### Examples

```bash
# Microphone tuner with default settings
python src/main.py

# Synthesize A4 and identify it (no hardware needed)
python src/main.py --source synth --notes A45

# Synthesize a chord with noise, play it back, and identify the dominant note
python src/main.py --source synth --notes A45,C#37:5,E46 --snr 20 --playback

# Tune with a larger FFT and a Kaiser window for lower spectral leakage
python src/main.py --fft-size 4096 --window kaiser --beta 8
```

Press `Ctrl+C` to stop.

## Running Tests

```bash
PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"
```

Unit tests cover frequency extraction (peak detection, Gaussian interpolation, amplitude thresholding), note identification, note-spec parsing, the Synthesizer, the T-junction pipeline stage, Playback, and console output. All tests use synthetic audio generated with NumPy — no microphone or audio hardware is required. Tests that depend on PortAudio are automatically skipped when `libportaudio2` is absent. Integration tests in `tests/integration/` are run manually and require hardware.

## Version History

- **0.7** — Synthesizer audio source; note-spec format; argparse CLI with configurable FFT/window parameters; T-junction pipeline stage; Playback process; graceful degradation when PortAudio is absent
- **0.65** — Refactored consumer/producer classes using multiple inheritance and the Strategy pattern to eliminate boilerplate
- **0.6** — Musical notes identified relative to a configurable reference pitch
- **0.5** — Core pipeline implemented: recording, frequency identification, and program entry point

## Roadmap

See [ROADMAP.md](ROADMAP.md).

## Bibliography

- Improving FFT resolution. J. Marsar. 2015<br>
  http://www.add.ece.ufl.edu/4511/references/ImprovingFFTResoltuion.pdf
- Improving FFT frequency measurement resolution by parabolic and gaussian interpolation. M. Gasior, J.L. Gonzalez. 2004.<br>
  https://mgasior.web.cern.ch/pap/FFT_resol_note.pdf
- Physics of Music - Notes. MTU. Accessed Mar 20, 2021.<br>
  https://pages.mtu.edu/~suits/notefreqs.html
  https://pages.mtu.edu/~suits/NoteFreqCalcs.html
