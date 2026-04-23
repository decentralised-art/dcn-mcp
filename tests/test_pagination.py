import unittest

from dcn_mcp.pagination import paginate


class PaginationTests(unittest.TestCase):
    def test_paginate_first_page(self):
        page, next_cursor = paginate(list(range(12)), None, page_size=5)
        self.assertEqual(page, [0, 1, 2, 3, 4])
        self.assertEqual(next_cursor, '5')

    def test_paginate_middle_page(self):
        page, next_cursor = paginate(list(range(12)), '5', page_size=5)
        self.assertEqual(page, [5, 6, 7, 8, 9])
        self.assertEqual(next_cursor, '10')

    def test_paginate_final_page(self):
        page, next_cursor = paginate(list(range(12)), '10', page_size=5)
        self.assertEqual(page, [10, 11])
        self.assertIsNone(next_cursor)


if __name__ == '__main__':
    unittest.main()
