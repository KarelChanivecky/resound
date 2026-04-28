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
from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec
from matplotlib.lines import Line2D
from matplotlib.widgets import Button, TextBox


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
    _CTRL_BG         = '#111120'
    _NOTE_BG         = '#12122a'
    _NOTE_EDGE       = '#5599ff'
    _RAW_COLOR       = '#888888'
    _WINDOWED_COLOR  = '#4fc3f7'
    _SPECTRUM_COLOR  = '#4fc3f7'
    _THRESHOLD_COLOR = '#ffa726'
    _NOISE_ALPHA     = 0.12
    _PEAK_COLOR      = '#ef5350'
    _GRID_COLOR      = '#2a2a4a'
    _SEPARATOR_COLOR = '#3a3a6a'
    _TEXT_COLOR      = '#e0e0e0'
    _NOTE_COLOR      = '#ffffff'
    _ACCENT_COLOR    = '#4fc3f7'
    _BTN_COLOR       = '#1e1e3a'
    _BTN_HOVER       = '#2a2a5a'
    _INPUT_DELAY_MS  = 500

    def __init__(self, fft_size: int = 2048, sample_rate: int = 2500,
                 controls=None, control_values=None):
        self._fft_size   = fft_size
        self._nyquist    = sample_rate / 2
        self._controls = controls or {}
        self._control_values = control_values or {}
        self._control_widgets = []
        self._control_timers = {}
        self._dropdowns = []
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

    def set_fft_size(self, fft_size: int) -> None:
        self._fft_size = fft_size
        self._ax_time.set_xlim(0, fft_size - 1)
        self._fig.canvas.draw_idle()

    def set_sample_rate(self, sample_rate: int) -> None:
        self._nyquist = sample_rate / 2
        self._ax_freq.set_xlim(0, self._nyquist)
        self._fig.canvas.draw_idle()

    def set_controls(self, controls) -> None:
        self._controls = controls

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
        self._fig = plt.figure(figsize=(15, 8), facecolor=self._BG)
        self._fig.canvas.manager.set_window_title('Resound — real-time tuner')

        gs = GridSpec(
            3, 2, figure=self._fig,
            width_ratios=[3.5, 1.5],
            height_ratios=[2, 3, 1.4],
            hspace=0.45,
            wspace=0.28,
        )
        self._ax_time = self._fig.add_subplot(gs[0, 0])
        self._ax_freq = self._fig.add_subplot(gs[1, 0])
        self._ax_note = self._fig.add_subplot(gs[2, 0])
        self._setup_controls_panel(gs[:, 1])

        # Vertical separator between the plots and the controls sidebar.
        # width_ratios=[3.5, 1.5], wspace=0.28; with default subplot margins
        # (left≈0.125, right≈0.9) the gap between col-0 and col-1 sits near x≈0.74.
        self._fig.add_artist(Line2D(
            [0.74, 0.74], [0.04, 0.96],
            transform=self._fig.transFigure,
            color=self._SEPARATOR_COLOR,
            linewidth=1,
            solid_capstyle='butt',
        ))

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
            spine.set_edgecolor(self._NOTE_EDGE)
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
                facecolor=self._NOTE_BG,
                edgecolor=self._NOTE_EDGE,
                linewidth=2,
                alpha=0.9,
            ),
            animated=True)

    def _setup_controls_panel(self, spec):
        # 15 rows: 3 section-header axes + 9 control axes + 1 pause/play + 1 spacer
        # Layout: [0]=Signal header, [1..6]=Signal controls, [7]=Tuning header,
        #         [8]=A4, [9]=Source header, [10..11]=Max Hz / Step s,
        #         [12]=spacer, [13]=pause/play, [14]=spacer
        n_rows = 15
        control_grid = GridSpecFromSubplotSpec(
            n_rows, 1, subplot_spec=spec, hspace=0.7)
        axes = [self._fig.add_subplot(control_grid[i, 0]) for i in range(n_rows)]

        for ax in axes:
            ax.set_facecolor(self._CTRL_BG)
            ax.tick_params(left=False, bottom=False,
                           labelleft=False, labelbottom=False)
            for spine in ax.spines.values():
                spine.set_edgecolor(self._GRID_COLOR)

        def make_header(ax, title):
            ax.axis('off')
            ax.text(
                0.5, 0.5, title,
                transform=ax.transAxes,
                ha='center', va='center',
                color=self._SEPARATOR_COLOR,
                fontsize=7, fontstyle='italic',
            )

        values = self._control_values

        # ── Signal ──────────────────────────────────────────────────────────
        make_header(axes[0], '─── Signal ───')

        self._make_text_box(axes[1], 'FFT',
                            str(values.get('fft_size', self._fft_size)),
                            int, 'fft_size')
        self._make_dropdown(
            axes[2], 'Window',
            ('hann', 'hamming', 'blackman', 'blackmanharris',
             'boxcar', 'flattop', 'kaiser', 'tukey'),
            values.get('window', 'hann'), 'window')
        self._make_text_box(axes[3], 'Beta', str(values.get('beta', 5.0)),
                            float, 'beta')
        self._make_text_box(axes[4], 'Alpha', str(values.get('alpha', 0.5)),
                            float, 'alpha')
        self._make_text_box(axes[5], 'Z', str(values.get('zscore', 3.0)),
                            float, 'zscore')
        self._make_dropdown(
            axes[6], 'Norm', ('backward', 'ortho', 'forward'),
            values.get('fft_norm', 'backward'), 'fft_norm')

        # ── Tuning ──────────────────────────────────────────────────────────
        make_header(axes[7], '─── Tuning ───')

        self._make_text_box(axes[8], 'A4',
                            str(values.get('a4_frequency', 440.0)),
                            float, 'a4_frequency')

        # ── Source ──────────────────────────────────────────────────────────
        make_header(axes[9], '─── Source ───')

        self._make_text_box(axes[10], 'Max Hz',
                            str(values.get('recorder_target_frequency_max',
                                           int(self._nyquist))),
                            int, 'recorder_target_frequency_max')
        self._make_text_box(axes[11], 'Step s',
                            str(values.get('recorder_sample_duration', 0.05)),
                            float, 'recorder_sample_duration')

        self._make_text_box(axes[12], 'Amp Exp',
                            str(values.get('amp_exp', 1.0)),
                            float, 'amp_exp')

        # ── Pause / Play ────────────────────────────────────────────────────
        self._paused = False
        self._pause_btn = Button(
            axes[13], '⏸ Pause',
            color=self._BTN_COLOR,
            hovercolor=self._BTN_HOVER,
        )
        self._pause_btn.label.set_color(self._TEXT_COLOR)
        self._pause_btn.label.set_fontsize(8)
        self._pause_btn.on_clicked(self._toggle_pause)
        self._control_widgets.append(self._pause_btn)

        axes[14].axis('off')

    def _toggle_pause(self, _event):
        if self._paused:
            self._anim.resume()
            self._pause_btn.label.set_text('⏸ Pause')
            self._paused = False
        else:
            self._anim.pause()
            self._pause_btn.label.set_text('▶ Play')
            self._paused = True
        self._fig.canvas.draw_idle()

    def _make_text_box(self, ax, label, initial, parser, callback_name):
        text_box = TextBox(
            ax, label, initial=initial,
            color=self._CTRL_BG,
            hovercolor=self._GRID_COLOR,
            label_pad=0.02,
        )
        text_box.label.set_color(self._TEXT_COLOR)
        text_box.text_disp.set_color(self._TEXT_COLOR)
        text_box.on_submit(
            lambda value: self._submit_control(callback_name, parser, value))
        text_box.on_text_change(
            lambda value: self._schedule_control(callback_name, parser, value))
        self._control_widgets.append(text_box)

    def _make_dropdown(self, ax, label, options, initial, callback_name):
        ax.set_title(label, color=self._TEXT_COLOR, fontsize=8, pad=2)
        ax.tick_params(left=False, bottom=False,
                       labelleft=False, labelbottom=False)

        dropdown = {
            'main': Button(
                ax,
                f'{initial} v',
                color=self._CTRL_BG,
                hovercolor=self._GRID_COLOR,
            ),
            'option_values': options,
            'option_widgets': [],
            'open': False,
        }
        dropdown['main'].label.set_color(self._TEXT_COLOR)

        def toggle(_event):
            self._toggle_dropdown(dropdown)

        dropdown['main'].on_clicked(toggle)

        dropdown['callback_name'] = callback_name
        self._dropdowns.append(dropdown)
        self._control_widgets.append(dropdown['main'])

    def _toggle_dropdown(self, dropdown):
        if dropdown['open']:
            self._close_dropdown(dropdown)
        else:
            for other in self._dropdowns:
                self._close_dropdown(other)
            self._open_dropdown(dropdown)
        self._fig.canvas.draw_idle()

    def _open_dropdown(self, dropdown):
        if dropdown['open']:
            return

        parent = dropdown['main'].ax.get_position()
        option_height = min(parent.height, 0.035)
        dropdown['option_widgets'] = []

        for i, option in enumerate(dropdown['option_values']):
            option_ax = self._fig.add_axes([
                parent.x0,
                parent.y0 - option_height * (i + 1),
                parent.width,
                option_height,
            ])
            option_ax.set_zorder(10)
            button = Button(
                option_ax,
                option,
                color=self._CTRL_BG,
                hovercolor=self._GRID_COLOR,
            )
            button.label.set_color(self._TEXT_COLOR)
            button.label.set_fontsize(7)
            button.on_clicked(
                lambda _event, opt=option: self._select_dropdown(
                    dropdown, dropdown['callback_name'], opt))
            dropdown['option_widgets'].append((option_ax, button))
            self._control_widgets.append(button)

        dropdown['open'] = True

    def _close_dropdown(self, dropdown):
        if not dropdown['open']:
            return

        for option_ax, _button in dropdown['option_widgets']:
            option_ax.remove()
        dropdown['option_widgets'] = []
        dropdown['open'] = False

    def _select_dropdown(self, dropdown, callback_name, value):
        dropdown['main'].label.set_text(f'{value} v')
        self._close_dropdown(dropdown)
        self._run_control(callback_name, value)
        self._fig.canvas.draw_idle()

    def _submit_control(self, callback_name, parser, value):
        timer = self._control_timers.pop(callback_name, None)
        if timer is not None:
            timer.stop()
        try:
            parsed = parser(value)
        except ValueError:
            return
        self._run_control(callback_name, parsed)

    def _schedule_control(self, callback_name, parser, value):
        timer = self._control_timers.get(callback_name)
        if timer is not None:
            timer.stop()

        timer = self._fig.canvas.new_timer(interval=self._INPUT_DELAY_MS)

        def apply_value():
            self._control_timers.pop(callback_name, None)
            self._submit_control(callback_name, parser, value)
            return False

        timer.add_callback(apply_value)
        self._control_timers[callback_name] = timer
        timer.start()

    def _run_control(self, callback_name, value):
        callback = self._controls.get(callback_name)
        if callback is not None:
            callback(value)

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
