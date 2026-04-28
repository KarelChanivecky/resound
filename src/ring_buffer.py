import numpy as np

from reusable_buffer import ReusableBuffer


class RingBuffer:
    """
    Fixed-size one-dimensional ring buffer with chronological snapshots.
    """

    def __init__(self, capacity, dtype=np.float64):
        if capacity <= 0:
            raise ValueError('capacity must be greater than 0')

        self.__capacity = capacity
        self.__buffer = np.zeros(capacity, dtype=dtype)
        self.__window = ReusableBuffer()
        self.__window.ensure((capacity,), self.__buffer.dtype)
        self.__write_pos = 0
        self.__total_written = 0

    def write(self, values):
        values = np.asarray(values)
        n_values = len(values)

        if n_values >= self.__capacity:
            self.__buffer[:] = values[-self.__capacity:]
            self.__write_pos = 0
            self.__total_written += n_values
            return

        end = self.__write_pos + n_values
        if end <= self.__capacity:
            self.__buffer[self.__write_pos:end] = values
        else:
            split = self.__capacity - self.__write_pos
            self.__buffer[self.__write_pos:] = values[:split]
            self.__buffer[:n_values - split] = values[split:]

        self.__write_pos = (self.__write_pos + n_values) % self.__capacity
        self.__total_written += n_values

    def is_full(self):
        return self.__total_written >= self.__capacity

    def snapshot(self):
        return self.__chronological_window().copy()

    def __chronological_window(self):
        window = self.__window.ensure((self.__capacity,), self.__buffer.dtype)

        if self.__write_pos == 0:
            window[:] = self.__buffer
        else:
            split = self.__capacity - self.__write_pos
            window[:split] = self.__buffer[self.__write_pos:]
            window[split:] = self.__buffer[:self.__write_pos]

        return window
