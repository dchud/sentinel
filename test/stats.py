# $Id$

from unittest import TestCase

from canary.context import Context
from canary.stats import *
from canary.search import RecordSearcher

class StatsTests (TestCase):

    context = Context()
    
    def setUp (self):
        # each test gets a new collector
        self.collector = StatCollector(self.context)
        # get some records for statistics generation once
        searcher = RecordSearcher(self.context)
        self.records = searcher.search('environment')

    def test_curators (self):
        handler = ArticleTypeHandler()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()) > 0, True)

    def test_article_types (self):
        handler = ArticleTypeHandler()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()) > 0, True)

    def test_methodology_samplings (self):
        handler = MethodologySamplingHandler()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()) > 0, True)

    def test_methology_types (self):
        handler = MethodologyTypeHandler()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()) > 0, True)

    def test_methology_timings (self):
        handler = MethodologyTimingHandler()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()) > 0, True)

    def test_methology_controls (self):
        handler = MethodologyControlHandler()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()) > 0, True)

    def test_exposure_routes (self):
        handler = ExposureRouteHandler()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()) > 0, True)

    def test_exposures (self):
        handler = ExposureHandler()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()) > 0, True)

    def test_risk_factors (self):
        handler = RiskFactorHandler()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()) > 0, True)

    def test_outcomes (self):
        handler = OutcomeHandler()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()) > 0, True)

    def test_species (self):
        handler = SpeciesHandler()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()) > 0, True)

    def test_locations (self):
        handler = LocationHandler()
        self.collector.add_handler(handler)
        self.collector.process(self.records)
        self.assertEquals(len(handler.stats.keys()) > 0, True)
