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
├── pipeline/      Threaded pipeline — ThreadedConsumer, ThreadedProducer, ThreadedConsumerProducer
├── processes/     Domain strategies — FrequencyExtractor, NoteIdentifier, Recorder, ConsolePrinter
├── musical_note.py    Data model (semitone index, octave, cent delta)
├── sound_sample.py    Data model (raw samples, sample rate, duration)
└── main.py            Wires the pipeline
```

`pipeline/` and `interfaces/` have no imports from `processes/`. All domain-specific logic is encapsulated in `Process` subclasses and can be swapped without changing the threading layer.

## Requirements

- Python 3.14t (free-threaded build, GIL disabled) — **recommended**; without it the pipeline stages share the GIL and the threaded implementation runs effectively single-threaded
- Python 3.11+ works for running the code but defeats the purpose of the threading model
- A working microphone

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python src/main.py
```

Records audio from the default microphone and prints the closest musical note to the console. Press `Ctrl+C` to stop.

## Running Tests

```bash
pytest
```

Unit tests cover frequency extraction (peak detection, Gaussian interpolation, amplitude thresholding) and note identification. All tests use synthetic audio generated with NumPy; no microphone is required. Integration tests in `tests/integration/` are run manually.

## Version History

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
