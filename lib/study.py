# study.py

import dtuple
import time
import types

from quixote.form2 import StringWidget, TextWidget, IntWidget
from quixote.form2 import SingleSelectWidget, CheckboxWidget, SubmitWidget
from quixote.html import htmltext

from canary.qx_defs import MyForm
from canary.utils import DTable


class TableValue:
    
    def __init__ (self, uid=-1, value=None):
        self.uid = uid
        self.value = value
    
    def get_uid (self):
        return self.uid
    
    def set_uid (self, uid):
        self.uid = uid
        
    def get_value (self):
        return self.value
        
    def set_value (self, value):
        self.value = value


class Study (DTable):

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
        'traditional' : 1,
        'review' : 2,
        'outcomes only' : 3,
        'exposures only' : 4,
        'curated' : 5,
        }
    
    # A Study can have zero-to-many STUDY_TYPEs
    TYPES = {
        'experimental' : 1,
        'descriptive' : 2,
        'aggregate' : 3,
        'cross sectional' : 4,
        'cohort' : 5,
        'case control' : 6,
        }
        
    # A Study can have at most one TIMING
    TIMING = {
        'unknown' : 0,
        'historical' : 1,
        'concurrent' : 2,
        'repeated' : 3,
        'mixed' : 4,
        }
    
    # A Study can have at most one SAMPLING
    SAMPLING = {
        'unknown' : 0,
        'exposure' : 1,
        'outcome' : 2,
        'both' : 3,
        }
        
    # A Study can have at most one CONTROLS
    CONTROLS = {
        'no' : 0,
        'yes' : 1,
        'both' : 2,
        }
        
    # A Study can have at most one ROUTE
    ROUTE = {
        'ingestion' : 0,
        'inhalation' : 1,
        'mucocutaneous' : 2,
        'vector' : 3,
        'other' : 4,
        }
        
    TABLES = [
        'types', 
        'outcomes', 
        'exposures', 
        'species', 
        'locations'
        ]

    def __init__ (self, uid=-1, record_id=-1):
    
        self.uid = uid
        self.record_id = record_id
        self.status = self.STATUS_TYPES['unclaimed']
        self.article_type = self.ARTICLE_TYPES['unknown']
        self.curator_user_id = ''
        self.has_outcomes = False
        self.has_exposures = False
        self.has_relationships = False
        self.has_interspecies = False
        self.has_exposure_linkage = False
        self.has_outcome_linkage = False
        self.comments = ''
        self.types = []
        self.outcomes = []
        self.exposures = []
        self.species = []
        self.locations = []
        self.sample_size = ''
        self.timing = None
        self.sampling = None
        self.controls = None
        self.route = None
        self.date_modified = None
        self.date_entered = None
        
    
    def __str__ (self):
        out = []
        out.append('<Study uid=%s record_id=%s' % (self.uid, self.record_id))
        out.append('\tstatus=%s' % self._get_text_value(self.STATUS_TYPES, self.status))
        out.append('\tcurator_user_id=%s' % self.curator_user_id)
        out.append('\tarticle_type=%s' % self._get_text_value(self.ARTICLE_TYPES, self.article_type))
        out.append('\thas_outcomes=%s' % self.has_outcomes)
        out.append('\thas_exposures=%s' % self.has_exposures)
        out.append('\thas_relationships=%s' % self.has_relationships)
        out.append('\thas_interspecies=%s' % self.has_interspecies)
        out.append('\thas_exposure_linkage=%s' % self.has_exposure_linkage)
        out.append('\thas_outcome_linkage=%s' % self.has_outcome_linkage)
        # What are you wanting here?  TYPES is not like OUTCOMES, is it?
        #for table_name in self.TABLES:
        #    if len(getattr(self, table_name)) > 0:
        #        out.append('\t%s=' % table_name + \
        #            ','.join(getattr(self, 'get_' + table_name)(text=True)))
        if len(self.types) > 0:
            out.append('\ttypes=' + ','.join(self.get_types(text=True)))
        out.append('\tcomments=%s' % self.comments or '')
        out.append('/>')
        return '\n'.join(out)
        
        
        
    def _get_text_value (self, lookup_table, value):
        iter = lookup_table.iteritems()
        for k, v in iter:
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
            return self._get_text_value(self.STATUS_TYPES, self.status)
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
            return self._get_text_value(self.ARTICLE_TYPES, self.article_type)
        else:
            return self.article_type
    
    def set_type (self, value):
        """
        Study.types can have multiple values, but each must be valid, 
        and type cannot repeat.
        """
        if type(value) is types.StringType:
            
            if value in self.TYPES.keys() \
                and not value in self.types:
                    self.types.append(self.TYPES[value])
                    
        elif type(value) == type(htmltext('a')):
            
            str_value = str(value)
            if str_value in self.TYPES.keys() \
                and not str_value in self.types:
                    self.types.append(self.TYPES[str_value])

        elif type(value) is types.IntType:
            
            if value in self.TYPES.values() \
                and not value in self.types:
                    self.types.append(value)
                
    def set_types (self, values):
        """
        Empty, then refill, self.types; useful for refreshing from a form.
        """
        self.types = []
        for value in values:
            self.set_type(value)
    
    def has_type (self, value):
        """
        Simple quick lookup for any type
        """
        if type(value) is types.StringType:
            
            if value in self.get_types(text=True):
                return True
                
        elif type(value) == type(htmltext('a')):
            
            if str(value) in self.get_types(text=True):
                return True
                
        elif type(value) is types.IntType:
            
            if self.TYPES[type] in self.get_types():
                return True
                
        return False
            
    def get_types (self, text=False, sort=True):
        """
        Called r_types ("return types") for clarity.
        """
        r_types = []
        for t in self.types:
            if text:
                r_types.append(self._get_text_value(self.TYPES, t))
            else:
                r_types.append(t)
            
        if sort:
            r_types.sort()
            
        return r_types
        
    def set_timing (self, timing):
        
        if type(timing) is types.StringType:
            
            if timing in self.TIMING.keys():
                self.timing = self.TIMING[timing]

        elif type(timing) is types.IntType:

            if timing in self.TIMING.values():
                self.timing = timing
    
    def get_timing (self, text=False):
        if text:
            return self._get_text_value(self.TIMING, self.timing)
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
            return self._get_text_value(self.SAMPLING, self.sampling)
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
            return self._get_text_value(self.CONTROLS, self.controls)
        else:
            return self.controls
    
    def set_route (self, route):
        
        if type(route) is types.StringType:
            
            if route in self.ROUTE.keys():
                self.route = self.ROUTE[route]
                
        elif type(route) is types.IntType:
            
            if route in self.ROUTE.values():
                self.route = route
    
    def get_route (self, text=False):
        if text:
            return self._get_text_value(self.ROUTE, self.route)
        else:
            return self.route


    def load (self, cursor):
        
        if self.uid == -1:
            return

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

        # each field in this list is a list attribute; multivalues will be appended
        for table in self.TABLES:
            select_phrase = """SELECT * FROM study_%s """ % table
            cursor.execute(select_phrase + """
                WHERE study_id = %s
                """, (self.uid))
            rows = cursor.fetchall()
            values = []
            for row in rows:
                # row[0] : uid ; row[1] : study_id (i.e. self.uid)
                values.append(int(row[2]))
            if len(values) > 0:
                table_set_function = getattr(self, 'set_' + table)
                table_set_function(values)
        

    def save (self, cursor):
        
        if self.uid == -1:
            print 'inserting new study'
            cursor.execute("""
                INSERT INTO studies
                (uid, 
                record_id, status, article_type, curator_user_id, 
                has_outcomes, has_exposures, 
                has_relationships, has_interspecies, 
                has_exposure_linkage, has_outcome_linkage,
                comments, sample_size, timing, 
                sampling, controls, route, 
                date_modified, date_entered)
                VALUES 
                (NULL, 
                %s, %s, %s, %s,
                %s, %s, 
                %s, %s,
                %s, %s,
                %s, %s, %s, 
                %s, %s, %s,
                NOW(), NOW())
                """, (self.record_id, self.status, self.article_type, self.curator_user_id,
                self.has_outcomes, self.has_exposures, 
                self.has_relationships, self.has_interspecies, 
                self.has_exposure_linkage, self.has_outcome_linkage,
                self.comments, self.sample_size, self.timing, 
                self.sampling, self.controls, self.route)
                )
            print 'inserted new study'
            self.uid = self.get_new_uid(cursor)
            print 'set new study uid to %s' % self.uid
        else:
            print 'updating study %s' % self.uid
            try:
                cursor.execute("""
                    UPDATE studies
                    SET record_id = %s, status = %s, article_type = %s, curator_user_id = %s,
                    has_outcomes = %s, has_exposures = %s, 
                    has_relationships = %s, has_interspecies = %s, 
                    has_exposure_linkage = %s, has_outcome_linkage = %s,
                    comments = %s, sample_size = %s, timing = %s,
                    sampling = %s, controls = %s, route = %s,
                    date_modified = NOW()
                    WHERE uid = %s
                    """, (self.record_id, self.status, self.article_type, self.curator_user_id,
                    self.has_outcomes, self.has_exposures, 
                    self.has_relationships, self.has_interspecies, 
                    self.has_exposure_linkage, self.has_outcome_linkage,
                    self.comments, self.sample_size, self.timing, 
                    self.sampling, self.controls, self.route,
                    self.uid)
                    )
            except:
                import sys
                print 'MySQL exception:'
                for info in sys.exc_info():
                    print 'exception:', info
            print 'updated study %s' % self.uid
        # FIXME: should this be set from the SQL?
        self.date_modified = time.strftime(str('%Y-%m-%d'))
        
        
        # re-insert all the related table values
        for table in ['types', 'outcomes', 'exposures', 'species', 'locations']:
            # clear all existing values first
            delete_phrase = """DELETE FROM study_%s """ % table
            cursor.execute(delete_phrase + """
                WHERE study_id = %s
                """, self.uid)
                
            # now re-insert
            for value in getattr(self, table):
                insert_phrase = """INSERT INTO study_%s """ % table
                cursor.execute(insert_phrase + """
                    VALUES (NULL, %s, %s)
                    """, (self.uid, value))
                        
                        
                        
    def create_summary_form (self):
        
        print 'creating form'
        form = MyForm()
        
        # only curated types get these options
        if self.get_article_type() == self.ARTICLE_TYPES['curated']:
            
            # all types get a sample size
            form.add(IntWidget, 'sample_size',
                title='Sample size (study n)',
                size=10, value=int(self.sample_size),
                required=True)
                
            # all types get a route
            form.add(SingleSelectWidget, 'route',
                title='Route of exposure',
                value=self.get_route(),
                options=[(val, name, val) for name, val in self.ROUTE.items()],
                sort=True,
                required=True)

            # study types except experimental and descriptive get timing
            if not self.has_type('experimental') \
                and not self.has_type('descriptive'):
                form.add(SingleSelectWidget, 'timing',
                    title='Timing',
                    value=self.get_timing(),
                    options=[(val, name, val) for name, val in self.TIMING.items()],
                    sort=True,
                    required=True)
        
            # all the 'c*' study types get controls
            if self.has_type('cross sectional') \
                or self.has_type('cohort') \
                or self.has_type('case control'):
                form.add(SingleSelectWidget, 'controls',
                    title='Controls from same population?',
                    value=self.get_controls(),
                    options=[(val, name, val) for name, val in self.CONTROLS.items()],
                    sort=True,
                    required=True)
                
            # only cross sectional gets sampling
            if self.has_type('cross sectional'):
                form.add(SingleSelectWidget, 'sampling',
                    title='Sampling',
                    value=self.get_sampling(),
                    options=[(val, name, val) for name, val in self.SAMPLING.items()],
                    sort=True,
                    required=True)
                    
        # every article and study type has comments
        form.add(TextWidget, 'comments', 
            title='Comments',
            rows='4', cols='60',
            wrap='virtual',
            value=self.comments)
        
        form.add_submit('update', value='update')
        form.add_submit('finish', value='finish')

        return form
        
    
    def process_summary_form(self, form):
        
        # only curated articles get these options
        if self.get_article_type() == self.ARTICLE_TYPES['curated']:
        
            # all curated types get a sample size
            print 'setting sample size to %s' % form['sample_size']
            self.sample_size = form['sample_size']
                
            # all curated types get a route
            print 'setting route to %s' % form['route']
            self.set_route(form['route'])
            
            # all curated types but experimental and descriptive get timing
            if not self.has_type('experimental') \
                and not self.has_type('descriptive'):
                print 'setting timing to %s' % form['timing']
                self.set_timing(form['timing'])
            
            # all the curated 'c*' types get controls
            if self.has_type('cross sectional') \
                or self.has_type('cohort') \
                or self.has_type('case control'):
                print 'setting controls to %s' % form['controls']
                self.set_controls(form['controls'])
                
            # only cross sectional gets sampling
            if self.has_type('cross sectional'):
                print 'setting sampling to %s' % form['sampling']
                self.set_sampling(form['sampling'])

        # every article and study type has comments
        if form['comments']:
            print 'setting comments'
            self.comments = form['comments']
        


if __name__ == '__main__':
    import MySQLdb
    conn = MySQLdb.connect(db='canary-dev',user='dlc33',passwd='floogy')
    cursor = conn.cursor()
    s1 = Study()
    s1.curator_user_id = 'dchud'
    s1.set_status('unclaimed')
    s1.set_article_type('review')
    s1.has_exposure_linkage = True
    s1.set_controls('both')
    s1.set_timing('concurrent')
    s1.set_sampling('exposure')
    s1.set_type('cross sectional')
    s1.set_types(['cohort', 'experimental'])
    s1.save(cursor)
    print s1
    
    print '\n---\nupdating current Study()\n---'
    s1.set_type('aggregate')
    print s1
    s1.save(cursor)
    
    print '\n---\nloading into new Study()\n---'
    s2 = Study(s1.uid)
    s2.load(cursor)
    print s2
