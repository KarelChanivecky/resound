import unittest

import numpy as np

from buffers.ring_buffer import RingBuffer


class TestRingBuffer(unittest.TestCase):

    def test_is_not_full_before_capacity_written(self):
        ring = RingBuffer(5, dtype=np.int32)
        ring.write(np.array([1, 2, 3], dtype=np.int32))

        self.assertFalse(ring.is_full())

    def test_is_full_after_capacity_written(self):
        ring = RingBuffer(5, dtype=np.int32)
        ring.write(np.array([1, 2, 3, 4, 5], dtype=np.int32))

        self.assertTrue(ring.is_full())

    def test_snapshot_returns_chronological_values_without_wrap(self):
        ring = RingBuffer(5, dtype=np.int32)
        ring.write(np.array([1, 2, 3, 4, 5], dtype=np.int32))

        np.testing.assert_array_equal(ring.snapshot(), np.array([1, 2, 3, 4, 5]))

    def test_snapshot_returns_chronological_values_after_wrap(self):
        ring = RingBuffer(5, dtype=np.int32)
        ring.write(np.array([1, 2, 3], dtype=np.int32))
        ring.write(np.array([4, 5, 6], dtype=np.int32))

        np.testing.assert_array_equal(ring.snapshot(), np.array([2, 3, 4, 5, 6]))

    def test_snapshot_keeps_latest_values_when_write_exceeds_capacity(self):
        ring = RingBuffer(5, dtype=np.int32)
        ring.write(np.array([1, 2, 3, 4, 5, 6, 7], dtype=np.int32))

        np.testing.assert_array_equal(ring.snapshot(), np.array([3, 4, 5, 6, 7]))

    def test_write_after_oversized_write_preserves_order(self):
        ring = RingBuffer(5, dtype=np.int32)
        ring.write(np.array([1, 2, 3, 4, 5, 6, 7], dtype=np.int32))
        ring.write(np.array([8, 9], dtype=np.int32))

        np.testing.assert_array_equal(ring.snapshot(), np.array([5, 6, 7, 8, 9]))

    def test_snapshot_is_not_mutated_by_later_write(self):
        ring = RingBuffer(5, dtype=np.int32)
        ring.write(np.array([1, 2, 3, 4, 5], dtype=np.int32))
        snapshot = ring.snapshot()
        ring.write(np.array([6, 7], dtype=np.int32))

        np.testing.assert_array_equal(snapshot, np.array([1, 2, 3, 4, 5]))

    def test_rejects_nonpositive_capacity(self):
        with self.assertRaises(ValueError):
            RingBuffer(0)
