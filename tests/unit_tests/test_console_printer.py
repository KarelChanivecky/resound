import unittest
from unittest.mock import patch

from processes.console_printer import ConsolePrinter


class TestConsolePrinter(unittest.TestCase):

    def test_run_prints_item(self):
        item = 'A4'
        with patch('builtins.print') as mock_print:
            ConsolePrinter().run(item)
        mock_print.assert_called_once_with(f'Note:\n{item}')

    def test_run_with_none_does_not_raise(self):
        with patch('builtins.print') as mock_print:
            ConsolePrinter().run(None)
        mock_print.assert_called_once_with('Note:\nNone')

    def test_run_with_no_argument_does_not_raise(self):
        with patch('builtins.print') as mock_print:
            ConsolePrinter().run()
        mock_print.assert_called_once_with('Note:\nNone')
