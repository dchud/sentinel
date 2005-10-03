# $Id$

from canary.context import Context
from canary.study import *
from canary.user import get_user_by_id



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


class StatHandler:
        
    # Define a list of keys to tally
    KEYS = []
    
    def __init__ (self, filters=[]):
        self.stats = {}
        self.filters = []
        for keyset in self.KEYS:
            for key in keyset:
                self.stats[key] = 0
            
    def get_study (self, context, record):
        return self.filter(context, record)

    def filter (self, context, record):
        try:
            # Does the study exist?
            study = Study(context, record.study_id)
            for filter in self.filters:
                type, attr, val = filter.split(':')
                if type == 'record':
                    if not getattr(record, attr) == val:
                        raise 'FilteredRecordValue'
                elif type == 'study':
                    if not getattr(study, attr) == val:
                        raise 'FilteredStudyValue'
                else:
                    raise 'InvalidFilter'
            return study
        except:
            return None
            
    
    def tally (self, item):
        try:
            self.stats[item] += 1
        except:
            self.stats[item] = 1

    
class CuratorHandler (StatHandler):

    def process (self, context, record):
        study = self.get_study(context, record)
        if study:
            user = get_user_by_id(context, study.curator_user_id)
            self.tally(user.name)


class ArticleTypeHandler (StatHandler):

    KEYS = [Study.ARTICLE_TYPES]
        
    def process (self, context, record):
        study = self.get_study(context, record)
        if study:
            self.tally(study.get_article_type(text=True))


class MethodologySamplingHandler (StatHandler):

    KEYS = [Methodology.SAMPLING]

    def process (self, context, record):
        study = self.get_study(context, record)
        if study:
            for methodology in study.methodologies:
                self.tally(methodology.get_sampling(text=True))


class MethodologyTypeHandler (StatHandler):

    KEYS = [Methodology.TYPES]

    def process (self, context, record):
        study = self.get_study(context, record)
        if study:
            for methodology in study.methodologies:
                self.tally(methodology.get_study_type(text=True))


class MethodologyTimingHandler (StatHandler):

    KEYS = [Methodology.TIMING]
    

    def process (self, context, record):
        study = self.get_study(context, record)
        if study:
            for methodology in study.methodologies:
                self.tally(methodology.get_timing(text=True))


class MethodologyControlHandler (StatHandler):

    KEYS = [Methodology.CONTROLS]

    def process (self, context, record):
        study = self.get_study(context, record)
        if study:
            for methodology in study.methodologies:
                self.tally(methodology.get_controls(text=True))


class ExposureRouteHandler (StatHandler):
    
    KEYS = [ExposureRoute.ROUTE]

    def process (self, context, record):
        study = self.get_study(context, record)
        if study:
            for methodology in study.methodologies:
                for route in methodology.get_routes(text=True):
                    self.tally(route)


class ExposureHandler (StatHandler):
    
    KEYS = [Exposure.UMLS_SOURCES.values()]

    def process (self, context, record):
        study = self.get_study(context, record)
        if study:
            for exposure in study.exposures:
                source = Exposure.UMLS_SOURCES[exposure.concept_source_id]
                self.tally((exposure.term, exposure.concept_id))


class RiskFactorHandler (StatHandler):

    KEYS = [RiskFactor.UMLS_SOURCES.values()]
    
    def process (self, context, record):
        study = self.get_study(context, record)
        if study:
            for risk_factor in study.risk_factors:
                source = RiskFactor.UMLS_SOURCES[risk_factor.concept_source_id]
                self.tally((risk_factor.term, risk_factor.concept_id))

    
class OutcomeHandler (StatHandler): 

    KEYS = [Outcome.UMLS_SOURCES.values()]

    def process (self, context, record):
        study = self.get_study(context, record)
        if study:
            for outcome in study.outcomes:
                source = Outcome.UMLS_SOURCES[outcome.concept_source_id]
                self.tally((outcome.term, outcome.concept_id))


class SpeciesHandler (StatHandler): 

    KEYS = [Species.UMLS_SOURCES.values()]

    def process (self, context, record):
        study = self.get_study(context, record)
        if study:
            for species in study.species:
                source = Species.UMLS_SOURCES[species.concept_source_id]
                self.tally((species.term, species.concept_id))


class LocationHandler (StatHandler):
    
    def process (self, context, record):
        study = self.get_study(context, record)
        if study:
            for location in study.locations:
                self.tally((location.country, location.name))

