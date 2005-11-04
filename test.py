#!/usr/bin/env python2.4

# $Id$

from test import StatsTests, SearchTests, ParserTests
from unittest import TestSuite, TextTestRunner, makeSuite

def suite ():
    suite = TestSuite()
    suite.addTest(makeSuite(StatsTests, 'test'))
    suite.addTest(makeSuite(SearchTests, 'test'))
    suite.addTest(makeSuite(ParserTests, 'test'))
    return suite

if __name__ == '__main__':
    runner = TextTestRunner(verbosity=2)
    runner.run(suite())
