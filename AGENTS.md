# Resound — Contribution Guide

## Goal

Make Resound a better demonstration of producer/consumer threading abstractions, applied statistics, and FFT signal processing. The musical tuner is the vehicle for those goals — not the end in itself.

## Learning Focus

- General, reusable producer/consumer threading pipeline
- Statistical peak detection (z-score) and sub-bin interpolation (Gaussian)
- FFT, windowing, and frequency domain analysis

## Rules

- One concern per PR
- Every new `Process` subclass needs unit tests
- Prefer synthetic audio tests over microphone hardware
- Do not change the threading or abstract hierarchy without an issue requesting it
- All PRs must pass CI (`pytest` from repo root)
- Prefer minimal changes

## Detailed Agent Instructions

See `CLAUDE.md` for architecture overview, design constraints, naming conventions, commit format, and the step-by-step agent workflow.
