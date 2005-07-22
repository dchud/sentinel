#!/usr/bin/env python2.3

# Fix one or all canary records by replacing all medline metadata
# with results of a fresh pubmed query.
#
# $Id$

from optparse import OptionParser
import pprint
import time

import canary.context
from canary.loader import Parser, QueuedRecord
from canary.search import PubmedSearch
from canary.study import Study


if __name__ == '__main__':
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    parser.add_option('-i', '--canary-identifier',
        dest='canary_id', default=0,
        help='specific canary id to fetch')
    parser.add_option('-c', '--config', 
        dest='config', default='conf/canary_config.py',
        help='path to configuration file')
    parser.add_option('-u', '--update', 
        action='store_true', dest='update', default=False,
        help='save updated data to the database')

    (options, args) = parser.parse_args()

    context = canary.context.Context()
    cursor = context.get_cursor()

    # get a complete mapping
    source_catalog = context.get_source_catalog()
    complete_mapping = source_catalog.get_complete_mapping()
    # pubmed-medline is source 13 
    pubmed_source = source_catalog.get_source(13)
    pubmed_search = PubmedSearch()

    if options.canary_id:
        rows = [[options.canary_id,],]
    else:
        # get all active queuedrecord ids
        cursor.execute("""
            SELECT uid
            FROM queued_records
            """)
        rows = cursor.fetchall()

    parser = Parser(pubmed_source)
    for row in rows:
        qr = QueuedRecord(context, row[0])
        print 'Fetching pubmed data for ui %s' % qr.unique_identifier
        pm_data = pubmed_search.fetch(qr.unique_identifier)
        fetched_records = parser.parse(mapped_terms=complete_mapping,
            is_email=False, data=pm_data)

        if len(fetched_records) != 1:
            print 'Fetch for %s (%s) found %s records, ignoring' % (ui,
                qr.uid, len(fetched_records))
        else:
            print 'Orig metadata:', qr.metadata
            fetched_rec = fetched_records[0]
            print 'Fetched metadata:', fetched_rec.metadata
            fetched_rec_metadata = fetched_rec.get_mapped_metadata(complete_mapping)
            print 'Fetched metadata, mapped:', fetched_rec_metadata
            if options.update:
                print 'Updating.'
                qr.metadata = fetched_rec.metadata
                qr.save(context)

        # It is a condition of Entrez eutilities to wait 3s bet. requests
        time.sleep(3)
