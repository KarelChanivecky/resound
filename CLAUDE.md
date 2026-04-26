# Resound — Agent Instructions

## Project Purpose

Resound is a **learning project**, not a product. The musical instrument tuner is the concrete application used to exercise three learning goals:

1. **Producer/consumer abstractions** — designing a general, reusable threading pipeline where stages are decoupled and swappable
2. **Applied statistics** — z-score-based peak detection and Gaussian interpolation for sub-bin frequency resolution
3. **FFT and digital signal processing** — understanding windowing, spectral leakage, and frequency domain analysis

All code decisions should serve these goals. Improving tuner accuracy or adding UI is valuable only when it exercises one of the above. Do not optimise for the application at the expense of the abstractions.

---

## Architecture

```
src/
├── interfaces/       # Abstract contracts
│   ├── process.py              # Process — the Strategy interface; implement this for new domain logic
│   ├── runnable.py             # Runnable — lifecycle (start/stop/_run)
│   ├── abstract_consumer.py    # AbstractConsumer — semaphore-guarded buffer intake
│   └── abstract_producer.py    # AbstractProducer — pushes items to a downstream consumer
├── pipeline/         # Threaded, domain-agnostic pipeline stages
│   ├── threaded_consumer.py
│   ├── threaded_producer.py
│   └── threaded_consumer_producer.py
├── processes/        # Domain strategies (each implements Process)
│   ├── frequency_extractor.py  # FFT → fundamental frequency
│   ├── note_identifier.py      # frequency → MusicalNote
│   ├── recorder.py             # microphone → SoundSample
│   └── console_printer.py      # prints items to stdout (debug sink)
├── musical_note.py   # Data model: semitone index, octave, cent delta
├── sound_sample.py   # Data model: raw samples + sample rate + duration
└── main.py           # Wires the pipeline: Recorder → FrequencyExtractor → NoteIdentifier → ConsolePrinter
tests/
├── unit_tests/       # unittest suite — run with python -m unittest discover
└── integration/      # Manual scripts — require a microphone, not run in CI
proofs_of_concept/    # Exploratory code; not part of the main pipeline
```

**Key invariant:** `pipeline/` and `interfaces/` are domain-agnostic. They must never import from `processes/` or any domain module. All domain logic lives in `Process` subclasses in `processes/`.

---

## Design Rules

- **New domain logic** → create a `Process` subclass in `processes/`
- **`pipeline/` and `interfaces/`** must stay free of domain imports
- **Do not rewrite** the threading hierarchy or abstract contracts without explicit instruction
- **Strategy pattern** is the intended extension point — swap `Process` implementations without touching `ThreadedConsumer` / `ThreadedProducer`
- **Demonstrate, don't hide** — code should make the abstractions visible, not bury them in convenience wrappers

---

## Testing Rules

- Every new `Process` subclass needs unit tests in `tests/unit_tests/`
- Use synthetic audio (numpy-generated arrays) rather than microphone hardware in tests
- `tests/integration/` scripts are manual-only and are excluded from CI
- The full test suite runs with `PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"`
- Use Python 3.14t (free-threaded build) — without it the GIL serialises the pipeline threads and the concurrency model is not actually exercised

---

## Naming Conventions

- `snake_case` for modules, functions, methods, parameters, and local variables
- `PascalCase` for classes
- `UPPER_SNAKE_CASE` for module-level constants
- No redundant suffix on strategy classes — `FrequencyExtractor`, not `FrequencyExtractionProcess`
- Test classes named after what they test: `TestFrequencyExtractor`, not `Test`

---

## Commit Convention

```
TYPE: Short imperative description
```

| Type | When to use |
|------|-------------|
| `FT` | New feature or capability |
| `RF` | Refactor — behaviour unchanged |
| `FX` | Bug fix |
| `CI` | Build, config, or infrastructure |
| `DOC` | Documentation only |
| `WIP` | Checkpoint commit, work in progress |

---

## Agent Workflow

### Before starting work
1. Read every file you expect to touch
2. Run `PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"` and note how many tests pass — this is your baseline

### While working
3. New domain logic goes in `processes/` as a `Process` subclass
4. Do not add imports from `processes/` into `pipeline/` or `interfaces/`
5. Follow the naming conventions above
6. Keep changes minimal — do not refactor surrounding code unless that is the explicit task

### After finishing work
7. Run `PYTHONPATH=src python -m unittest discover -s tests -p "test_*.py"` — all tests that passed at baseline must still pass; new code must be covered
8. Commit using the `TYPE: description` format above
