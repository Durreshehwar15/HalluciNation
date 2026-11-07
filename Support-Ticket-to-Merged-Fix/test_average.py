import unittest

from average import average


class AverageTests(unittest.TestCase):
    def test_average_of_normal_input(self):
        self.assertEqual(average([2, 4, 6]), 4)

    def test_average_of_empty_input_raises_value_error(self):
        with self.assertRaises(ValueError) as context:
            average([])
        self.assertEqual(str(context.exception), "Cannot calculate the average of an empty list.")


if __name__ == "__main__":
    unittest.main()
