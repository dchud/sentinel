#!/usr/bin/env python2.4

"""
Run all tests:

    ./test.py 

Or a specific suite (search, parsing, stats)

    ./test.py parsing 
"""

from test import StatsTests, SearchTests, PubmedMedlineTests
from unittest import TestSuite, TextTestRunner, makeSuite
from sys import argv

# determine if we should all or just one 
tests = [ 'stats', 'parsing', 'search' ]
if len(argv) == 2: 
    tests = [argv[1]]

# add appropriate tests 
suite = TestSuite()
if 'stats' in tests:
    suite.addTest(makeSuite(StatsTests, 'test'))

if 'search' in tests:
    suite.addTest(makeSuite(SearchTests, 'test'))

if 'parsing' in tests:
    suite.addTest(makeSuite(PubmedMedlineTests, 'test'))

# run 'em 
runner = TextTestRunner(verbosity=2)
runner.run(suite)
