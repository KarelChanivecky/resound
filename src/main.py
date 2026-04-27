import argparse

import scipy.signal.windows as scipy_win

from pipeline.threaded_consumer import ThreadedConsumer
from pipeline.threaded_consumer_producer import ThreadedConsumerProducer
from pipeline.threaded_producer import ThreadedProducer
from pipeline.threaded_t_producer_consumer import ThreadedTConsumerProducer
from processes.frequency_extractor import FrequencyExtractor
from processes.console_printer import ConsolePrinter
from processes.note_identifier import NoteIdentifier
from processes.playback import Playback
from processes.recorder import Recorder
from processes.synthesizer import Synthesizer
from note_spec import parse_note_specs

_WINDOWS_WITH_NO_PARAMS = {'hann', 'hamming', 'blackman', 'blackmanharris', 'boxcar', 'flattop'}
_WINDOWS_ALL = _WINDOWS_WITH_NO_PARAMS | {'kaiser', 'tukey'}

# Synthesizer defaults mirror the Recorder(2500, 0.5) settings used in recorder mode.
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
    p = argparse.ArgumentParser(description='Resound — musical instrument tuner')

    # Audio source
    p.add_argument('--source', choices=['recorder', 'synth'], default='recorder',
                   help='audio source: microphone recorder or synthesizer (default: recorder)')
    p.add_argument('--notes', default=None, metavar='SPEC',
                   help='note spec for synth source, e.g. "A45,C#37:5" '
                        '(required when --source synth)')
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

    namespace = p.parse_args(args)

    if namespace.source == 'synth' and namespace.notes is None:
        p.error('--notes is required when --source is synth')
    if namespace.playback and namespace.source != 'synth':
        p.error('--playback is only supported with --source synth')

    return namespace


def _build_window(args):
    if args.window == 'kaiser':
        window_spec = ('kaiser', args.beta)
    elif args.window == 'tukey':
        window_spec = ('tukey', args.alpha)
    else:
        window_spec = args.window
    return scipy_win.get_window(window_spec, args.fft_size, fftbins=True)


def _build_audio_source(args):
    if args.source == 'synth':
        notes = parse_note_specs(args.notes)
        # Guarantee the sample has at least fft_size samples so windowing never fails.
        min_duration = args.fft_size / _SYNTH_SAMPLE_RATE
        sample_duration = max(_SYNTH_SAMPLE_DURATION, min_duration)
        return Synthesizer(notes, _SYNTH_SAMPLE_RATE, sample_duration, snr=args.snr)
    return Recorder(2500, 0.5)


def main():
    args = _parse_args()
    norm = None if args.fft_norm == 'backward' else args.fft_norm
    window = _build_window(args)

    console_printer = ThreadedConsumer(10, ConsolePrinter())
    note_identifier = ThreadedConsumerProducer(10, console_printer, NoteIdentifier())
    freq_extractor = ThreadedConsumerProducer(
        10, note_identifier,
        FrequencyExtractor(fft_size=args.fft_size,
                           target_z_score=args.zscore,
                           norm=norm,
                           window=window))
    source = _build_audio_source(args)
    if args.playback:
        playback_consumer = ThreadedConsumer(2, Playback())
        upstream = ThreadedTConsumerProducer(10, freq_extractor, playback_consumer)
    else:
        upstream = freq_extractor
    record_producer = ThreadedProducer(upstream, source)
    record_producer.start()


if __name__ == '__main__':
    main()
