# $Id$

from unittest import TestCase, makeSuite

from canary.context import Context
from canary.stats import *
from canary.search import RecordSearcher

class StatsTests(TestCase):

    def __init__(self,name):

        # call parent initializer
        TestCase.__init__(self,name);

        # establish context once
        self.context = Context()

        # get some records for statistics generation once
        searcher = RecordSearcher(self.context)
        self.records = searcher.search('environment')

    def setUp(self):

        # each test gets a new collector
        self.collector = StatCollector(self.context)

    def test_curators(self):
        handler = ArticleTypes()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()) > 0, True)

    def test_article_types(self):
        handler = ArticleTypes()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()), 9)

    def test_methodology_samplings(self):
        handler = MethodologySamplings()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()), 5)

    def test_methology_types(self):
        handler = MethodologyTypes()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()), 7)

    def test_methology_timings(self):
        handler = MethodologyTimings()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()), 6)

    def test_methology_controls(self):
        handler = MethodologyControls()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()), 4)

    def test_exposure_routes(self):
        handler = ExposureRoutes()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()), 6)

    def test_exposures(self):
        handler = Exposures()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()), 3)

    def test_risk_factors(self):
        handler = RiskFactors()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()), 3)

    def test_outcomes(self):
        handler = Outcomes()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()), 3)

    def test_species(self):
        handler = SpeciesStats()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()), 3)

    def test_locations(self):
        handler = Locations()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        print handler.stats

def suite():
    return makeSuite( StatsTests, 'test' )
