import unittest

import pandas as pd

from replayParser import get_action_at_time


class PositionTests(unittest.TestCase):
    data = pd.DataFrame([[-123, 12, 50, 2],
                         [-100, 41, 230, 0],
                         [-50, 412, 123, 0],
                         [0, 42, 123, 0],
                         [20, 54, 213, 0],
                         [100, 123, 532, 0],
                         [120, 54, 34, 21],
                         [124, 45, 65, 0],
                         [300, 41, 34, 0]],
                        columns=["offset", "x pos", "y pos", "clicks"])

    def test_smaller_then(self):
        test = get_action_at_time(self.data, -200)
        self.assertEqual((test == self.data.iloc[0]).all(), True)

    def test_equals(self):
        test = get_action_at_time(self.data, 0)
        self.assertEqual((test == self.data.iloc[3]).all(), True)

    def test_round_down(self):
        test = get_action_at_time(self.data, 140)
        self.assertEqual((test == self.data.iloc[7]).all(), True)

    def test_bigger_then(self):
        test = get_action_at_time(self.data, 400)
        self.assertEqual((test == self.data.iloc[8]).all(), True)

    def test_smallest_equals(self):
        test = get_action_at_time(self.data, -123)
        self.assertEqual((test == self.data.iloc[0]).all(), True)

    def test_largest_equals(self):
        test = get_action_at_time(self.data, 300)
        self.assertEqual((test == self.data.iloc[-1]).all(), True)


if __name__ == '__main__':
    unittest.main()
