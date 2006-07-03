# $Id$

import sys
import traceback

from canary.concept import Concept
import canary.context
from canary.human_study import HumanStudy
from canary import study
from canary.utils import DTable
import dtuple


this_module = sys.modules[__name__]

def summary_set_from_concept (context, concept_id, concept_type):
    """
    For a given concept_id with a particular concept_type, return
    the set of summary/study pairs for that concept.
    """
    if concept_type in ('exposure', 'outcome'):
        table_name = concept_type + 's'
    elif concept_type == 'species':
        table_name = concept_type
    else:
        return None

    pairs = []
    try:
        cursor = context.get_cursor()
        query = """
            SELECT summary_concepts.*, %s.study_id
            FROM %s, summary_concepts 
            WHERE %s.uid = summary_concepts.study_concept_id
            AND %s.concept_id =
            """ % (table_name, table_name, table_name, table_name)
        cursor.execute(query + " %s ", int(concept_id))
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        for row in cursor.fetchall():
            row = dtuple.DatabaseTuple(desc, row)
            summary = Summary(context, row['summary_id'])
            st = study.Study(context, row['study_id'])
            pairs.append((summary, st))
    except Exception, e:
        context.logger.error(e)
        print traceback.print_exc()
        return None

    return SummarySet(concept_type, concept_id, pairs)


def get_summaries_from_study (context, study):
    """
    For a given Study, return a list of all relevant Summary objects.
    """
    summaries = []
    try:
        cursor = context.get_cursor()
        for m in study.methodologies:
            cursor.execute("""
                SELECT uid
                FROM summaries
                WHERE methodology_id = %s
                ORDER BY uid
                """, m.uid)
            rows = cursor.fetchall()
            for row in rows:
                s = Summary(context, row[0])
                summaries.append(s)
    except Exception, e:
        context.logger.error(e)
    
    return summaries
    


def get_study_concept (concept_type, ):
    """For a SummaryConcept, get the concept instance related to the
    Study itself from the appropriate table (which we must determine
    dynamically)."""
    
    # Figure out which table to use
    table_name = self.CONCEPT_TYPES.get(self.concept_type, '')
    if not table_name:
        return None
    
    # First, get the related study concept
    this_module = sys.modules[__name__]
    # Tricky:  getattr should return one of (Exposure, Outcome, Species),
    # then the parameters passed in should instantiate one of those types
    study_concept = getattr(this_module, 
        table_name.capitalize())(context, self.study_concept_id)
    return study_concept



class SummaryConcept (DTable):
    """
    For a given Summary, an explicit statement that this study's related
    concept is part of what is summarized.
    """
    
    CONCEPT_TYPES = {'e': 'exposures', 'o': 'outcomes', 's': 'species'}
        
    def __init__ (self, context=None, uid=-1):
        self.uid = uid
        self.summary_id = -1
        self.concept_type = ''
        self.study_concept_id = -1
        
    
    
class Summary (canary.context.Cacheable, DTable):
    """
    A specific summary of the relationships between exposures, outcomes,
    species, and human references for a single Study.
    
    These are designed to be aggregated into UberSummaries (not yet defined!) 
    for a particular Concept across the whole database.
    """
    
    TABLE_NAME = 'summaries'
    
    CACHE_KEY = 'summary'
    
    CACHE_CHECK_KEY = 'methodology_id'

    def __init__ (self, context=None, uid=-1):
        try:
            if getattr(self, self.CACHE_CHECK_KEY):
                return
        except AttributeError:
            pass

        self.uid = uid
        # Note: the methodology will reference a study_id, so don't store 
        # study_id again
        self.methodology_id = 0
        self.public_notes = ''
        # Positive findings
        self.has_susceptibility = False
        self.has_latency = False
        self.has_exposure_risk = False
        self.has_warning = False
        # Negative findings; store separately for easy query
        self.hasnt_susceptibility = False
        self.hasnt_latency = False
        self.hasnt_exposure_risk = False
        self.hasnt_warning = False
        # Note: each of the following references a study_id already also
        self.exposures = []
        self.outcomes = []
        self.species = []
        # HumanStudy references
        self.human_refs = []


    def get_human_ref (self, context, ref_id):
        """Get a particular human reference."""
        for ref in self.human_refs:
            if ref == ref_id:
                return HumanStudy(context, ref_id)
        return None


    def load (self, context):
        if self.uid == -1:
            return
        
        # Is it already loaded?  Convenience check for client calls
        # don't need to verify loads from the cache.
        if context.config.use_cache:
            try:
                if getattr(self, self.CACHE_CHECK_KEY):
                    # Already loaded
                    return
            except AttributeError:
                # Note already loaded, so continue
                pass

        try:
            cursor = context.get_cursor()
            
            # Summary, load thyself
            cursor.execute("""
                SELECT * 
                FROM summaries
                WHERE uid = %s
                """, self.uid)
            fields = [d[0] for d in cursor.description]
            desc = dtuple.TupleDescriptor([[f] for f in fields])
            rows = cursor.fetchall()
            if not rows:
                print 'Tried to load summary with id', self.uid
                print traceback.print_exc()
                raise ValueError
            row = dtuple.DatabaseTuple(desc, rows[0])
            for f in fields:
                self.set(f, row[f])
                
            # ...and thy concepts
            cursor.execute("""
                SELECT *
                FROM summary_concepts
                WHERE summary_id = %s
                """, self.uid)
            fields = [d[0] for d in cursor.description]
            desc = dtuple.TupleDescriptor([[f] for f in fields])
            rows = cursor.fetchall()
            for row in rows:
                row = dtuple.DatabaseTuple(desc, row)
                summary_concept = SummaryConcept(uid=row['uid'])
                summary_concept.summary_id = self.uid
                summary_concept.concept_type = row['concept_type']
                summary_concept.study_concept_id = row['study_concept_id']
                getattr(self, 
                    summary_concept.CONCEPT_TYPES[row['concept_type']]).append(summary_concept)
            
            # ...and thy references
            cursor.execute("""
                SELECT human_study_id 
                FROM summary_human_refs
                WHERE summary_id = %s
                ORDER by uid 
                """, self.uid)
            fields = [d[0] for d in cursor.description]
            desc = dtuple.TupleDescriptor([[f] for f in fields])
            rows = cursor.fetchall()
            for row in rows:
                self.human_refs.append(row[0])
            
            self.cache_set(context)
        #except ValueError:
        #    raise ValueError
        except:
            print traceback.print_exc()

    def save (self, context):
        cursor = context.get_cursor()
        try:
            if self.uid == -1:
                cursor.execute("""
                    INSERT INTO summaries
                    (methodology_id, public_notes, has_susceptibility,
                    has_latency, has_exposure_risk, has_warning,
                    hasnt_susceptibility, hasnt_latency,
                    hasnt_exposure_risk, hasnt_warning)
                    VALUES (%s, %s, %s,
                        %s, %s, %s,
                        %s, %s, 
                        %s, %s)
                    """, (self.methodology_id, self.public_notes, int(self.has_susceptibility),
                    int(self.has_latency), int(self.has_exposure_risk), int(self.has_warning),
                    int(self.hasnt_susceptibility), int(self.hasnt_latency), 
                    int(self.hasnt_exposure_risk), int(self.hasnt_warning)
                    ))
                self.uid = self.get_new_uid(context)
                context.logger.info('Summary created with uid %s', self.uid)
    
            else:
                cursor.execute("""
                    UPDATE summaries
                    SET methodology_id = %s, public_notes = %s, has_susceptibility = %s,
                        has_latency = %s, has_exposure_risk = %s, has_warning = %s,
                        hasnt_susceptibility = %s, hasnt_latency = %s, 
                        hasnt_exposure_risk = %s, hasnt_warning = %s
                    WHERE uid = %s
                    """, (self.methodology_id, self.public_notes, int(self.has_susceptibility),
                        int(self.has_latency), int(self.has_exposure_risk), int(self.has_warning),
                        int(self.hasnt_susceptibility), int(self.hasnt_latency),
                        int(self.hasnt_exposure_risk), int(self.hasnt_warning),
                        self.uid))
                context.logger.info('Summary %s updated', self.uid)
            
            # Update summary_concepts
            cursor.execute("""
                DELETE FROM summary_concepts
                WHERE summary_id = %s
                """, self.uid)
            for key, table in SummaryConcept.CONCEPT_TYPES.items():
                for concept in getattr(self, table):
                    cursor.execute("""
                    INSERT INTO summary_concepts
                    (summary_id, concept_type, study_concept_id)
                    VALUES (%s, %s, %s)
                    """, (self.uid, key, concept.study_concept_id))
            
            # Update summary_human_refs
            cursor.execute("""
                DELETE FROM summary_human_refs
                WHERE summary_id = %s
                """, self.uid)
            for id in self.human_refs:
                cursor.execute("""
                    INSERT INTO summary_human_refs
                    (summary_id, human_study_id)
                    VALUES (%s, %s)
                    """, (self.uid, id))
            
            self.cache_set(context)

        except Exception, e:
            print traceback.print_exc()
            context.logger.error(e)
        
           
           
    def delete (self, context):
        cursor = context.get_cursor()
        try:
            # Get rid of all human studies referenced from this study
            cursor.execute("""
                DELETE FROM summary_human_refs
                WHERE summary_id = %s
                """, self.uid)
            
            cursor.execute("""
                DELETE FROM summary_concepts
                WHERE summary_id = %s
                """, self.uid)
            
            cursor.execute("""
                DELETE FROM summaries
                WHERE uid = %s
                """, self.uid)
            self.cache_delete(context)
        except Exception, e:
            context.logger.error(e)



class SummaryRow:
    """
    A single row in a user-visible SummarySet table.  Provides
    convenient access for rendering.
    """

    pass


class SummarySet:
    """
    A set of studies and summaries pertaining to a particular pair of species,
    exposure, or outcome, in these combinations:
    
        exposure -> species
        outcome -> species
        species -> exposure
    """
    
    LEVELS = ['susceptibility', 'latency', 'exposure_risk', 'warning']

    def __init__ (self, concept_type, concept_id, summary_pairs=[]):
        """
        summary_pairs are (a_summary, its_study) tuples.
        """
        self.concept_type = concept_type
        self.concept_id = concept_id
        self.summary_pairs = summary_pairs
        self.study_concepts = {'exposures':{}, 'outcomes':{}, 
            'species':{}}
        self.concepts = {'exposures':{}, 'outcomes':{}, 'species':{}}
        self.scores = {}
        self.rows = []
        for level in self.LEVELS:
            setattr(self, 'has_%s' % level, 0)
            setattr(self, 'hasnt_%s' % level, 0)
        
    def set_scores (self, summary, meth):
        try:
            pass
        except: 
            pass
            
                        

    def summarize (self, context):
        """
        Generate summary rows suitable for rendering in the UI.
        """
        self.study_concept = Concept(context, self.concept_id)
        for summary, st in self.summary_pairs:
            meth = study.Methodology()
            meth.uid = summary.methodology_id
            meth.load(context)
            level = meth.evidence_level()             
            #self.set_scores(summary, meth)
            for attr, concept_type in (
                ('exposures', 'Exposure'), 
                ('outcomes', 'Outcome'), 
                ('species', 'Species')):
                for con in getattr(summary, attr):
                    concept = getattr(study, concept_type)()
                    concept.uid = con.study_concept_id
                    concept.load(context)
                    score_key = '%s:%s' % (concept_type, concept.term)
                    if not self.scores.has_key(score_key):
                        self.scores[score_key] = {}

                    for l in self.LEVELS:
                        has_level = 'has_%s' % l
                        if getattr(summary, has_level):
                            try:
                                self.scores[score_key][has_level] = \
                                    max(self.scores[score_key][has_level], level)
                            except:
                                self.scores[score_key][has_level] = level

                        hasnt_level = 'hasnt_%s' % l
                        if getattr(summary, hasnt_level):
                            try:
                                self.scores[score_key][hasnt_level] = \
                                    max(self.scores[score_key][hasnt_level], level)
                            except:
                                self.scores[score_key][hasnt_level] = level
                            
        import pprint
        pprint.pprint(self.scores)


        

