# $Id$

import unittest
import test
import sys

def suite():
    suite = unittest.TestSuite()
    suite.addTest(test.stats.suite())
    suite.addTest(test.search.suite())
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite())
