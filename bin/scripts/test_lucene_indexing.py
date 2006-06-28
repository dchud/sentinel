#!/usr/bin/env python2.3

# Test creation of a lucene search index using canary database.
#
# $Id$

import os
os.environ['GCJ_PROPERTIES'] = "disableLuceneLocks=true"

from optparse import OptionParser
import pprint

import canary.context
from canary.loader import QueuedRecord
import canary.search


if __name__ == '__main__':
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    parser.add_option('-c', '--config', dest='config',
        default='conf/canary_config.py', 
        help='path to configuration file')

    (options, args) = parser.parse_args()

    context = canary.context.Context()
    cursor = context.get_cursor()

    si = canary.search.SearchIndex(context)
    writer = context.get_search_index_writer(True)
    # Tweak for better performance
    writer.mergeFactor = 100
    writer.minMergeDocs = 100
    
    # Index all records
    record_count = 0
    try:
        # Index everything, now
        cursor.execute("""
            SELECT uid
            FROM queued_records
            ORDER BY uid
            """)
        rows = cursor.fetchall()
        for row in rows:
            uid = int(row[0])
            print 'loading record %s' % uid
            record = QueuedRecord(context, uid)
            #print 'indexing record %s' % uid
            si.index_record(record, writer)
            #print 'indexed record %s' % uid
            record_count += 1
    except:
        import traceback
        print traceback.print_exc()


    writer.optimize()
    writer.close()
    cursor.close()
    
    print 'Total indexed records:', record_count
