from unittest import TestCase
from frequency_extractor import contains_dissimilar_frequency


class TestContainsDissimilarFrequency(TestCase):
    def test_contains_dissimilar_frequency_empty_list_no_dissimilar(self):
        test_case = []
        self.assertFalse(contains_dissimilar_frequency(test_case))

    def test_contains_dissimilar_frequency_one_item_no_dissimilar(self):
        test_case = [5]
        self.assertFalse(contains_dissimilar_frequency(test_case))

    def test_contains_dissimilar_frequency_4_items_no_dissimilar(self):
        test_case = [14, 15, 16, 17]
        self.assertFalse(contains_dissimilar_frequency(test_case))

    def test_contains_dissimilar_frequency_4_items_dissimilar(self):
        test_case = [14, 15, 16, 18]
        self.assertTrue(contains_dissimilar_frequency(test_case))
