import argparse

import scipy.signal.windows as scipy_win

from pipeline.threaded_consumer import ThreadedConsumer
from pipeline.threaded_consumer_producer import ThreadedConsumerProducer
from pipeline.threaded_producer import ThreadedProducer
from processes.frequency_extractor import FrequencyExtractor
from processes.console_printer import ConsolePrinter
from processes.note_identifier import NoteIdentifier
from processes.recorder import Recorder

_WINDOWS_WITH_NO_PARAMS = {'hann', 'hamming', 'blackman', 'blackmanharris', 'boxcar', 'flattop'}
_WINDOWS_ALL = _WINDOWS_WITH_NO_PARAMS | {'kaiser', 'tukey'}


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


def _parse_args():
    p = argparse.ArgumentParser(description='Resound — musical instrument tuner')
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
    return p.parse_args()


def _build_window(args):
    if args.window == 'kaiser':
        window_spec = ('kaiser', args.beta)
    elif args.window == 'tukey':
        window_spec = ('tukey', args.alpha)
    else:
        window_spec = args.window
    return scipy_win.get_window(window_spec, args.fft_size, fftbins=True)


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
    record_producer = ThreadedProducer(freq_extractor, Recorder(2500, 0.5))
    record_producer.start()


if __name__ == '__main__':
    main()
