"""
Real-time visualization window for the Resound pipeline.

Layout (GridSpec 3 rows)
------------------------
Row 0 — time domain waveform
  · light gray  : raw cropped samples (before normalization / windowing)
  · foreground  : windowed samples (after normalization and window function)

Row 1 — frequency spectrum (amplitudes normalized to [0, 1])
  · blue line   : FFT amplitude spectrum
  · orange fill : z-score noise floor (0 → threshold)
  · dashed line : z-score threshold
  · red scatter : detected peaks

Row 2 — identified note display
  · large boxed text : note name and cent offset

Performance
-----------
blit=True: only animated artists are redrawn each frame.  All axes limits are
set at construction time from fft_size and sample_rate so the static background
is stable and never needs a full redraw.
"""

import threading
import traceback

import numpy as np
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.gridspec import GridSpec


class ResoundGUI:
    """
    Thread-safe GUI driven by FuncAnimation at ~20 fps.

    fft_size and sample_rate must match the pipeline so that axis limits are
    correct from the first frame.  The pipeline calls give_peaks() and
    give_note() from its own threads; the animation callback reads the latest
    snapshot under a lock and repaints only the animated artists.
    """

    # Colour palette
    _BG              = '#1a1a2e'
    _AX_BG           = '#16213e'
    _NOTE_BG         = '#0e0e20'
    _RAW_COLOR       = '#888888'
    _WINDOWED_COLOR  = '#4fc3f7'
    _SPECTRUM_COLOR  = '#4fc3f7'
    _THRESHOLD_COLOR = '#ffa726'
    _NOISE_ALPHA     = 0.12
    _PEAK_COLOR      = '#ef5350'
    _GRID_COLOR      = '#2a2a4a'
    _TEXT_COLOR      = '#e0e0e0'
    _NOTE_COLOR      = '#ffffff'
    _ACCENT_COLOR    = '#4fc3f7'

    def __init__(self, fft_size: int = 2048, sample_rate: int = 2500):
        self._fft_size   = fft_size
        self._nyquist    = sample_rate / 2
        self._latest_peaks = None
        self._latest_note  = None
        self._lock = threading.Lock()
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
        self._fig = plt.figure(figsize=(12, 8), facecolor=self._BG)
        self._fig.canvas.manager.set_window_title('Resound — real-time tuner')

        gs = GridSpec(3, 1, figure=self._fig,
                      height_ratios=[2, 3, 1.4], hspace=0.45)
        self._ax_time = self._fig.add_subplot(gs[0])
        self._ax_freq = self._fig.add_subplot(gs[1])
        self._ax_note = self._fig.add_subplot(gs[2])

        self._setup_time_axis()
        self._setup_freq_axis()
        self._setup_note_axis()

        self._animated_artists = [
            self._line_raw,
            self._line_windowed,
            self._line_spectrum,
            self._threshold_line,
            self._scatter_peaks,
            self._noise_fill,
            self._note_text,
        ]

        self._anim = FuncAnimation(
            self._fig, self._update,
            init_func=self._init_anim,
            interval=50,
            blit=True,
            cache_frame_data=False)

    def _setup_time_axis(self):
        ax = self._ax_time
        ax.set_facecolor(self._AX_BG)
        ax.set_title('Waveform', color=self._TEXT_COLOR, fontsize=10, pad=6)
        ax.set_xlabel('Sample', color=self._TEXT_COLOR, fontsize=8)
        ax.set_ylabel('Amplitude', color=self._TEXT_COLOR, fontsize=8)
        ax.set_xlim(0, self._fft_size - 1)
        ax.set_ylim(-1.15, 1.15)
        ax.tick_params(colors=self._TEXT_COLOR, labelsize=7)
        ax.grid(color=self._GRID_COLOR, linewidth=0.5)
        for spine in ax.spines.values():
            spine.set_edgecolor(self._GRID_COLOR)

        self._line_raw, = ax.plot(
            [], [], color=self._RAW_COLOR, linewidth=0.8,
            alpha=0.6, label='raw', animated=True)
        self._line_windowed, = ax.plot(
            [], [], color=self._WINDOWED_COLOR, linewidth=1.0,
            label='windowed', animated=True)
        ax.legend(fontsize=7, facecolor=self._AX_BG,
                  labelcolor=self._TEXT_COLOR, loc='upper right')

    def _setup_freq_axis(self):
        ax = self._ax_freq
        ax.set_facecolor(self._AX_BG)
        ax.set_title('Spectrum', color=self._TEXT_COLOR, fontsize=10, pad=6)
        ax.set_xlabel('Frequency (Hz)', color=self._TEXT_COLOR, fontsize=8)
        ax.set_ylabel('Amplitude (norm)', color=self._TEXT_COLOR, fontsize=8)
        ax.set_xlim(0, self._nyquist)
        ax.set_ylim(0, 1.05)
        ax.tick_params(colors=self._TEXT_COLOR, labelsize=7)
        ax.grid(color=self._GRID_COLOR, linewidth=0.5)
        for spine in ax.spines.values():
            spine.set_edgecolor(self._GRID_COLOR)

        self._line_spectrum, = ax.plot(
            [], [], color=self._SPECTRUM_COLOR, linewidth=0.8, animated=True)
        self._threshold_line = ax.axhline(
            y=0, color=self._THRESHOLD_COLOR, linewidth=1.2,
            linestyle='--', alpha=0.85, label='z-score threshold', animated=True)
        self._scatter_peaks = ax.scatter(
            [], [], color=self._PEAK_COLOR, zorder=5, s=45,
            label='peaks', animated=True)
        self._noise_fill = ax.axhspan(
            0, 0, color=self._THRESHOLD_COLOR, alpha=self._NOISE_ALPHA,
            zorder=0, animated=True)

        ax.legend(fontsize=7, facecolor=self._AX_BG,
                  labelcolor=self._TEXT_COLOR, loc='upper right')

    def _setup_note_axis(self):
        ax = self._ax_note
        ax.set_facecolor(self._NOTE_BG)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.tick_params(left=False, bottom=False,
                       labelleft=False, labelbottom=False)
        for spine in ax.spines.values():
            spine.set_edgecolor(self._ACCENT_COLOR)
            spine.set_linewidth(1.5)

        self._note_text = ax.text(
            0.5, 0.5, '—',
            transform=ax.transAxes,
            ha='center', va='center',
            color=self._NOTE_COLOR,
            fontsize=42, fontweight='bold',
            fontfamily='monospace',
            bbox=dict(
                boxstyle='round,pad=0.35',
                facecolor='#1a1a4a',
                edgecolor=self._ACCENT_COLOR,
                linewidth=2,
                alpha=0.9,
            ),
            animated=True)

    # ------------------------------------------------------------------ #
    # Animation callbacks                                                  #
    # ------------------------------------------------------------------ #

    def _init_anim(self):
        self._line_raw.set_data([], [])
        self._line_windowed.set_data([], [])
        self._line_spectrum.set_data([], [])
        self._threshold_line.set_ydata([0, 0])
        self._scatter_peaks.set_offsets(np.empty((0, 2)))
        self._noise_fill.set_height(0)
        self._note_text.set_text('—')
        return self._animated_artists

    def _update(self, _frame):
        try:
            with self._lock:
                peaks = self._latest_peaks
                note  = self._latest_note

            if peaks is not None:
                self._draw_time_domain(peaks)
                self._draw_spectrum(peaks)
            self._draw_note(note)
        except Exception:
            traceback.print_exc()
            self._anim.event_source.stop()
            raise

        return self._animated_artists

    # ------------------------------------------------------------------ #
    # Per-frame draw helpers                                               #
    # ------------------------------------------------------------------ #

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

    def _draw_spectrum(self, peaks):
        amps     = peaks.amplitudes
        freq_res = peaks.freq_resolution
        freqs    = np.arange(len(amps)) * freq_res

        amp_max = float(amps.max())
        amps_norm = amps / amp_max if amp_max > 0 else amps
        self._line_spectrum.set_data(freqs, amps_norm)

        threshold = peaks.threshold
        if threshold is not None and amp_max > 0:
            t_norm = min(float(threshold) / amp_max, 1.0)
        else:
            t_norm = 0.0

        self._threshold_line.set_ydata([t_norm, t_norm])
        self._noise_fill.set_height(t_norm)

        valid_bins = [b for b in peaks.peak_bins if b >= 0]
        if valid_bins and amp_max > 0:
            pf = np.array([b * freq_res for b in valid_bins])
            pa = np.array([float(amps[b]) / amp_max for b in valid_bins])
            self._scatter_peaks.set_offsets(np.c_[pf, pa])
        else:
            self._scatter_peaks.set_offsets(np.empty((0, 2)))

    def _draw_note(self, note):
        self._note_text.set_text(str(note) if note is not None else '—')
