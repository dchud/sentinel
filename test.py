#!/usr/bin/env python2.4

"""
Run all tests:

    ./test.py 

Or a specific suite (search, parser, stats)

    ./test.py parser

$Id$
"""

from os import system
from sys import argv
from unittest import TestSuite, TextTestRunner, makeSuite

from test import StatsTests, SearchTests, PubmedMedlineTests, \
    OvidMedlineTests, OvidBiosisTests, TermTests

# determine if we should all or just one 
tests = [ 'stats', 'parsing', 'search', 'term' ]
if len(argv) == 2: 
    tests = [argv[1]]

# add appropriate tests 
suite = TestSuite()
if 'stats' in tests:
    suite.addTest(makeSuite(StatsTests, 'test'))

if 'search' in tests:
    suite.addTest(makeSuite(SearchTests, 'test'))

if 'parser' in tests:
    suite.addTest(makeSuite(PubmedMedlineTests, 'test'))
    suite.addTest(makeSuite(OvidMedlineTests, 'test'))
    suite.addTest(makeSuite(OvidBiosisTests, 'test'))

if 'term' in tests:
    suite.addTest(makeSuite(TermTests, 'test'))

# run 'em 
runner = TextTestRunner(verbosity=2)
runner.run(suite)

# clean up .pyc files
system('\\rm canary/*.pyc')
system('\\rm test/*.pyc')
