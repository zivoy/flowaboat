import unittest
from unittest import mock

import arrow

import utils

date_form = "YYYY-MM-DD hh:mm:ss"
sample_date = arrow.get(2019, 1, 1, 13, 14, 15)


class TestAPIMethods(unittest.TestCase):

    @mock.patch('arrow.utcnow', mock.MagicMock(return_value=sample_date))
    def test_clear_queue(self):
        api = utils.Api('http://foo.com', 4)
        time4 = sample_date
        api.actions = []

        api.actions.append(time4.shift(seconds=-60))
        self.assertEqual(len(api.actions), 1)

        api.clear_queue()
        self.assertEqual(len(api.actions), 0)
        api.actions.append(time4.shift(seconds=-60))
        api.actions.append(time4)
        api.actions.append(time4)
        self.assertEquals(len(api.actions), 3)
        api.clear_queue()
        self.assertEquals(len(api.actions), 2)


if __name__ == '__main__':
    unittest.main()
