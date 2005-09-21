# $Id$

from canary.context import Context
from canary.study import *
from canary.user import get_user_by_id


# helper function for tallying stats
def tally(storage, item):
    if storage.has_key(item):
        storage[item] += 1
    else:
        storage[item] = 1


class StatCollector: 

    def __init__ (self, context):
        self.context = context
        self.handlers = []

    def add_handler(self, handler):
        self.handlers.append(handler)

    def add_handlers(self, *handlers):
        for handler in handlers:
            self.add_handler(handler)

    def process(self, records):
        for record in records:
            for handler in self.handlers:
                handler.process(self.context, record)

class Curators:

    def __init__(self):
        self.stats = {}

    def process(self, context, record):
        study = Study(context, record.study_id)
        user = get_user_by_id(context, study.curator_user_id)
        tally(self.stats, user.name)

class ArticleTypes:

    def __init__(self):
        self.stats = {}
        for key in Study.ARTICLE_TYPES:
            self.stats[key] = 0
        
    def process (self, context, record):
        type = Study(context, record.study_id).get_article_type(text=True)
        tally(self.stats, type)

class MethodologySamplings:

    def __init__(self):
        self.stats = {}
        for key in Methodology.SAMPLING:
            self.stats[key] = 0

    def process (self, context, record):
        for methodology in Study(context, record.study_id).methodologies:
            tally(self.stats, methodology.get_sampling(text=True))

class MethodologyTypes:

    def __init__(self):
        self.stats = {}
        for key in Methodology.TYPES:
            self.stats[key] = 0

    def process (self, context, record):
        for methodology in Study(context, record.study_id).methodologies:
            tally(self.stats, methodology.get_study_type(text=True))

class MethodologyTimings:

    def __init__(self):
        self.stats = {}
        for key in Methodology.TIMING:
            self.stats[key] = 0

    def process (self, context, record):
        for methodology in Study(context, record.study_id).methodologies:
            tally(self.stats, methodology.get_timing(text=True))

class MethodologyControls:

    def __init__(self):
        self.stats = {}
        for key in Methodology.CONTROLS:
            self.stats[key] = 0

    def process (self, context, record):
        for methodology in Study(context, record.study_id).methodologies:
            tally(self.stats, methodology.get_controls(text=True))

class ExposureRoutes:

    def __init__(self):
        self.stats = {}
        for key in ExposureRoute.ROUTE:
            self.stats[key] = 0

    def process (self, context, record):
        for methodology in Study(context, record.study_id).methodologies:
            for route in methodology.get_routes(text=True):
                tally(self.stats, route)

class Exposures:

    def __init__(self):
        self.stats = {}
        for source in Exposure.UMLS_SOURCES.values():
            self.stats[source] = {}

    def process (self, context, record):
        for exposure in Study(context, record.study_id).exposures:
            source = Exposure.UMLS_SOURCES[exposure.concept_source_id]
            tally(self.stats[source], exposure.term)

class RiskFactors:

    def __init__ (self):
        self.stats = {}
        for source in RiskFactor.UMLS_SOURCES.values():
            self.stats[source] = {}

    def process (self, context, record):
        for risk_factor in Study(context, record.study_id).risk_factors:
            source = RiskFactor.UMLS_SOURCES[risk_factor.concept_source_id]
            tally(self.stats[source], risk_factor.term)

class Outcomes: 

    def __init__ (self):
        self.stats = {}
        for source in Outcome.UMLS_SOURCES.values():
            self.stats[source] = {}

    def process (self, context, record):
        for outcome in Study(context, record.study_id).outcomes:
            source = Outcome.UMLS_SOURCES[outcome.concept_source_id]
            tally(self.stats[source], outcome.term)

# named diferently since study.Species exists
class SpeciesStats: 

    def __init__ (self):
        self.stats = {}
        for source in Species.UMLS_SOURCES.values():
            self.stats[source] = {}

    def process (self, context, record):
        for species in Study(context, record.study_id).species:
            source = Species.UMLS_SOURCES[species.concept_source_id]
            tally(self.stats[source], species.term)

class Locations:

    def __init__(self):
        self.stats = {}

    def process (self, context, record):
        for location in Study(context, record.study_id).locations:
            if not self.stats.has_key(location.country):
                self.stats[location.country] = {}
            tally(self.stats[location.country], location.name)

