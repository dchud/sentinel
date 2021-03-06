# $Id$

import copy
import logging
import time
import traceback
import types

from quixote import form2
from quixote.html import htmltext

import canary.context
from canary.gazeteer import Feature
from canary.qx_defs import MyForm
from canary.utils import DTable, render_capitalized
import dtuple



class ExposureRoute (DTable):

    # A Methodology can have one to many ROUTEs
    ROUTE = {
        '-': -1,
        'ingestion' : 1,
        'inhalation' : 2,
        'mucocutaneous' : 3,
        'vector' : 4,
        'other' : 5,
        }
        
    def __init__ (self):
        self.uid = -1
        self.study_id = -1
        self.methodology_id = -1
        self.route = self.ROUTE['-']
        
    def __str__ (self):
        out = []
        out.append('<Route uid=%s study_id=%s' % (self.uid, self.study_id))
        out.append('\troute=%s' % self.get_text_value(self.ROUTE, self.route))
        out.append('\tmethodology_id=%s' % self.methodology_id)
        out.append('/>')
        return '\n'.join(out)
        
        
    def get_text_value (self, lookup_table, value):
        for k, v in lookup_table.iteritems():
            if v == value:
                return k
        return ''


    def set_route (self, route):
        
        if type(route) is types.StringType:
            
            if route in self.ROUTE.keys():
                self.route = self.ROUTE[route]
                
        elif type(route) is types.IntType:
            
            if route in self.ROUTE.values():
                self.route = route
    
    def get_route (self, text=False):
        if text:
            return self.get_text_value(self.ROUTE, self.route)
        else:
            return self.route


    def delete (self, context):
        """
        Delete this route from the database.
        """
        cursor = context.get_cursor()
        if not self.uid == -1:
            try:
                cursor.execute("""
                    DELETE FROM exposure_routes
                    WHERE uid = %s
                    """, self.uid)
            except Exception, e:
                context.logger.error('ExposureRoute: %s (%s)', self.uid, e)
        
        
    def save (self, context):
        cursor = context.get_cursor()
        if self.uid == -1:
            cursor.execute("""
                INSERT INTO exposure_routes
                (uid, study_id, methodology_id, route)
                VALUES 
                (NULL, %s, %s, %s)
                """, (self.study_id, self.methodology_id, self.route)
                )
            self.uid = self.get_new_uid(context)
        else:
            # Assume all calls to save() are after all routes have been removed
            # already by "DELETE FROM exposure_routes" in methodology.save()
            try:
                cursor.execute("""
                    INSERT INTO exposure_routes
                    (uid, study_id, methodology_id, route)
                    VALUES 
                    (%s, %s, %s, %s)
                    """, (self.uid, self.study_id, self.methodology_id, self.route)
                )
            except Exception, e:
                context.logger.error('ExposureRoute: %s (%s)', self.uid, e)
        # FIXME: should this be set from the SQL?
        self.date_modified = time.strftime(str('%Y-%m-%d'))
        

class Methodology (DTable):

    TABLE_NAME = 'methodologies'
    
    # A Methodology must have one TYPE
    TYPES = {
        'experimental' : 1,
        'descriptive' : 2,
        'aggregate' : 3,
        'cross sectional' : 4,
        'cohort' : 5,
        'case control' : 6,
        'disease model' : 7,
        }
        
    # A Methodology can have at most one TIMING
    TIMING = {
        '-': -1,
        'unknown' : 0,
        'historical' : 1,
        'concurrent' : 2,
        'repeated' : 3,
        'mixed' : 4,
        }
    
    # A Methodology can have at most one SAMPLING
    SAMPLING = {
        '-': -1,
        'unknown' : 0,
        'exposure' : 1,
        'outcome' : 2,
        'both' : 3,
        }
        
    # A Methodology can have at most one CONTROLS
    CONTROLS = {
        '-': -1,
        'no' : 0,
        'yes' : 1,
        'both' : 2,
        }


    def __init__ (self, uid=-1):
        self.uid = uid
        self.study_id = -1
        self.study_type_id = -1
        self.sample_size = ''
        self.timing = -1
        self.sampling = -1
        self.controls = -1
        self.is_mesocosm = False
        self.is_enclosure = False
        self.exposure_routes = []
        self.comments = ''
        self.date_modified = None
        self.date_entered = None
        

    def __str__ (self):
        out = []
        out.append('<Methodology uid=%s study_id=%s' % (self.uid, self.study_id))
        out.append('\tstudy_type=%s' % self.get_text_value(self.TYPES, self.study_type_id))
        out.append('\tsample_size=%s' % self.sample_size)
        for item in ['timing', 'sampling', 'controls', 'exposure_routes']:
            out.append('\t%s=%s' % (item, getattr(self, 'get_' + item)(text=True)))
        out.append('\tis_mesocosm=%s, is_enclosure=%s' % (self.is_mesocosm, self.is_enclosure))
        out.append('\tcomments=%s' % self.comments or '')
        out.append('/>')
        return '\n'.join(out)
        

    def evidence_level (self):
        """
        Return the evidence level relative to the type of study 
        performed.
        """
        text_value = self.get_text_value(self.TYPES, self.study_type_id)
        if text_value in ['experimental', 'cohort']:
            return 3
        elif text_value in ['case control', 'cross sectional', 'aggregate']:
            return 2
        elif text_value in ['descriptive', 'disease model']:
            return 1
        else:
            return 0


    def get_text_value (self, lookup_table, value):
        for k, v in lookup_table.iteritems():
            if v == value:
                return k
        return ''

        
    def set_timing (self, timing):
        
        if type(timing) is types.StringType:
            
            if timing in self.TIMING.keys():
                self.timing = self.TIMING[timing]

        elif type(timing) is types.IntType:

            if timing in self.TIMING.values():
                self.timing = timing
    
    def get_timing (self, text=False):
        if text:
            return self.get_text_value(self.TIMING, self.timing)
        else:
            return self.timing
    
    def set_sampling (self, sampling):
        
        if type(sampling) is types.StringType:
            
            if sampling in self.SAMPLING.keys():
                self.sampling = self.SAMPLING[sampling]
        
        elif type(sampling) is types.IntType:
            
            if sampling in self.SAMPLING.values():
                self.sampling = sampling
    
    def get_sampling (self, text=False):
        if text:
            return self.get_text_value(self.SAMPLING, self.sampling)
        else:
            return self.sampling
            
    def set_controls (self, controls):
        
        if type(controls) is types.StringType:
            
            if controls in self.CONTROLS.keys():
                self.controls = self.CONTROLS[controls]
        
        elif type(controls) is types.IntType:
            
            if controls in self.CONTROLS.values():
                self.controls = controls

    def get_controls (self, text=False):
        if text:
            return self.get_text_value(self.CONTROLS, self.controls)
        else:
            return self.controls
    
    
    def set_routes (self, routes):
        
        for route in routes:
            self.add_route(route)
            
        # Remove routes no longer specified
        for route in self.exposure_routes:
            if not route.get_route() in [r.get_route() for r in routes]:
                self.exposure_routes.remove(route)
    
    def add_route (self, route):
        
        if not route.get_route() in [r.get_route() for r in self.exposure_routes]:
            route.methodology_id = self.uid
            route.study_id = self.study_id
            self.exposure_routes.append(route)
            
    
    def get_routes (self, text=False):
        
        if text:
            return [r.get_text_value(r.ROUTE, r.route) for r in self.exposure_routes]
        else:
            return self.exposure_routes


    def set_study_type (self, value):
        """
        Each methodology has exactly one type.
        """
        if type(value) is types.StringType:
            
            if value in self.TYPES.keys():
                self.study_type_id = self.TYPES[value]
                    
        elif type(value) == type(htmltext('a')):
            
            str_value = str(value)
            if str_value in self.TYPES.keys():
                self.study_type_id = self.TYPES[str_value]
        
        elif type(value) is types.IntType:
            
            if value in self.TYPES.values():
                self.study_type_id = value
        
        self.update_values()


    def get_study_type (self, text=False):
        """
        Return the study design type.
        """
        if text:
            return self.get_text_value(self.TYPES, self.study_type_id)
        else:
            return self.study_type_id


    def update_values (self):
        """
        To keep values consistent with methodology type, "blank out"
        inapplicable ones; called by set_study_type() on update.
        """
        if self.get_study_type() in [
            self.TYPES['experimental'],
            self.TYPES['descriptive'],
            self.TYPES['disease model'],
            ]:
            self.set_timing('-')
        
        if not self.get_study_type() in [
            self.TYPES['cross sectional'],
            self.TYPES['cohort'], 
            self.TYPES['case control']
            ]:
            self.set_controls('-')
            
        if not self.get_study_type() in [
            self.TYPES['cross sectional']
            ]:
            self.set_sampling('-')
        

    def delete (self, context):
        """
        Delete this methodology, and its exposure_routes, from the database.
        """
        cursor = context.get_cursor()
        if not self.uid == -1:
            try:
                cursor.execute("""
                    DELETE FROM methodologies
                    WHERE uid = %s
                    """, self.uid)
                
                cursor.execute("""
                    DELETE FROM exposure_routes
                    where methodology_id = %s
                    """, self.uid)
            except Exception, e:
                context.logger.error('Methodology: %s (%s)', self.uid, e)
        
    
    def load_routes (self, context):
        cursor = context.get_cursor()
        cursor.execute("""
            SELECT * FROM exposure_routes
            WHERE methodology_id = %s
            """, (self.uid))
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        for row in rows:
            row = dtuple.DatabaseTuple(desc, row)
            exp_route = ExposureRoute()
            for field in fields:
                exp_route.set(field, row[field])
            self.add_route(exp_route)
        
        
    def save (self, context):
        cursor = context.get_cursor()
        if self.uid == -1:
            cursor.execute("""
                INSERT INTO methodologies
                (uid, study_id, study_type_id, 
                sample_size, timing, 
                sampling, controls, comments,
                is_mesocosm, is_enclosure,
                date_modified, date_entered)
                VALUES 
                (NULL, %s, %s, 
                %s, %s,
                %s, %s, %s,
                %s, %s,
                NOW(), NOW())
                """, (self.study_id, self.study_type_id,
                self.sample_size, self.timing,
                self.sampling, self.controls, self.comments,
                int(self.is_mesocosm), int(self.is_enclosure))
                )
            self.uid = self.get_new_uid(context)
        else:
            try:
                cursor.execute("""
                    UPDATE methodologies
                    SET study_id = %s, study_type_id = %s,
                    sample_size = %s, timing = %s,
                    sampling = %s, controls = %s, comments = %s,
                    is_mesocosm = %s, is_enclosure = %s,
                    date_modified = NOW()
                    WHERE uid = %s
                    """, (self.study_id, self.study_type_id,
                    self.sample_size, self.timing, 
                    self.sampling, self.controls, self.comments,
                    int(self.is_mesocosm), int(self.is_enclosure),
                    self.uid)
                    )
            except Exception, e:
                context.logger.error('Methodology: %s (%s)', self.uid, e)
        # FIXME: should this be set from the SQL?
        self.date_modified = time.strftime(str('%Y-%m-%d'))
        
        # Refill these values every time
        cursor.execute("""
            DELETE FROM exposure_routes
            WHERE methodology_id = %s
            """, self.uid)
            
        for route in self.exposure_routes:
            route.save(context)
        

    def create_form (self, context):
        
        form = MyForm(context)
        
        # all methodology types get a sample size
        form.add(form2.StringWidget, 'sample_size',
            title='Sample size (study n)',
            size=10, value=self.sample_size,
            required=False)
            
        # all methodology types get one or more routes
        route_options = [(route, text, route) for text, route in ExposureRoute.ROUTE.items()]
        # FIXME: what else to do about leaving out the default/empty?
        route_options.remove((-1, '-', -1))
        select_size = len(route_options)
        form.add(form2.MultipleSelectWidget, 'exposure_routes',
            title='Routes of exposure (ctrl-click to select or change multiple)',
            value=[r.route for r in self.get_routes()],
            options=route_options,
            size=select_size,
            sort=False,
            required=True)
        
        # experimental can be is_mesocosm=True
        if self.get_study_type() == self.TYPES['experimental']:
            form.add(form2.CheckboxWidget, 'is_mesocosm',
                title='Is mesocosm?',
                value=self.is_mesocosm)
            
        # methodology types except experimental get timing
        if not self.get_study_type() == self.TYPES['experimental']:
            form.add(form2.SingleSelectWidget, 'timing',
                title='Timing',
                value=self.get_timing(),
                options=[(val, name, val) for name, val in self.TIMING.items()],
                sort=True,
                required=True)
    
        # all the 'c*' methodology types get controls
        if self.get_study_type() in [
            self.TYPES['cross sectional'],
            self.TYPES['cohort'], 
            self.TYPES['case control']
            ]:
            form.add(form2.SingleSelectWidget, 'controls',
                title='Controls from same population?',
                value=self.get_controls(),
                options=[(val, name, val) for name, val in self.CONTROLS.items()],
                sort=True,
                required=True)
        
        # cohort can be is_enclosure=True
        if self.get_study_type() == self.TYPES['cohort']:
            form.add(form2.CheckboxWidget, 'is_enclosure',
                title='Is enclosure?',
                value=self.is_enclosure)
                
            
        # only cross sectional methodologies get sampling
        if self.get_study_type() == self.TYPES['cross sectional']:
            form.add(form2.SingleSelectWidget, 'sampling',
                title='Sampling',
                value=self.get_sampling(),
                options=[(val, name, val) for name, val in self.SAMPLING.items()],
                sort=True,
                required=True)
                    
        # every methodology type has comments
        form.add(form2.TextWidget, 'comments', 
            title='Comments',
            rows='4', cols='60',
            wrap='virtual',
            value=self.comments)
        
        form.add_submit('update', value='update')
        form.add_submit('finish', value='finish')

        return form
        
    
    def process_form (self, form):
        
        # all methodology types get a sample size
        if form['sample_size']:
            self.sample_size = form['sample_size']
            
        # all methodology types get one or more routes
        if form['exposure_routes']:
            routes = []
            for r in form['exposure_routes']:
                route = ExposureRoute()
                route.set_route(r)
                routes.append(route)
            self.set_routes(routes)
        else:
            form.set_error('exposure_routes', 'You must choose at least one route of exposure.')

        # experimental can be is_mesocosm=True
        if self.get_study_type() == self.TYPES['experimental']:
            if form['is_mesocosm']:
                self.is_mesocosm = True
            else:
                self.is_mesocosm = False

        # all methodology types but experimental get timing
        if not self.get_study_type() == self.TYPES['experimental']:
            if form['timing'] == self.TIMING['-']:
                form.set_error('timing', 'You must specifiy the timing.')
            else:
                self.set_timing(form['timing'])
        
        # all 'c*' methodology types get controls
        if self.get_study_type() in [
            self.TYPES['cross sectional'],
            self.TYPES['cohort'],
            self.TYPES['case control']
            ]:
            if form['controls'] == self.CONTROLS['-']:
                form.set_error('controls', 'You must specify the controls.')
            else:
                self.set_controls(form['controls'])
            
        # cohort can be is_enclosure=True
        if self.get_study_type() == self.TYPES['cohort']:
            if form['is_enclosure']:
                self.is_enclosure = True
            else:
                self.is_enclosure = False
            
        # only cross sectional gets sampling
        if self.get_study_type() == self.TYPES['cross sectional']:
            if form['sampling'] == self.SAMPLING['-']:
                form.set_error('sampling', 'You must specify the sampling.')
            else:
                self.set_sampling(form['sampling'])

        # every methodology type can have comments
        if form['comments']:
            self.comments = form['comments']


def find_exposures (context, search_term):
    exposures = {}
    if search_term \
        and len(search_term) > 0:
        
        cursor = context.get_cursor()
        query_term = search_term.strip().replace(' ', '% ') + '%'
        cursor.execute("""
            SELECT umls_terms.umls_concept_id, term, preferred_name, umls_source_id 
            FROM umls_terms, umls_concepts, umls_concepts_sources 
            WHERE term LIKE %s
            AND umls_concepts.umls_concept_id = umls_terms.umls_concept_id 
            AND umls_concepts_sources.umls_concept_id = umls_concepts.umls_concept_id
            ORDER BY term, preferred_name
            """, query_term)
        
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        for row in rows:
            row = dtuple.DatabaseTuple(desc, row)
            if not exposures.has_key((row['umls_concept_id'], row['umls_source_id'])):
                exp = Exposure()
                exp.concept_source_id = row['umls_source_id']
                exp.concept_id = row['umls_concept_id']
                exp.term = row['preferred_name']
                exp.synonyms.append(row['term'])
                exposures[(exp.concept_id, exp.concept_source_id)] = exp
            else:
                exp = exposures[(row['umls_concept_id'], row['umls_source_id'])]
                if not row['term'] in exp.synonyms:
                    exp.synonyms.append(row['term'])
                exposures[(exp.concept_id, exp.concept_source_id)] = exp
        
        # Try to bump up coarse "relevance" of exact matches
        exposures_ranked = exposures.values()
        for exp in exposures_ranked:
            if exp.term.lower() == search_term.lower()\
                or search_term.lower() in [syn.lower() for syn in exp.synonyms]:
                exposures_ranked.remove(exp)
                exposures_ranked.insert(0, exp)
        
        return exposures_ranked
    
    else:
        return exposures.values()

    

class Exposure (DTable):
    
    TABLE_NAME = 'exposures'
    
    UMLS_SOURCES = {
        75: 'MeSH',
        85: 'NCBI Taxonomy',
        501: 'ITIS',
        }
    
    def __init__ (self):
        self.uid = -1
        self.study_id = -1
        self.concept_id = -1
        self.concept_source_id = -1
        self.term = ''
        self.synonyms = []
        
    def __str__ (self):
        out = []
        out.append('<Exposure uid=%s study_id=%s' % (self.uid, self.study_id))
        out.append('\tconcept_id=%s (%s)' % (self.concept_id, self.concept_source_id))
        out.append('\tterm=%s' % self.term)
        out.append('/>')
        return '\n'.join(out)
    
    def delete (self, context):
        """
        Delete this exposure from the database.
        """
        cursor = context.get_cursor()
        if not self.uid == -1:
            try:
                cursor.execute("""
                    DELETE FROM exposures
                    WHERE uid = %s
                    """, self.uid)
            except Exception, e:
                context.logger.error('Exposure: %s (%s)', self.uid, e)
        
    def save (self, context):
        cursor = context.get_cursor()
        if self.uid == -1:
            cursor.execute("""
                INSERT INTO exposures
                (uid, study_id, concept_id, 
                concept_source_id, term)
                VALUES 
                (NULL, %s, %s, 
                %s, %s)
                """, (self.study_id, self.concept_id, 
                self.concept_source_id, self.term)
                )
            self.uid = self.get_new_uid(context)
        else:
            try:
                cursor.execute("""
                    UPDATE exposures
                    SET study_id = %s, concept_id = %s, 
                    concept_source_id = %s, term = %s
                    WHERE uid = %s
                    """, (self.study_id, self.concept_id, 
                    self.concept_source_id, self.term,
                    self.uid)
                    )
            except Exception, e:
                context.logger.error('Exposure: %s (%s)', self.uid, e)
        # FIXME: should this be set from the SQL?
        self.date_modified = time.strftime(str('%Y-%m-%d'))
        

def find_outcomes (context, search_term):
    # Note: for now, limit to only MeSH (umls_source_id==75)
    
    outcomes = {}
    if search_term \
        and len(search_term) > 0:
        cursor = context.get_cursor()
        query_term = search_term.strip().replace(' ', '% ') + '%'
        cursor.execute("""
            SELECT umls_terms.umls_concept_id, term, preferred_name, umls_source_id 
            FROM umls_terms, umls_concepts, umls_concepts_sources 
            WHERE term LIKE %s
            AND umls_source_id = %s
            AND umls_concepts.umls_concept_id = umls_terms.umls_concept_id 
            AND umls_concepts_sources.umls_concept_id = umls_concepts.umls_concept_id
            ORDER BY term, preferred_name
            """, (query_term, 75))
        
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        for row in rows:
            row = dtuple.DatabaseTuple(desc, row)
            if not outcomes.has_key((row['umls_concept_id'], row['umls_source_id'])):
                outcome = Outcome()
                outcome.concept_source_id = row['umls_source_id']
                outcome.concept_id = row['umls_concept_id']
                outcome.term = row['preferred_name']
                outcome.synonyms.append(row['term'])
                outcomes[(outcome.concept_id, outcome.concept_source_id)] = outcome
            else:
                outcome = outcomes[(row['umls_concept_id'], row['umls_source_id'])]
                if not row['term'] in outcome.synonyms:
                    outcome.synonyms.append(row['term'])
                outcomes[(outcome.concept_id, outcome.concept_source_id)] = outcome
        
        # Try to bump up coarse "relevance" of exact matches
        outcomes_ranked = outcomes.values()
        for outcome in outcomes_ranked:
            if outcome.term.lower() == search_term.lower()\
                or search_term.lower() in [syn.lower() for syn in outcome.synonyms]:
                outcomes_ranked.remove(outcome)
                outcomes_ranked.insert(0, outcome)
        return outcomes_ranked
    
    else:
        return outcomes.values()


class Outcome (DTable):
    
    TABLE_NAME = 'outcomes'
    
    UMLS_SOURCES = {
        75: 'MeSH',
        85: 'NCBI Taxonomy',
        501: 'ITIS',
        }
    
    def __init__ (self):
        self.uid = -1
        self.study_id = -1
        self.concept_id = -1
        self.concept_source_id = -1
        self.term = ''
        self.synonyms = []
    
    def __str__ (self):
        out = []
        out.append('<Outcome uid=%s study_id=%s' % (self.uid, self.study_id))
        out.append('\tconcept_id=%s (%s)' % (self.concept_id, self.concept_source_id))
        out.append('\tterm=%s' % self.term)
        out.append('/>')
        return '\n'.join(out)
    
    def delete (self, context):
        """
        Delete this outcome from the database.
        """
        cursor = context.get_cursor()
        if not self.uid == -1:
            try:
                cursor.execute("""
                    DELETE FROM outcomes
                    WHERE uid = %s
                    """, self.uid)
            except Exception, e:
                context.logger.error('Outcome: %s (%s)', self.uid, e)
        
    def save (self, context):
        cursor = context.get_cursor()
        if self.uid == -1:
            cursor.execute("""
                INSERT INTO outcomes
                (uid, study_id, concept_id, 
                concept_source_id, term)
                VALUES 
                (NULL, %s, %s, 
                %s, %s)
                """, (self.study_id, self.concept_id, 
                self.concept_source_id, self.term)
                )
            self.uid = self.get_new_uid(context)
        else:
            try:
                cursor.execute("""
                    UPDATE outcomes
                    SET study_id = %s, concept_id = %s, 
                    concept_source_id = %s, term = %s
                    WHERE uid = %s
                    """, (self.study_id, self.concept_id, 
                    self.concept_source_id, self.term,
                    self.uid)
                    )
            except Exception, e:
                context.logger.error('Outcome: %s (%s)', self.uid, e)
        # FIXME: should this be set from the SQL?
        self.date_modified = time.strftime(str('%Y-%m-%d'))
        
def find_risk_factors (context, search_term):
    # Note: for now, limit to only MeSH (umls_source_id==75)
    
    risk_factors = {}
    if search_term \
        and len(search_term) > 0:
        cursor = context.get_cursor()
        query_term = search_term.strip().replace(' ', '% ') + '%'
        cursor.execute("""
            SELECT umls_terms.umls_concept_id, term, preferred_name, umls_source_id 
            FROM umls_terms, umls_concepts, umls_concepts_sources 
            WHERE term LIKE %s
            AND umls_source_id = %s
            AND umls_concepts.umls_concept_id = umls_terms.umls_concept_id 
            AND umls_concepts_sources.umls_concept_id = umls_concepts.umls_concept_id
            ORDER BY term, preferred_name
            """, (query_term, 75))
        
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        for row in rows:
            row = dtuple.DatabaseTuple(desc, row)
            if not risk_factors.has_key((row['umls_concept_id'], row['umls_source_id'])):
                risk_factor = RiskFactor()
                risk_factor.concept_source_id = row['umls_source_id']
                risk_factor.concept_id = row['umls_concept_id']
                risk_factor.term = row['preferred_name']
                risk_factor.synonyms.append(row['term'])
                risk_factors[(risk_factor.concept_id, risk_factor.concept_source_id)] = risk_factor
            else:
                risk_factor = risk_factors[(row['umls_concept_id'], row['umls_source_id'])]
                if not row['term'] in risk_factor.synonyms:
                    risk_factor.synonyms.append(row['term'])
                risk_factors[(risk_factor.concept_id, risk_factor.concept_source_id)] = risk_factor
        
        # Try to bump up coarse "relevance" of exact matches
        risk_factors_ranked = risk_factors.values()
        for risk_factor in risk_factors_ranked:
            if risk_factor.term.lower() == search_term.lower()\
                or search_term.lower() in [syn.lower() for syn in risk_factor.synonyms]:
                risk_factors_ranked.remove(risk_factor)
                risk_factors_ranked.insert(0, risk_factor)
        return risk_factors_ranked
    
    else:
        return risk_factors.values()


class RiskFactor (DTable):
    
    UMLS_SOURCES = {
        75: 'MeSH',
        85: 'NCBI Taxonomy',
        501: 'ITIS',
        }
    
    def __init__ (self):
        self.uid = -1
        self.study_id = -1
        self.concept_id = -1
        self.concept_source_id = -1
        self.term = ''
        self.synonyms = []
        
    def __str__ (self):
        out = []
        out.append('<RiskFactor uid=%s study_id=%s' % (self.uid, self.study_id))
        out.append('\tconcept_id=%s (%s)' % (self.concept_id, self.concept_source_id))
        out.append('\tterm=%s' % self.term)
        out.append('/>')
        return '\n'.join(out)
    
    def delete (self, context):
        """
        Delete this risk_factor from the database.
        """
        cursor = context.get_cursor()
        if not self.uid == -1:
            try:
                cursor.execute("""
                    DELETE FROM risk_factors
                    WHERE uid = %s
                    """, self.uid)
            except Exception, e:
                context.logger.error('RiskFactor: %s (%s)', self.uid, e)
        
    def save (self, context):
        cursor = context.get_cursor()
        if self.uid == -1:
            cursor.execute("""
                INSERT INTO risk_factors
                (uid, study_id, concept_id, 
                concept_source_id, term)
                VALUES 
                (NULL, %s, %s, 
                %s, %s)
                """, (self.study_id, self.concept_id, 
                self.concept_source_id, self.term)
                )
            self.uid = self.get_new_uid(context)
        else:
            try:
                cursor.execute("""
                    UPDATE risk_factors
                    SET study_id = %s, concept_id = %s, 
                    concept_source_id = %s, term = %s
                    WHERE uid = %s
                    """, (self.study_id, self.concept_id, 
                    self.concept_source_id, self.term,
                    self.uid)
                    )
            except Exception, e:
                context.logger.error('RiskFactor: %s (%s)', self.uid, e)
        # FIXME: should this be set from the SQL?
        self.date_modified = time.strftime(str('%Y-%m-%d'))
        
def find_species (context,search_term):
    
    species_map = {}
    if search_term \
        and len(search_term) > 0:
        cursor = context.get_cursor()
        query_term = search_term.strip().replace(' ', '% ') + '%'
        cursor.execute("""
            SELECT umls_terms.umls_concept_id, term, preferred_name, umls_source_id 
            FROM umls_terms, umls_concepts, umls_concepts_sources 
            WHERE term LIKE %s
            AND umls_concepts.umls_concept_id = umls_terms.umls_concept_id 
            AND umls_concepts_sources.umls_concept_id = umls_concepts.umls_concept_id
            ORDER BY term, preferred_name
            """, query_term)
        
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        for row in rows:
            row = dtuple.DatabaseTuple(desc, row)
            if not species_map.has_key((row['umls_concept_id'], row['umls_source_id'])):
                spec = Species()
                spec.concept_source_id = row['umls_source_id']
                spec.concept_id = row['umls_concept_id']
                spec.term = row['preferred_name']
                spec.synonyms.append(row['term'])
                species_map[(spec.concept_id, spec.concept_source_id)] = spec
            else:
                spec = species_map[(row['umls_concept_id'], row['umls_source_id'])]
                if not row['term'] in spec.synonyms:
                    spec.synonyms.append(row['term'])
                species_map[(spec.concept_id, spec.concept_source_id)] = spec
        
        # Try to bump up coarse "relevance" of exact matches
        species_ranked = species_map.values()
        for spec in species_ranked:
            if spec.term.lower() == search_term.lower()\
                or search_term.lower() in [syn.lower() for syn in spec.synonyms]:
                species_ranked.remove(spec)
                species_ranked.insert(0, spec)
        return species_ranked
    
    else:
        return species_map.values()


class Species (DTable):
    
    TABLE_NAME = 'species'
    
    UMLS_SOURCES = {
        75: 'MeSH',
        85: 'NCBI Taxonomy',
        501: 'ITIS',
        }
    
    TYPES = [
        'companion',
        'livestock',
        'wildlife',
        'laboratory',
        ]
        
    def __init__ (self):
        self.uid = -1
        self.study_id = -1
        self.concept_id = -1
        self.concept_source_id = -1
        self.term = ''
        self.synonyms = []
        self.__dict__['types'] = []
        
    def __str__ (self):
        out = []
        out.append('<Species uid=%s study_id=%s' % (self.uid, self.study_id))
        out.append('\tconcept_id=%s (%s)' % (self.concept_id, self.concept_source_id))
        out.append('\tterm=%s' % self.term)
        out.append('\tsynonyms=%s' % '; '.join(self.synonyms))
        out.append('\ttypes=%s' % '; '.join(self.types))
        out.append('/>')
        return '\n'.join(out)
        
    def __setattr__ (self, name, value):
        # self.types should be a list, but the auto-loader from Study
        # will try to assign it a string.  Catch here, and assume it
        # will be the only time a direct assignment to self.types is
        # called.
        if name == 'types':
            if value.__class__ == ''.__class__:
                self.set_types(value)
            else:
                self.__dict__[name] = value
        else:
            self.__dict__[name] = value
            
    def add_type (self, type):
        if type in self.TYPES:
            if not type in self.types:
                self.types.append(type)
            
    def clear_types (self):
        self.__dict__['types'] = []
    
    def set_types (self, types):
        self.clear_types()
        if types.__class__ == ''.__class__:
            type_dict = dict(zip([t[0:2] for t in self.TYPES], self.TYPES))
            # pass through every two chars in types 
            for i in range(0, len(types), 2):
                type = types[i:i+2]
                species_type = type_dict.get(type, None)
                if species_type:
                    self.add_type(species_type)
                    
        elif types.__class__ == [].__class__:
            for type in types:
                if type in self.TYPES:
                    self.add_type(type)
        
    def get_types (self, shorthand=False):
        if shorthand:
            sh = ''.join([type[0:2] for type in self.types])
            return sh
        else:
            return self.types
    
    def delete (self, context):
        """
        Delete this species from the database.
        """
        cursor = context.get_cursor()
        if not self.uid == -1:
            try:
                cursor.execute("""
                    DELETE FROM species
                    WHERE uid = %s
                    """, self.uid)
            except Exception, e:
                context.logger.error('Species: %s (%s)', self.uid, e)
        

    def save (self, context):
        cursor = context.get_cursor()
        if self.uid == -1:
            cursor.execute("""
                INSERT INTO species
                (uid, study_id, concept_id, 
                concept_source_id, term, types)
                VALUES 
                (NULL, %s, %s, 
                %s, %s, %s)
                """, (self.study_id, self.concept_id, 
                self.concept_source_id, self.term, self.get_types(shorthand=True))
                )
            self.uid = self.get_new_uid(context)
        else:
            try:
                cursor.execute("""
                    UPDATE species
                    SET study_id = %s, concept_id = %s, 
                    concept_source_id = %s, term = %s, types = %s
                    WHERE uid = %s
                    """, (self.study_id, self.concept_id, 
                    self.concept_source_id, self.term, self.get_types(shorthand=True),
                    self.uid)
                    )
            except Exception, e:
                context.logger.error('Species: %s (%s)', self.uid, e)
        # FIXME: should this be set from the SQL?
        self.date_modified = time.strftime(str('%Y-%m-%d'))
        

class Location (DTable):
    
    TABLE_NAME = 'locations'
    
    def __init__ (self, uid=-1):
        self.uid = uid
        self.study_id = -1
        self.feature_id = -1
        self.name = ''
        self.country = ''
        self.designation = ''
        
    def __str__ (self):
        out = []
        out.append('<Location uid=%s study_id=%s' % (self.uid, self.study_id))
        out.append('\tfeature_id=%s' % self.feature_id)
        out.append('/>')
        return '\n'.join(out)
    
    def delete (self, context):
        """
        Delete this location from the database.
        """
        cursor = context.get_cursor()
        if not self.uid == -1:
            try:
                cursor.execute("""
                    DELETE FROM locations
                    WHERE uid = %s
                    """, self.uid)
            except Exception, e:
                context.logger.error('Location: %s (%s)', self.uid, e)
                
    def save (self, context):
        cursor = context.get_cursor()
        if self.uid == -1:
            cursor.execute("""
                INSERT INTO locations
                (uid, study_id, feature_id) 
                VALUES 
                (NULL, %s, %s)
                """, (self.study_id, self.feature_id))
            self.uid = self.get_new_uid(context)
        else:
            try:
                cursor.execute("""
                    UPDATE locations
                    SET study_id = %s, feature_id = %s
                    WHERE uid = %s
                    """, (self.study_id, self.feature_id,
                    self.uid)
                    )
            except Exception, e:
                context.logger.error('Location: %s (%s)', self.uid, e)
        
        
class Study (canary.context.Cacheable, DTable):

    TABLE_NAME = 'studies'
    
    # FIXME:  does this only belong here or on loader.QueuedRecord?
    # A Study has only one STATUS_TYPE
    STATUS_TYPES = {
        'unclaimed' : 0,
        'claimed' : 1,
        'curated' : 2,
        }

    # A Study has only one ARTICLE_TYPE
    ARTICLE_TYPES = {
        'unknown' : 0,
        'irrelevant' : 1,
        'traditional' : 2,
        'general' : 3,
        'review' : 4,
        'outcomes only' : 5,
        'exposures only' : 6,
        'curated' : 7,
        'duplicate' : 8,
        }
            
    # For dynamic iteration over related tables
    TABLES = {
        'methodologies' : Methodology,
        'exposures': Exposure,
        'risk_factors': RiskFactor,
        'outcomes': Outcome,
        'species': Species,
        'locations': Location,
        }

    CACHE_KEY = 'study'

    def __init__ (self, context=None, uid=-1, record_id=-1):
        try:
            if self.record_id >= 0:
                return
        except AttributeError:
            pass
        self.uid = uid
        self.record_id = -1
        self.status = self.STATUS_TYPES['unclaimed']
        self.article_type = self.ARTICLE_TYPES['unknown']
        self.curator_user_id = ''
        self.has_outcomes = False
        self.has_exposures = False
        self.has_relationships = False
        self.has_interspecies = False
        self.has_exposure_linkage = False
        self.has_outcome_linkage = False
        self.has_genomic = False
        self.comments = ''
        self.methodologies = []
        self.exposures = []
        self.risk_factors = []
        self.outcomes = []
        self.species = []
        self.locations = []
        self.date_modified = None
        self.date_entered = None
        self.date_curated = None
        self.history = {}
        
    
    def __str__ (self):
        out = []
        out.append('<Study uid=%s record_id=%s' % (self.uid, self.record_id))
        out.append('\tstatus=%s' % self.get_text_value(self.STATUS_TYPES, self.status))
        out.append('\tcurator_user_id=%s' % self.curator_user_id)
        out.append('\tarticle_type=%s' % self.get_text_value(self.ARTICLE_TYPES, self.article_type))
        out.append('\thas_outcomes=%s' % self.has_outcomes)
        out.append('\thas_exposures=%s' % self.has_exposures)
        out.append('\thas_relationships=%s' % self.has_relationships)
        out.append('\thas_interspecies=%s' % self.has_interspecies)
        out.append('\thas_exposure_linkage=%s' % self.has_exposure_linkage)
        out.append('\thas_outcome_linkage=%s' % self.has_outcome_linkage)
        out.append('\thas_genomic=%s' % self.has_genomic)
        # What are you wanting here?  TYPES is not like OUTCOMES, is it?
        #for table_name in self.TABLES:
        #    if len(getattr(self, table_name)) > 0:
        #        out.append('\t%s=' % table_name + \
        #            ','.join(getattr(self, 'get_' + table_name)(text=True)))
        #if len(self.types) > 0:
        #    out.append('\ttypes=' + ','.join(self.get_types(text=True)))
        out.append('\tcomments=%s' % self.comments or '')
        out.append('/>')
        return '\n'.join(out)
        
    def get_text_value (self, lookup_table, value):
        for k, v in lookup_table.iteritems():
            if v == value:
                return k
        return ''

    """Simple accessors for basic study parameters."""
    # FIXME: some of these could be parameterized.
    
    def set_status (self, value):
        if value in self.STATUS_TYPES.keys():
            self.status = self.STATUS_TYPES[value]
            
    def get_status (self, text=False):
        if text:
            return self.get_text_value(self.STATUS_TYPES, self.status)
        else:
            return self.status
    
    def set_article_type (self, value):
        try:
            if str(value) in self.ARTICLE_TYPES.keys():
                self.article_type = self.ARTICLE_TYPES[str(value)]
        except:
            # FIXME: proper error here
            pass
            
    def get_article_type (self, text=False):
        if text:
            return self.get_text_value(self.ARTICLE_TYPES, self.article_type)
        else:
            return self.article_type
    
    def get_concept_from_concept (self, concept):
        """
        For use in matching searches for exposure/species/outcome against
        summary data. 
       
        NOTE: not checking 'risk_factor', but that should be refactored in
        with a broader concept code refactoring.
        """
        for concept_type in ('exposures', 'outcomes', 'species'):
            for c in getattr(self, concept_type):
                if c.concept_id == concept.uid:
                    # Eliminate trailing 's'
                    if concept_type in ('exposures', 'outcomes'):
                        concept_type = concept_type[:-1]
                    return c, concept_type
        return None, None

    
    def add_methodology (self, methodology):
        for meth in self.methodologies:
            if meth.uid == methodology.uid:
                return
        methodology.study_id = self.uid
        self.methodologies.append(methodology)
        
    def delete_methodology (self, context, methodology):
        for meth in self.methodologies:
            if meth.uid == methodology.uid:
                self.methodologies.remove(meth)
                meth.delete(context)

    def get_methodology (self, id):
        for methodology in self.methodologies:
            if methodology.uid == id:
                return methodology
        return None
        
    def has_exposure (self, exposure):
        """
        Returns True if this exposure has already been added to this Study.
        
        Note that has_exposure may be used before exposure is added,
        hence it does not check exposure.uid.
        """
        for exp in self.exposures:
            if exp.concept_id == exposure.concept_id:
                return True
        return False

    def add_exposure (self, exposure):
        if not self.has_exposure(exposure):
            exposure.study_id = self.uid
            self.exposures.append(exposure)
        
    def delete_exposure (self, context, exposure):
        for exp in self.exposures:
            if exp.concept_id == exposure.concept_id:
                self.exposures.remove(exp)
                exp.delete(context)

    def get_exposure (self, id):
        """
        Return the matching exposure, if added.
        
        Note that get_exposure is for use in matching or deleting exposures,
        i.e., only after an exposure has been added to the Study, so uid
        matching is required.
        """
        for exp in self.exposures:
            if exp.uid == id:
                return exp
        return None
    
    def get_exposure_from_exposure (self, exposure):
        for exp in self.exposures:
            if exp.concept_id == exposure.concept_id:
                return exp
        return None

    def has_risk_factor (self, risk_factor):
        """
        Returns True if this risk_factor has already been added to this Study.
        
        Note that has_risk_factor may be used before risk_factor is added,
        hence it does not check risk_factor.uid.
        """
        for rf in self.risk_factors:
            if rf.concept_id == risk_factor.concept_id:
                return True
        return False

    def add_risk_factor (self, risk_factor):
        if not self.has_risk_factor(risk_factor):
            risk_factor.study_id = self.uid
            self.risk_factors.append(risk_factor)
        
    def delete_risk_factor (self, context, risk_factor):
        for rf in self.risk_factors:
            if rf.concept_id == risk_factor.concept_id:
                self.risk_factors.remove(rf)
                rf.delete(context)

    def get_risk_factor (self, id):
        """
        Return the matching risk_factor, if added.
        
        Note that get_risk_factor is for use in matching or deleting risk_factors,
        i.e., only after an risk_factor has been added to the Study, so uid
        matching is required.
        """
        for risk_factor in self.risk_factors:
            if risk_factor.uid == id:
                return risk_factor
        return None
    
    def get_risk_factor_from_risk_factor (self, risk_factor):
        for rf in self.risk_factors:
            if rf.concept_id == risk_factor.concept_id:
                return rf
        return None

    def has_outcome (self, outcome):
        """
        Returns True if this outcome has already been added to this Study.
        
        Note that has_outcome may be used before outcome is added,
        hence it does not check outcome.uid.
        """
        for outc in self.outcomes:
            if outc.concept_id == outcome.concept_id:
                return True
        return False

    def add_outcome (self, outcome):
        if not self.has_outcome(outcome):
            outcome.study_id = self.uid
            self.outcomes.append(outcome)
        
    def delete_outcome (self, context, outcome):
        for outc in self.outcomes:
            if outc.concept_id == outcome.concept_id:
                self.outcomes.remove(outc)
                outc.delete(context)

    def get_outcome (self, id):
        """
        Return the matching outcome, if added.
        
        Note that get_outcome is for use in matching or deleting outcomes,
        i.e., only after an outcome has been added to the Study, so uid
        matching is required.
        """
        for outcome in self.outcomes:
            if outcome.uid == id:
                return outcome
        return None
    
    def get_outcome_from_outcome (self, outcome):
        for outc in self.outcomes:
            if outc.concept_id == outcome.concept_id:
                return outc
        return None


    def has_species (self, species):
        """
        Returns True if this species has already been added to this Study.
        
        Note that has_species may be used before species is added,
        hence it does not check species.uid.
        """
        for spec in self.species:
            if spec.concept_id == species.concept_id:
                return True
        return False

    def add_species (self, species):
        if not self.has_species(species):
            species.study_id = self.uid
            self.species.append(species)
        
    def delete_species (self, context, species):
        for spec in self.species:
            if spec.concept_id == species.concept_id:
                self.species.remove(spec)
                spec.delete(context)

    def get_species (self, id):
        """
        Return the matching species, if added.
        
        Note that get_species is for use in matching or deleting species,
        i.e., only after an species has been added to the Study, so uid
        matching is required.
        """
        for species in self.species:
            if species.uid == id:
                return species
        return None
    
    def get_species_from_species (self, species):
        for spec in self.species:
            if spec.concept_id == species.concept_id:
                return spec
        return None


    def has_location (self, location):
        """
        Returns True if this location has already been added to this Study.
        
        Note that has_location may be used before location is added,
        hence it does not check location.uid.
        """
        for loc in self.locations:
            if loc.feature_id == location.feature_id:
                return True
        return False

    def has_feature (self, feature):
        """
        Returns True if this feature has already been added to this Study.
        """
        for loc in self.locations:
            if loc.feature_id == feature.uid:
                return True
        return False

    def add_location (self, location):
        if not self.has_location(location):
            location.study_id = self.uid
            self.locations.append(location)
        
    def delete_location (self, context, location):
        for loc in self.locations:
            if loc.uid == location.uid:
                self.locations.remove(loc)
                loc.delete(context)
                
    def get_location (self, id):
        """
        Return the matching location, if added.
        
        Note that get_location is for use in matching or deleting locations,
        i.e., only after an location has been added to the Study, so uid
        matching is required.
        """
        for loc in self.locations:
            if loc.uid == id:
                return loc
        return None
    
    def get_location_from_feature (self, feature):
        for loc in self.locations:
            if loc.feature_id == feature.uid:
                return loc
        return None
        
    def get_locations_sorted (self, context):
        """
        For a set of canary record locations, return them in sort order
        by lower((country_name, region_name, feature_name)).
        """
        gazeteer = context.get_gazeteer()
        locs = []
        for location in self.locations:
            feature = Feature(uid=location.feature_id)
            feature.load(context)
            if gazeteer.fips_codes.has_key((feature.country_code, feature.adm1)):
                region_name = gazeteer.fips_codes[(feature.country_code, feature.adm1)]
            else:
                region_name = ''
            name = feature.name
            type = gazeteer.feature_codes[feature.feature_type]
            region_name = render_capitalized(region_name)
            country_name = render_capitalized(gazeteer.country_codes[feature.country_code])
            locs.append(
                ((country_name.lower(), region_name.lower(), name.lower()),
                (name, type, region_name, country_name))
                )
        locs.sort()
        return locs

    def get_lat_longs (self, context, dms=False):
        """
        For a set of canary record locations, return their latitudes
        and longitudes as two lists.
        """
        lats = longs = []
        for location in self.locations:
            feature = Feature(uid=location.feature_id)
            feature.load(context)
            if dms:
                lats.append(feature.dms_latitude)
                longs.append(feature.dms_longitude)
            else:
                lats.append(feature.latitude)
                longs.append(feature.longitude)
        return lats, longs

    def add_history (self, uid=-1, curator_user_id='', message='', modified=''):
        """
        Add a history record; only one history record can be added to a
        study_history at a time (because the key is set to -1).  Maybe
        that's bad design. :\
        """
        # Convert w/str() in case htmltext is passed by mistake
        curator_user_id = str(curator_user_id)
        message = str(message)
        new_history = {
            'uid': uid, 
            'study_id': self.uid,
            'curator_user_id': curator_user_id, 
            'message': message,
            'modified': modified
            }
        self.history[new_history['uid']] = new_history
        
    def load (self, context):
        
        # Can't load a new study; it hasn't been saved yet.
        if self.uid == -1:
            return

        # Is it already loaded?  Convenience check for client calls
        # don't need to verify loads from the cache.
        if context.config.use_cache:
            try:
                if self.record_id >= 0:
                    # Already loaded
                    return
            except AttributeError:
                # Note already loaded, so continue
                pass
        
        cursor = context.get_cursor()
        cursor.execute("""
            SELECT *
            FROM studies
            WHERE uid = %s
            """, self.uid)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        if rows and len(rows) > 0:
            row = dtuple.DatabaseTuple(desc, rows[0])
            for field in fields:
                self.set(field, row[field])

        # Every table_class is a DTable
        for table_name, table_class in self.TABLES.items():
            select_phrase = """SELECT * FROM %s """ % table_name
            cursor.execute(select_phrase + """
                WHERE study_id = %s
                """, (self.uid))
            fields = [d[0] for d in cursor.description]
            desc = dtuple.TupleDescriptor([[f] for f in fields])
            rows = cursor.fetchall()
            for row in rows:
                row = dtuple.DatabaseTuple(desc, row)
                table_class_instance = table_class()
                for field in fields:
                    table_class_instance.set(field, row[field])
                getattr(self, table_name).append(table_class_instance)
        
        for meth in self.methodologies:
            meth.load_routes(context)
            
        cursor.execute("""
            SELECT *
            FROM study_history
            WHERE study_id = %s
            """, self.uid)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        for row in rows:
            row = dtuple.DatabaseTuple(desc, row)
            history_record = {}
            for field in fields:
                history_record[field] = row[field]
            self.add_history(uid=history_record['uid'], 
                curator_user_id=history_record['curator_user_id'],
                message=history_record['message'],
                modified=history_record['modified'])
        
        

    def save (self, context):
        cursor = context.get_cursor()
        if self.uid == -1:
            try:
                cursor.execute("""
                    INSERT INTO studies
                    (uid, 
                    record_id, status, article_type, curator_user_id, 
                    has_outcomes, has_exposures, 
                    has_relationships, has_interspecies, 
                    has_exposure_linkage, has_outcome_linkage,
                    has_genomic, comments, 
                    date_modified, date_entered, date_curated)
                    VALUES 
                    (NULL, 
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    NOW(), NOW(), %s)
                    """, (self.record_id, self.status, self.article_type, self.curator_user_id,
                    int(self.has_outcomes), int(self.has_exposures), 
                    int(self.has_relationships), int(self.has_interspecies), 
                    int(self.has_exposure_linkage), int(self.has_outcome_linkage),
                    int(self.has_genomic), self.comments,
                    self.date_curated)
                    )
            except Exception, e:
                context.logger.error('Save study: %s (%s)', self.uid, e)
                
            self.uid = self.get_new_uid(context)

        else:
            try:
                cursor.execute("""
                    UPDATE studies
                    SET record_id = %s, status = %s, article_type = %s, curator_user_id = %s,
                    has_outcomes = %s, has_exposures = %s, 
                    has_relationships = %s, has_interspecies = %s, 
                    has_exposure_linkage = %s, has_outcome_linkage = %s,
                    has_genomic = %s, comments = %s,
                    date_modified = NOW(), date_curated = %s
                    WHERE uid = %s
                    """, (self.record_id, self.status, self.article_type, self.curator_user_id,
                    int(self.has_outcomes), int(self.has_exposures), 
                    int(self.has_relationships), int(self.has_interspecies), 
                    int(self.has_exposure_linkage), int(self.has_outcome_linkage),
                    int(self.has_genomic), self.comments,
                    self.date_curated,
                    self.uid)
                    )
            except Exception, e:
                context.logger.error('Update study: %s', e)
        # FIXME: should this be set from the SQL?
        self.date_modified = time.strftime(str('%Y-%m-%d'))
        
        # update all the related table values
        for table_name in self.TABLES.keys():
            for item in getattr(self, table_name):
                item.save(context)
        
        # Save new history records; assume only one can be added at a time,
        # new record will necessarily have uid == -1
        if self.history:
            new_history_record = self.history.get(-1, None)
            if new_history_record:
                try:
                    cursor.execute("""
                        INSERT INTO study_history
                        (uid, study_id, curator_user_id, 
                        message, modified)
                        VALUES
                        (NULL, %s, %s, 
                        %s, NOW())
                        """, (self.uid, new_history_record['curator_user_id'], 
                        new_history_record['message']))
                    new_history_record_id = self.get_new_uid(context)
                    del(self.history[-1])
                    self.history[new_history_record_id] = new_history_record
                except Exception, e:
                    context.logger.error('Save study history: %s (%s)', self.uid, e)
                    
        if context.config.use_cache:
            # Force reload on next call to flush history times
            context.cache_delete('%s:%s' % (self.CACHE_KEY, self.uid))
        
        
    def delete (self, context):
        cursor = context.get_cursor()
        try:
            for table_name in self.TABLES.keys():
                for item in getattr(self, table_name):
                    item.delete(context)
                
            cursor.execute("""
                DELETE FROM studies
                WHERE uid = %s
                """, self.uid)

            if context.config.use_cache:
                context.cache_delete('%s:%s' % (self.CACHE_KEY, self.uid))

        except Exception, e:
            context.logger.error('Delete study: %s', e)
       
