import argparse
import threading

import scipy.signal.windows as scipy_win

from pipeline.consumer_producer import ConsumerProducer
from pipeline.threaded_consumer import ThreadedConsumer
from pipeline.threaded_consumer_producer import ThreadedConsumerProducer
from pipeline.threaded_producer import ThreadedProducer
from pipeline.threaded_t_producer_consumer import ThreadedTConsumerProducer
from processes.amplitude_exponentiation import AmplitudeExponentiator
from processes.console_printer import ConsolePrinter
from processes.frequency_interpolator import FrequencyInterpolator
from processes.note_identifier import NoteIdentifier
from processes.peak_detector import PeakDetector
from processes.playback import Playback
from processes.recorder import Recorder
from processes.spectrum_analyzer import SpectrumAnalyzer
from processes.synthesizer import Synthesizer
from processes.windower import Windower
from note_spec import parse_note_specs

# GUI imports are deferred to avoid pulling in matplotlib when --gui is not used.
def _import_gui():
    from gui.resound_gui import ResoundGUI
    from processes.gui_process import PeaksGUIProcess, NoteGUIProcess
    return ResoundGUI, PeaksGUIProcess, NoteGUIProcess

_WINDOWS_WITH_NO_PARAMS = {'hann', 'hamming', 'blackman', 'blackmanharris', 'boxcar', 'flattop'}
_WINDOWS_ALL = _WINDOWS_WITH_NO_PARAMS | {'kaiser', 'tukey'}

# Recorder defaults use a short blocking step and an FFT-sized sliding window.
_DEFAULT_MAX_ANALYZED_FREQUENCY = 2500
_RECORDER_SAMPLE_RATE = _DEFAULT_MAX_ANALYZED_FREQUENCY * 2
_RECORDER_SAMPLE_DURATION = 0.05
_SYNTH_SAMPLE_RATE = 5000
_SYNTH_SAMPLE_DURATION = 0.5


def _positive_int(value):
    n = int(value)
    if n <= 0:
        raise argparse.ArgumentTypeError(f'must be greater than 0, got {value}')
    return n


def _nonneg_float(value):
    x = float(value)
    if x < 0:
        raise argparse.ArgumentTypeError(f'must be >= 0, got {value}')
    return x


def _parse_args(args=None):
    p = argparse.ArgumentParser(
        description='Resound — musical instrument tuner',
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Audio source
    p.add_argument('--source', choices=['recorder', 'synth'], default='recorder',
                   help='audio source: microphone recorder or synthesizer (default: recorder)')
    p.add_argument('--notes', default=None, metavar='SPEC',
                   help=(
                       'one or more comma-separated note specs (required with --source synth)\n'
                       '\n'
                       '  format:    <note><octave><intensity>[:<detune>]\n'
                       '  note:      A B C D E F G — sharps: A# C# D# F# G#\n'
                       '  octave:    1–10\n'
                       '  intensity: 1–10  (relative amplitude; 10 = loudest)\n'
                       '  detune:    1–10, optional  (1 = in tune, 10 = +25 cents sharp)\n'
                       '\n'
                       '  examples:\n'
                       '    A45          A, octave 4, intensity 5, in tune\n'
                       '    C#37:5       C#, octave 3, intensity 7, ~14 cents sharp\n'
                       '    A45,E45      A4 and E4 played simultaneously\n'
                   ))
    p.add_argument('--snr', type=_nonneg_float, default=0.0, metavar='DB',
                   help='signal-to-noise ratio in dB for synth noise; 0 = no noise (default: 0)')
    p.add_argument('--playback', action='store_true',
                   help='play the synthesized audio through the default output device '
                        '(only valid with --source synth)')

    # FFT / signal-processing parameters
    p.add_argument('--fft-size', type=_positive_int, default=2048, metavar='N',
                   help='FFT size in samples, must be > 0 (default: 2048)')
    p.add_argument('--zscore', type=_nonneg_float, default=3.0, metavar='Z',
                   help='z-score threshold for peak detection, must be >= 0 (default: 3.0)')
    p.add_argument('--fft-norm', choices=['backward', 'ortho', 'forward'],
                   default='backward',
                   help='numpy.fft normalisation mode (default: backward)')
    p.add_argument('--window', choices=sorted(_WINDOWS_ALL), default='hann',
                   help='scipy window function (default: hann)')
    p.add_argument('--beta', type=float, default=5.0, metavar='BETA',
                   help='shape parameter for the kaiser window (default: 5.0)')
    p.add_argument('--alpha', type=float, default=0.5, metavar='ALPHA',
                   help='taper fraction for the tukey window, 0..1 (default: 0.5)')
    p.add_argument('--amp-exp', type=_nonneg_float, default=1.0, metavar='E',
                   help='amplitude exponent for dynamic-range shaping, must be >= 0 (default: 1.0)')
    p.add_argument('--gui', action='store_true',
                   help='show the real-time visualization window')

    namespace = p.parse_args(args)

    if namespace.source == 'synth' and namespace.notes is None:
        p.error('--notes is required when --source is synth')
    if namespace.playback and namespace.source != 'synth':
        p.error('--playback is only supported with --source synth')

    return namespace


def _make_window(window_name, fft_size, beta, alpha):
    if window_name == 'kaiser':
        window_spec = ('kaiser', beta)
    elif window_name == 'tukey':
        window_spec = ('tukey', alpha)
    else:
        window_spec = window_name
    return scipy_win.get_window(window_spec, fft_size, fftbins=True)


def _fft_size_for_max_analyzed_frequency(max_frequency, reference_fft_size,
                                         reference_max_frequency=_DEFAULT_MAX_ANALYZED_FREQUENCY):
    return max(64, int(round(reference_fft_size * max_frequency / reference_max_frequency)))


def _build_window(args):
    return _make_window(args.window, args.fft_size, args.beta, args.alpha)


def _build_audio_source(args):
    if args.source == 'synth':
        notes = parse_note_specs(args.notes)
        # Guarantee the sample has at least fft_size samples so windowing never fails.
        min_duration = args.fft_size / _SYNTH_SAMPLE_RATE
        sample_duration = max(_SYNTH_SAMPLE_DURATION, min_duration)
        return Synthesizer(notes, _SYNTH_SAMPLE_RATE, sample_duration, snr=args.snr)
    return Recorder(_DEFAULT_MAX_ANALYZED_FREQUENCY, _RECORDER_SAMPLE_DURATION, args.fft_size)


def _build_gui_controls(args, source, gui, windower, peak_detector,
                        spectrum_analyzer, note_identifier, amplitude_exp_process):
    state = {
        'fft_size': args.fft_size,
        'reference_fft_size': args.fft_size,
        'max_analyzed_frequency': _DEFAULT_MAX_ANALYZED_FREQUENCY,
        'window': args.window,
        'beta': args.beta,
        'alpha': args.alpha,
    }

    def _set_window():
        window = _make_window(
            state['window'],
            state['fft_size'],
            state['beta'],
            state['alpha'],
        )
        windower.set_window(window)

    def _set_fft_size(fft_size):
        state['fft_size'] = int(fft_size)
        _set_window()
        if hasattr(source, 'set_fft_size'):
            source.set_fft_size(state['fft_size'])
        if hasattr(gui, 'set_analysis_range'):
            gui.set_analysis_range(state['max_analyzed_frequency'], state['fft_size'])
        else:
            gui.set_sample_rate(state['max_analyzed_frequency'] * 2)
            gui.set_fft_size(state['fft_size'])

    def set_max_analyzed_frequency(value):
        max_frequency = int(value)
        if max_frequency <= 0:
            return
        state['max_analyzed_frequency'] = max_frequency
        if hasattr(source, 'set_target_frequency_max'):
            source.set_target_frequency_max(max_frequency)
        fft_size = _fft_size_for_max_analyzed_frequency(
            max_frequency,
            state['reference_fft_size'],
        )
        _set_fft_size(fft_size)

    def set_window(value):
        state['window'] = value
        _set_window()

    def set_beta(value):
        state['beta'] = float(value)
        _set_window()

    def set_alpha(value):
        state['alpha'] = float(value)
        _set_window()

    def set_zscore(value):
        zscore = float(value)
        if zscore >= 0:
            peak_detector.set_target_z_score(zscore)

    def set_fft_norm(value):
        spectrum_analyzer.set_norm(None if value == 'backward' else value)

    def set_a4_frequency(value):
        a4_frequency = float(value)
        if a4_frequency > 0:
            note_identifier.set_a4_frequency(a4_frequency)

    def set_recorder_sample_duration(value):
        sample_duration = float(value)
        if sample_duration > 0 and hasattr(source, 'set_sample_duration'):
            source.set_sample_duration(sample_duration)

    def set_amp_exp(value):
        exp = float(value)
        if exp >= 0:
            amplitude_exp_process.set_exponent(exp)

    return {
        'max_analyzed_frequency': set_max_analyzed_frequency,
        'window': set_window,
        'beta': set_beta,
        'alpha': set_alpha,
        'zscore': set_zscore,
        'fft_norm': set_fft_norm,
        'a4_frequency': set_a4_frequency,
        'recorder_sample_duration': set_recorder_sample_duration,
        'amp_exp': set_amp_exp,
    }


def main(_stop_event=None):
    args = _parse_args()
    norm = None if args.fft_norm == 'backward' else args.fft_norm
    window = _build_window(args)

    console_printer = ThreadedConsumer(10, ConsolePrinter())
    source = _build_audio_source(args)
    windower_process = Windower(fft_size=args.fft_size, window=window)
    spectrum_analyzer_process = SpectrumAnalyzer(norm=norm)
    amplitude_exp_process = AmplitudeExponentiator(exponent=args.amp_exp)
    peak_detector_process = PeakDetector(target_z_score=args.zscore)
    note_identifier_process = NoteIdentifier()

    if args.gui:
        ResoundGUI, PeaksGUIProcess, NoteGUIProcess = _import_gui()
        sample_rate = _SYNTH_SAMPLE_RATE if args.source == 'synth' else _RECORDER_SAMPLE_RATE
        gui = ResoundGUI(
            fft_size=args.fft_size,
            sample_rate=sample_rate,
            control_values={
                'fft_size': args.fft_size,
                'window': args.window,
                'beta': args.beta,
                'alpha': args.alpha,
                'zscore': args.zscore,
                'fft_norm': args.fft_norm,
                'a4_frequency': 440.0,
                'max_analyzed_frequency': _DEFAULT_MAX_ANALYZED_FREQUENCY,
                'recorder_sample_duration': _RECORDER_SAMPLE_DURATION,
                'amp_exp': args.amp_exp,
            },
        )
        gui.set_controls(
            _build_gui_controls(
                args,
                source,
                gui,
                windower_process,
                peak_detector_process,
                spectrum_analyzer_process,
                note_identifier_process,
                amplitude_exp_process,
            )
        )

        # Fan note output to both ConsolePrinter and the GUI note display.
        note_gui       = ThreadedConsumer(2, NoteGUIProcess(gui))
        note_sink      = ThreadedTConsumerProducer(4, console_printer, note_gui)
        note_identifier = ThreadedConsumerProducer(10, note_sink, note_identifier_process)

        # Fan peak output to FrequencyInterpolator chain and the GUI spectrum display.
        freq_interpolator = ConsumerProducer(note_identifier, FrequencyInterpolator())
        peaks_gui  = ThreadedConsumer(2, PeaksGUIProcess(gui))
        peaks_sink = ThreadedTConsumerProducer(4, freq_interpolator, peaks_gui)
        peak_detector     = ConsumerProducer(peaks_sink, peak_detector_process)
    else:
        note_identifier   = ThreadedConsumerProducer(10, console_printer, note_identifier_process)
        freq_interpolator = ConsumerProducer(note_identifier, FrequencyInterpolator())
        peak_detector     = ConsumerProducer(freq_interpolator, peak_detector_process)

    amplitude_exp     = ConsumerProducer(peak_detector, amplitude_exp_process)
    spectrum_analyzer = ConsumerProducer(amplitude_exp, spectrum_analyzer_process)
    windower = ThreadedConsumerProducer(
        10, spectrum_analyzer, windower_process)
    if args.playback:
        playback_consumer = ThreadedConsumer(2, Playback())
        upstream = ThreadedTConsumerProducer(10, windower, playback_consumer)
    else:
        upstream = windower
    record_producer = ThreadedProducer(upstream, source)
    record_producer.start()

    if args.gui:
        try:
            gui.run()           # blocks in the matplotlib event loop
        finally:
            record_producer.stop()
            if isinstance(source, Recorder):
                source.close()
    else:
        stop_event = _stop_event if _stop_event is not None else threading.Event()
        try:
            stop_event.wait()
        except KeyboardInterrupt:
            pass
        finally:
            record_producer.stop()
            if isinstance(source, Recorder):
                source.close()


if __name__ == '__main__':
    main()
