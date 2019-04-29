#!/usr/bin/python

import unittest
from crawler import crawler


class TestCrawler(unittest.TestCase):
    def test_crawler(self):
        result = crawler("http://man7.org", 1)
        expect = "\nOutput file is tmp_output/man7.org_1.output\n"
        self.assertEqual(result, expect)


if __name__ == '__main__':
    unittest.main()
