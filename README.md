# Resound - A musical instrument tuner

By: Karel Chanivecky Garcia

Resound listens to your microphone and identifies the musical note being played in real time. It uses FFT-based frequency analysis with Gaussian interpolation and a threaded producer/consumer pipeline to keep recording, processing, and output stages decoupled.

## Requirements

- Python 3.11+
- A working microphone

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python src/main.py
```

The program captures audio from your default microphone, extracts the fundamental frequency using a windowed FFT, and prints the closest musical note to the console. Press `Ctrl+C` to stop.

## Running Tests

```bash
pytest
```

Unit tests cover frequency extraction (peak detection, Gaussian interpolation, amplitude thresholding) and musical note identification. Integration tests in `tests/integration/` require a microphone and are run manually.

## How It Works

1. **Recording** — `sounddevice` captures audio chunks from the microphone at a configurable sample rate and duration.
2. **Frequency extraction** — samples are normalized, a Hann window is applied to reduce spectral leakage, and an FFT is computed. Peaks above a z-score threshold are selected; the fundamental frequency is refined with Gaussian interpolation.
3. **Note identification** — the frequency is mapped to the nearest equal-temperament note (A4 = 440 Hz) with a cent-level delta.
4. **Threading** — stages run on independent threads connected by semaphore-guarded queues, implementing a producer/consumer pattern.

## Version History

- **0.65** — Refactored consumer/producer classes using multiple inheritance and the Strategy pattern to eliminate boilerplate
- **0.6** — Musical notes identified relative to a configurable reference pitch
- **0.5** — Core pipeline implemented: recording, frequency identification, and program entry point

## Roadmap

- Basic tuner UI
- Empirical optimization of frequency identification accuracy

## Known Limitations

- Not accurate enough for professional use; parameter tuning is ongoing

## Bibliography

- Improving FFT resolution. J. Marsar. 2015<br>
  http://www.add.ece.ufl.edu/4511/references/ImprovingFFTResoltuion.pdf
- Improving FFT frequency measurement resolution by parabolic and gaussian interpolation. M. Gasior, J.L. Gonzalez. 2004.<br>
  https://mgasior.web.cern.ch/pap/FFT_resol_note.pdf
- Physics of Music - Notes. MTU. Accessed Mar 20, 2021.<br>
  https://pages.mtu.edu/~suits/notefreqs.html
  https://pages.mtu.edu/~suits/NoteFreqCalcs.html