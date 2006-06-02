# $Id$

import traceback

import canary.context
from canary.utils import DTable
import dtuple


def find_references (context, token=''):
    if not token:
        return get_studies(context)
    studies = []
    cursor = context.get_cursor()
    cursor.execute("""
        SELECT uid
        FROM human_studies
        WHERE reference LIKE %s
        ORDER BY reference
        """, '%s%s' % (token, '%'))
    fields = [d[0] for d in cursor.description]
    desc = dtuple.TupleDescriptor([[f] for f in fields])
    rows = cursor.fetchall()
    for row in rows:
        row = dtuple.DatabaseTuple(desc, row)
        hs = HumanStudy(context, row['uid'])
        studies.append(hs)
    return studies
    

def get_studies (context):
    studies = []
    cursor = context.get_cursor()
    cursor.execute("""
        SELECT uid
        FROM human_studies
        ORDER BY reference
        """)

    fields = [d[0] for d in cursor.description]
    desc = dtuple.TupleDescriptor([[f] for f in fields])
    rows = cursor.fetchall()
    for row in rows:
        row = dtuple.DatabaseTuple(desc, row)
        hs = HumanStudy(context, row['uid'])
        studies.append(hs)
    return studies


class HumanStudy (canary.context.Cacheable, DTable):
    
    CACHE_KEY = 'human_study'
    
    CACHE_CHECK_KEY = 'reference'

    def __init__ (self, context=None, uid=-1):
        try:
            if getattr(self, self.CACHE_CHECK_KEY):
                return
        except AttributeError:
            pass

        self.uid = uid
        self.reference = ''
        self.comments = ''
        
    
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

        cursor = context.get_cursor()
        cursor.execute("""
            SELECT reference, comments
            FROM human_studies
            WHERE uid = %s
            """, self.uid)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        row = cursor.fetchone()
        row = dtuple.DatabaseTuple(desc, row)
        self.reference = row['reference']
        self.comments = row['comments']
        
        if context.config.use_cache:
            context.cache_set('%s:%s' % (self.CACHE_KEY, self.uid), self)

    
    def save (self, context):
        cursor = context.get_cursor()
        
        try:
            if self.uid == -1:
                cursor.execute("""
                    INSERT INTO human_studies
                    (reference, comments)
                    VALUES (%s, %s)
                    """, (self.reference, self.comments))
                self.uid = self.get_new_uid(context)
                context.logger.info('HumanStudy created with uid %s', self.uid)
    
            else:
                cursor.execute("""
                    UPDATE human_studies
                    SET reference = %s, comments = %s
                    WHERE uid = %s
                    """, (self.reference, self.comments, self.uid))
                context.logger.info('HumanStudy %s updates', self.uid)
        except:
            print traceback.print_exc()
            raise Error, 'Duplicate reference'
        
        if context.config.use_cache:
            context.cache_set('%s:%s' % (self.CACHE_KEY, self.uid), self)
           
           
    def delete (self, context):
        cursor = context.get_cursor()
        try:
            # First, delete from summary_human_refs
            cursor.execute("""
                DELETE FROM summary_human_refs
                WHERE human_study_id = %s
                """, self.uid)
            
            cursor.execute("""
                DELETE FROM human_studies
                WHERE uid = %s
                """, self.uid)
            if context.config.use_cache:
                context.cache_delete('%s:%s' % (self.CACHE_KEY, self.uid))
        except Exception, e:
            context.logger.error(e)
