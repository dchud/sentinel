# report.py

import time

from canary.utils import DTable



class Report (DTable):

    # FIXME:  does this only belong here or on loader.QueuedRecord?
    STATUS_UNCLAIMED = 0
    STATUS_CLAIMED = 1
    STATUS_CURATED = 2
    # FIXME: get a naming convention
    STATUS_FINISHED = STATUS_CURATED
    
    TYPE_UNKNOWN = 0
    TYPE_TRADITIONAL = 1
    TYPE_REVIEW = 2
    TYPE_OUTCOMES_ONLY = 4
    TYPE_EXPOSURES_ONLY = 8
    
    def __init__ (self, uid=-1, record_id=-1, status=STATUS_UNCLAIMED, type=TYPE_UNKNOWN):
    
        self.uid = uid
        self.record_id = record_id
        self.status = status
        self.curator_user_id = ''
        # FIXME:
        self.type = type
        self.is_traditional = False
        self.is_review = False
        self.is_outcomes_only = False
        self.is_exposure_only = False
        self.meta = {
            'has_exposures': False,
            'has_outcomes': False,
            'has_interspecies': False,
            'has_exposure_linkage': False,
            'has_outcome_linkage': False
            }
        
        self.comments = ''
        self.studies = []
        
    
    def load (self, cursor):
        
        if self.uid == -1:
            return

        cursor.execute("""
                       SELECT *
                       FROM reports
                       WHERE uid = %s
                       """, self.uid)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        if rows and len(rows) > 0:
            row = dtuple.DatabaseTuple(desc, rows[0])
            for field in fields:
                self.set(field, row[field])


    def save (self, cursor):
        
        if self.uid == -1:
            cursor.execute("""
                           INSERT INTO reports
                           (uid, record_id, status, curator_user_id,
                           is_traditional, is_review, is_outcomes_only, is_exposure_only, 
                           has_exposures, has_outcomes, has_interspecies,
                           has_exposure_linkage, has_outcome_linkage,
                           comments, date_modified)
                           VALUES (NULL, %s, %s, %s,
                           %s, %s, %s, %s,
                           %s, %s, %s,
                           %s, %s,
                           %s, CURDATE())
                           """, (self.record_id, self.status, self.curator_user_id,
                           self.is_traditional, self.is_review, self.is_outcomes_only, self.is_exposure_only,
                           self.meta['has_exposures'], self.meta['has_outcomes'], self.meta['has_interspecies'],
                           self.meta['has_exposure_linkage'], self.meta['has_outcome_linkage'],
                           self.comments)
                           )
            self.uid = self.get_new_uid(cursor)
        else:
            cursor.execute("""
                           UPDATE reports
                           SET record_id = %s, status = %s, curator_user_id = %s,
                           is_traditional = %s, is_review = %s, 
                           is_outcomes_only = %s, is_exposure_only = %s, 
                           has_exposures = %s, has_effects = %s, has_interspecies = %s,
                           has_exposure_linkage = %s, has_outcome_linkage = %s,
                           comments = %s, date_modified = CURDATE(),
                           WHERE uid = %s
                           """, (self.record_id, self.type, self.curator_user_id,
                           self.is_traditional, self.is_review,
                           self.is_outcomes_only, self.is_exposure_only,
                           self.meta['has_exposures'], self.meta['has_effects'], self.meta['has_interspecies'],
                           self.meta['has_exposure_linkage'], self.meta['has_outcome_linkage'],
                           self.comments,
                           self.uid)
                           )
        # FIXME: should this be set from the SQL?
        self.date_modified = time.strftime(str('%Y-%m-%d'))


class Study (DTable):

    TYPE_UNKNOWN = 0
    TYPE_EXPERIMENTAL = 1
    TYPE_DESCRIPTIVE = 2
    TYPE_AGGREGATE = 4
    TYPE_CROSS_SECTIONAL = 8
    TYPE_COHORT = 16
    TYPE_CASE_CONTROL = 32
    
    
    def __init__ (self, uid=-1, report_id=-1, type=TYPE_UNKNOWN):
    
        self.uid = uid
        self.report_id = report_id
        self.type = type
        self.comments = ''
        self.exposures = {}
        self.outcomes = {}
        self.species = {}
        self.date_modified = ''


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


    def save (self, cursor):
        
        if self.uid == -1:
            cursor.execute("""
                           INSERT INTO studies
                           (uid, report_id, type, comments, date_modified)
                           VALUES (NULL, %s, %s, %s, CURDATE())
                           """, (self.report_id, self.type, self.comments)
                           )
            self.uid = self.get_new_uid(cursor)

        else:
            cursor.execute("""
                           UPDATE studies
                           SET report_id = %s, type = %s, comments = %s,
                               date_modified = CURDATE(),
                           WHERE uid = %s
                           """, (self.report_id, self.type, self.comments,
                           self.uid)
                           )
        # FIXME: should this be set from the SQL?
        self.date_modified = time.strftime(str('%Y-%m-%d'))
