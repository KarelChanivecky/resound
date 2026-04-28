import numpy as np


class ReusableBuffer:
    """
    Process-local NumPy buffer that reallocates only when shape or dtype changes.
    """

    def __init__(self):
        self.__array = None

    def copy_from(self, values):
        values = np.asarray(values)
        self.ensure(values.shape, values.dtype)
        self.__array[...] = values
        return self.__array

    def ensure(self, shape, dtype):
        if self.__array is None or self.__array.shape != shape or self.__array.dtype != dtype:
            self.__array = np.empty(shape, dtype=dtype)
        return self.__array

    def snapshot(self):
        return self.__array.copy()
