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




class SubStudy (DTable):

    # A SubStudy must have one TYPE
    TYPES = {
        'experimental' : 1,
        'descriptive' : 2,
        'aggregate' : 3,
        'cross sectional' : 4,
        'cohort' : 5,
        'case control' : 6,
        }
        
    # A SubStudy can have at most one TIMING
    TIMING = {
        'unknown' : 0,
        'historical' : 1,
        'concurrent' : 2,
        'repeated' : 3,
        'mixed' : 4,
        }
    
    # A SubStudy can have at most one SAMPLING
    SAMPLING = {
        'unknown' : 0,
        'exposure' : 1,
        'outcome' : 2,
        'both' : 3,
        }
        
    # A SubStudy can have at most one CONTROLS
    CONTROLS = {
        'no' : 0,
        'yes' : 1,
        'both' : 2,
        }
        
    # A SubStudy can have at most one ROUTE
    ROUTE = {
        'ingestion' : 0,
        'inhalation' : 1,
        'mucocutaneous' : 2,
        'vector' : 3,
        'other' : 4,
        }


    def __init__ (self, uid=-1):
        self.uid = uid
        self.study_id = -1
        self.study_type_id = -1
        self.sample_size = 0
        #self.timing = self.TIMING['unknown']
        #self.sampling = self.SAMPLING['unknown']
        #self.controls = self.CONTROLS['no']
        #self.route = self.ROUTE['other']
        self.timing = None
        self.sampling = None
        self.controls = None
        self.route = None
        self.comments = ''
        self.date_modified = None
        self.date_entered = None


    def __str__ (self):
        out = []
        out.append('<SubStudy uid=%s study_id=%s' % (self.uid, self.study_id))
        out.append('\tstudy_type=%s' % self.get_text_value(self.TYPES, self.study_type_id))
        out.append('\tsample_size=%s' % self.sample_size)
        for item in ['timing', 'sampling', 'controls', 'route']:
            out.append('\t%s=%s' % (item, getattr(self, 'get_' + item)(text=True)))
        out.append('\tcomments=%s' % self.comments or '')
        out.append('/>')
        return '\n'.join(out)
        

    def get_text_value (self, lookup_table, value):
        for k, v in lookup_table.iteritems():
            if v == value:
                return k
        return ''


    def set_sample_size (self, n):
        
        try:
            if int(n):
                self.sample_size = n
        except:
            pass
        
        
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


    def set_study_type (self, value):
        """
        Each substudy has exactly one type.
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


    def get_study_type (self, text=False):
        """
        Return the study design type.
        """
        if text:
            return self.get_text_value(self.TYPES, self.study_type_id)
        else:
            return self.study_type_id


    def delete (self, cursor):
        """
        Delete this substudy from the database.
        """
        if not self.uid == -1:
            try:
                cursor.execute("""
                    DELETE FROM substudies
                    WHERE uid = %s
                    """, self.uid)
            except:
                import sys
                print 'MySQL exception:'
                for info in sys.exc_info():
                    print 'exception:', info
    
    def save (self, cursor):
        
        if self.uid == -1:
            #print 'inserting new substudy'
            cursor.execute("""
                INSERT INTO substudies
                (uid, study_id, study_type_id, 
                sample_size, timing, 
                sampling, controls, route, comments,
                date_modified, date_entered)
                VALUES 
                (NULL, %s, %s, 
                %s, %s,
                %s, %s, %s, %s,
                NOW(), NOW())
                """, (self.study_id, self.study_type_id,
                self.sample_size, self.timing,
                self.sampling, self.controls, self.route, self.comments)
                )
            #print 'inserted new substudy'
            self.uid = self.get_new_uid(cursor)
            #print 'set new substudy uid to %s' % self.uid
        else:
            #print 'updating substudy %s' % self.uid
            try:
                cursor.execute("""
                    UPDATE substudies
                    SET study_id = %s, study_type_id = %s,
                    sample_size = %s, timing = %s,
                    sampling = %s, controls = %s, route = %s, comments = %s,
                    date_modified = NOW()
                    WHERE uid = %s
                    """, (self.study_id, self.study_type_id,
                    self.sample_size, self.timing, 
                    self.sampling, self.controls, self.route, self.comments,
                    self.uid)
                    )
            except:
                import sys
                print 'MySQL exception:'
                for info in sys.exc_info():
                    print 'exception:', info
            #print 'updated substudy %s' % self.uid
        # FIXME: should this be set from the SQL?
        self.date_modified = time.strftime(str('%Y-%m-%d'))



    def create_form (self):
        
        form = MyForm()
        
        # all substudy types get a sample size
        form.add(IntWidget, 'sample_size',
            title='Sample size (study n)',
            size=10, value=int(self.sample_size),
            required=True)
            
        # all substudy types get a route
        form.add(SingleSelectWidget, 'route',
            title='Route of exposure',
            value=self.get_route(),
            options=[(val, name, val) for name, val in self.ROUTE.items()],
            sort=True,
            required=True)
        
        # substudy types except experimental and descriptive get timing
        if not self.get_study_type() in [
            self.TYPES['experimental'],
            self.TYPES['descriptive']
            ]:
            form.add(SingleSelectWidget, 'timing',
                title='Timing',
                value=self.get_timing(),
                options=[(val, name, val) for name, val in self.TIMING.items()],
                sort=True,
                required=True)
    
        # all the 'c*' substudy types get controls
        if self.get_study_type() in [
            self.TYPES['cross sectional'],
            self.TYPES['cohort'], 
            self.TYPES['case control']
            ]:
            form.add(SingleSelectWidget, 'controls',
                title='Controls from same population?',
                value=self.get_controls(),
                options=[(val, name, val) for name, val in self.CONTROLS.items()],
                sort=True,
                required=True)
            
        # only cross sectional substudies get sampling
        if self.get_study_type() == self.TYPES['cross sectional']:
            form.add(SingleSelectWidget, 'sampling',
                title='Sampling',
                value=self.get_sampling(),
                options=[(val, name, val) for name, val in self.SAMPLING.items()],
                sort=True,
                required=True)
                    
        # every substudy type has comments
        form.add(TextWidget, 'comments', 
            title='Comments',
            rows='4', cols='60',
            wrap='virtual',
            value=self.comments)
        
        form.add_submit('update', value='update')
        form.add_submit('finish', value='finish')

        return form
        
    
    def process_form (self, form):
        
        # all substudy types get a sample size
        print 'setting sample size to %s' % form['sample_size']
        self.sample_size = form['sample_size']
            
        # all substudy types get a route
        print 'setting route to %s' % form['route']
        self.set_route(form['route'])
        
        # all substudy types but experimental and descriptive get timing
        if not self.get_study_type() in [
            self.TYPES['experimental'],
            self.TYPES['descriptive']
            ]:
            print 'setting timing to %s' % form['timing']
            self.set_timing(form['timing'])
        
        # all 'c*' substudy types get controls
        if self.get_study_type() in [
            self.TYPES['cross sectional'],
            self.TYPES['cohort'],
            self.TYPES['case control']
            ]:
            print 'setting controls to %s' % form['controls']
            self.set_controls(form['controls'])
            
        # only cross sectional gets sampling
        if self.get_study_type() == self.TYPES['cross sectional']:
            print 'setting sampling to %s' % form['sampling']
            self.set_sampling(form['sampling'])

        # every substudy type can have comments
        if form['comments']:
            print 'setting comments'
            self.comments = form['comments']



class Exposure (DTable):
    
    def __init__ (self):
        pass
        

class Outcome (DTable):
    
    def __init__ (self):
        pass
        

class Location (DTable):
    
    def __init__ (self):
        pass
        

class Species (DTable):
    
    def __init__ (self):
        pass
        



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
        'irrelevant' : 1,
        'traditional' : 2,
        'descriptive' : 3,
        'review' : 4,
        'outcomes only' : 5,
        'exposures only' : 6,
        'curated' : 7,
        }
            
    # For dynamic iteration over related tables
    TABLES = {
        'substudies' : SubStudy,
        'outcomes': Outcome,
        'exposures': Exposure,
        'species': Species,
        'locations': Location,
        }


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
        self.has_genomic = False
        self.comments = ''
        self.substudies = []
        self.outcomes = []
        self.exposures = []
        self.species = []
        self.locations = []
        self.date_modified = None
        self.date_entered = None
        
    
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
    
    
    def add_substudy (self, substudy):
        for ss in self.substudies:
            if ss.uid == substudy.uid:
                return
        substudy.study_id = self.uid
        self.substudies.append(substudy)
        
    def get_substudy (self, id):
        for substudy in self.substudies:
            if substudy.uid == id:
                return substudy
        return None

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
        

    def save (self, cursor):
        
        if self.uid == -1:
            #print 'inserting new study'
            try:
                cursor.execute("""
                    INSERT INTO studies
                    (uid, 
                    record_id, status, article_type, curator_user_id, 
                    has_outcomes, has_exposures, 
                    has_relationships, has_interspecies, 
                    has_exposure_linkage, has_outcome_linkage,
                    has_genomic, comments, 
                    date_modified, date_entered)
                    VALUES 
                    (NULL, 
                    %s, %s, %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    %s, %s,
                    NOW(), NOW())
                    """, (self.record_id, self.status, self.article_type, self.curator_user_id,
                    self.has_outcomes, self.has_exposures, 
                    self.has_relationships, self.has_interspecies, 
                    self.has_exposure_linkage, self.has_outcome_linkage,
                    self.has_genomic, self.comments)
                    )
            except:
                # FIXME: proper exceptions
                print 'MySQL exception on study.save(new)'
                
            self.uid = self.get_new_uid(cursor)

        else:
            try:
                #print 'updating study:', self.__str__()
                cursor.execute("""
                    UPDATE studies
                    SET record_id = %s, status = %s, article_type = %s, curator_user_id = %s,
                    has_outcomes = %s, has_exposures = %s, 
                    has_relationships = %s, has_interspecies = %s, 
                    has_exposure_linkage = %s, has_outcome_linkage = %s,
                    has_genomic = %s, comments = %s,
                    date_modified = NOW()
                    WHERE uid = %s
                    """, (self.record_id, self.status, self.article_type, self.curator_user_id,
                    self.has_outcomes, self.has_exposures, 
                    self.has_relationships, self.has_interspecies, 
                    self.has_exposure_linkage, self.has_outcome_linkage,
                    self.has_genomic, self.comments,
                    self.uid)
                    )
            except:
                import traceback
                print 'MySQL exception on study.update'
                print 'exception:', traceback.print_exc()
            #print 'updated study %s' % self.uid
        # FIXME: should this be set from the SQL?
        self.date_modified = time.strftime(str('%Y-%m-%d'))
        
        
        # update all the related table values
        #print 'going to update related tables...'
        for table_name in self.TABLES.keys():
            #print 'attempting to update table items for', table_name
            for item in getattr(self, table_name):
                print 'saving item:', item
                item.save(cursor)
        



if __name__ == '__main__':
    import MySQLdb
    conn = MySQLdb.connect(db='canary-dev',user='dlc33',passwd='floogy')
    cursor = conn.cursor()
    s1 = Study()
    s1.curator_user_id = 'dchud'
    s1.set_status('unclaimed')
    s1.set_article_type('review')
    s1.has_exposure_linkage = True
    s1.save(cursor)
    print 'created study, creating substudy'
    
    ss1 = SubStudy()
    ss1.study_id = s1.uid
    ss1.set_controls('both')
    ss1.set_timing('concurrent')
    ss1.set_sampling('exposure')
    ss1.set_study_type('cross sectional')
    s1.substudies.append(ss1)
    s1.save(cursor)
    print 'saved study with substudy'
    
    
    print 'setting ss1 route to ingestion'
    ss1.set_route('ingestion')
    s1.save(cursor)
    
    ss2 = SubStudy()
    ss2.study_id = s1.uid
    ss2.set_study_type('cohort')
    ss2.set_timing('mixed')
    s1.substudies.append(ss2)
    s1.save(cursor)
    print 'saved study with substudy2'
