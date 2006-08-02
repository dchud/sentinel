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


# determine if we should all or just one 
tests = ['stats', 'search', 'parser', 'term', 'user_functions']
if len(argv) == 2: 
    tests = [argv[1]]

# add appropriate tests 
suite = TestSuite()
if 'stats' in tests:
    from test.stats import StatsTests
    suite.addTest(makeSuite(StatsTests))

if 'search' in tests:
    from test.search import SearchTests
    suite.addTest(makeSuite(SearchTests))

if 'parser' in tests:
    from test.parser import ParserTests, PubmedMedlineTests, OvidMedlineTests, \
        OvidBiosisTests, OvidCabAbstractsTests
    suite.addTest(makeSuite(PubmedMedlineTests))
    suite.addTest(makeSuite(OvidMedlineTests))
    suite.addTest(makeSuite(OvidBiosisTests))
    suite.addTest(makeSuite(OvidCabAbstractsTests))

if 'term' in tests:
    from test.term import TermTests
    suite.addTest(makeSuite(TermTests))

if 'user_functions' in tests:
    from test.user_functions import UserFunctionTests
    suite.addTest(makeSuite(UserFunctionTests))

if 'resolver' in tests:
    from test.resolver import ResolverTests
    suite.addTest(makeSuite(ResolverTests))


# run 'em 
runner = TextTestRunner(verbosity=2)
runner.run(suite)

# clean up .pyc files
system('\\rm canary/*.pyc')
system('\\rm test/*.pyc')
