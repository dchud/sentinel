#!/usr/bin/env python

from canary.context import Context
from canary.loader import QueuedRecord

con = Context()
cursor = con.get_cursor()
cursor.execute( """
    SELECT studies.record_id, study_history.study_id, study_history.modified
    FROM study_history, studies
    WHERE study_history.message = 'Set record status to curated'
    AND study_history.study_id = studies.uid
    ORDER BY studies.record_id ASC, study_history.modified ASC 
    """ )

for row in cursor:
    print "record_id:%i; study_id:%i; curated:%s" % row
    # update either QUEUED_RECORDS or STUDIES with curated time
    # r = QueuedRecord(con,row[0])
    # r.date_curated = row[2]
    # r.save


