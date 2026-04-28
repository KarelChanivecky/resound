"""
Real-time visualization window for the Resound pipeline.

Layout
------
Top subplot    — time domain waveform
  · light gray  : raw cropped samples (before normalization / windowing)
  · foreground  : windowed samples (after normalization and window function)

Bottom subplot — frequency spectrum
  · blue line   : FFT amplitude spectrum
  · orange fill : z-score noise floor (0 → threshold)
  · dashed line : z-score threshold
  · red scatter : detected peaks

Text label (bottom subplot title) — identified note and tuning offset in cents.
"""

import threading

import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


class ResoundGUI:
    """
    Thread-safe GUI driven by FuncAnimation at ~20 fps.

    The pipeline calls give_peaks() and give_note() from its own threads.
    The animation callback reads the latest snapshot under a lock and repaints.
    """

    # Colour palette
    _BG            = '#1a1a2e'
    _AX_BG         = '#16213e'
    _RAW_COLOR     = '#888888'
    _WINDOWED_COLOR = '#4fc3f7'
    _SPECTRUM_COLOR = '#4fc3f7'
    _THRESHOLD_COLOR = '#ffa726'
    _NOISE_ALPHA   = 0.12
    _PEAK_COLOR    = '#ef5350'
    _GRID_COLOR    = '#2a2a4a'
    _TEXT_COLOR    = '#e0e0e0'
    _NOTE_COLOR    = '#ffffff'

    def __init__(self):
        self._latest_peaks = None
        self._latest_note  = None
        self._lock = threading.Lock()
        self._noise_fill = None
        self._setup_figure()

    # ------------------------------------------------------------------ #
    # Pipeline interface — called from pipeline threads                    #
    # ------------------------------------------------------------------ #

    def give_peaks(self, detected_peaks) -> None:
        with self._lock:
            self._latest_peaks = detected_peaks

    def give_note(self, note) -> None:
        with self._lock:
            self._latest_note = note

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #

    def run(self) -> None:
        """Start the matplotlib event loop. Blocks until the window is closed."""
        plt.show()

    # ------------------------------------------------------------------ #
    # Figure setup                                                         #
    # ------------------------------------------------------------------ #

    def _setup_figure(self):
        plt.style.use('dark_background')
        self._fig, (self._ax_time, self._ax_freq) = plt.subplots(
            2, 1, figsize=(12, 7), facecolor=self._BG)
        self._fig.canvas.manager.set_window_title('Resound — real-time tuner')
        self._fig.subplots_adjust(hspace=0.35)

        self._setup_time_axis()
        self._setup_freq_axis()

        self._anim = FuncAnimation(
            self._fig, self._update, interval=50,
            blit=False, cache_frame_data=False)

    def _setup_time_axis(self):
        ax = self._ax_time
        ax.set_facecolor(self._AX_BG)
        ax.set_title('Waveform', color=self._TEXT_COLOR, fontsize=10, pad=6)
        ax.set_xlabel('Sample', color=self._TEXT_COLOR, fontsize=8)
        ax.set_ylabel('Amplitude', color=self._TEXT_COLOR, fontsize=8)
        ax.set_ylim(-1.15, 1.15)
        ax.tick_params(colors=self._TEXT_COLOR, labelsize=7)
        ax.grid(color=self._GRID_COLOR, linewidth=0.5)
        for spine in ax.spines.values():
            spine.set_edgecolor(self._GRID_COLOR)

        self._line_raw, = ax.plot(
            [], [], color=self._RAW_COLOR, linewidth=0.8,
            alpha=0.6, label='raw')
        self._line_windowed, = ax.plot(
            [], [], color=self._WINDOWED_COLOR, linewidth=1.0,
            label='windowed')
        ax.legend(fontsize=7, facecolor=self._AX_BG,
                  labelcolor=self._TEXT_COLOR, loc='upper right')

    def _setup_freq_axis(self):
        ax = self._ax_freq
        ax.set_facecolor(self._AX_BG)
        ax.set_title('—', color=self._NOTE_COLOR, fontsize=16, pad=8, fontweight='bold')
        ax.set_xlabel('Frequency (Hz)', color=self._TEXT_COLOR, fontsize=8)
        ax.set_ylabel('Amplitude', color=self._TEXT_COLOR, fontsize=8)
        ax.tick_params(colors=self._TEXT_COLOR, labelsize=7)
        ax.grid(color=self._GRID_COLOR, linewidth=0.5)
        for spine in ax.spines.values():
            spine.set_edgecolor(self._GRID_COLOR)

        self._line_spectrum, = ax.plot(
            [], [], color=self._SPECTRUM_COLOR, linewidth=0.8)
        self._threshold_line = ax.axhline(
            y=0, color=self._THRESHOLD_COLOR, linewidth=1.2,
            linestyle='--', alpha=0.85, label='z-score threshold')
        self._scatter_peaks = ax.scatter(
            [], [], color=self._PEAK_COLOR, zorder=5, s=45, label='peaks')
        ax.legend(fontsize=7, facecolor=self._AX_BG,
                  labelcolor=self._TEXT_COLOR, loc='upper right')

    # ------------------------------------------------------------------ #
    # Animation callback                                                   #
    # ------------------------------------------------------------------ #

    def _update(self, _frame):
        with self._lock:
            peaks = self._latest_peaks
            note  = self._latest_note

        if peaks is not None:
            self._draw_time_domain(peaks)
            self._draw_spectrum(peaks)
        self._draw_note(note)

    def _draw_time_domain(self, peaks):
        ws = peaks.windowed_sample
        if ws is None:
            return

        n = len(ws.samples)
        x = np.arange(n)

        if ws.raw_samples is not None:
            raw_max = np.abs(ws.raw_samples).max()
            raw_norm = ws.raw_samples / raw_max if raw_max > 0 else ws.raw_samples
            self._line_raw.set_data(x, raw_norm)

        wind_max = np.abs(ws.samples).max()
        wind_norm = ws.samples / wind_max if wind_max > 0 else ws.samples
        self._line_windowed.set_data(x, wind_norm)
        self._ax_time.set_xlim(0, n - 1)

    def _draw_spectrum(self, peaks):
        amps     = peaks.amplitudes
        freq_res = peaks.freq_resolution
        freqs    = np.arange(len(amps)) * freq_res

        self._line_spectrum.set_data(freqs, amps)

        amp_max = float(amps.max())
        y_max   = amp_max * 1.18 if amp_max > 0 else 1.0
        self._ax_freq.set_xlim(0, float(freqs[-1]) if len(freqs) > 0 else 1.0)
        self._ax_freq.set_ylim(0, y_max)

        # Z-score noise floor band
        threshold = peaks.threshold
        if threshold is not None and threshold > 0:
            self._threshold_line.set_ydata([threshold, threshold])
            if self._noise_fill is not None:
                self._noise_fill.remove()
            self._noise_fill = self._ax_freq.fill_between(
                [0.0, float(freqs[-1])], 0, float(threshold),
                color=self._THRESHOLD_COLOR, alpha=self._NOISE_ALPHA,
                zorder=0)

        # Peak markers
        valid_bins = [b for b in peaks.peak_bins if b >= 0]
        if valid_bins:
            pf = np.array([b * freq_res for b in valid_bins])
            pa = np.array([float(amps[b]) for b in valid_bins])
            self._scatter_peaks.set_offsets(np.c_[pf, pa])
        else:
            self._scatter_peaks.set_offsets(np.empty((0, 2)))

    def _draw_note(self, note):
        label = str(note) if note is not None else '—'
        self._ax_freq.set_title(
            label, color=self._NOTE_COLOR, fontsize=16, pad=8, fontweight='bold')
