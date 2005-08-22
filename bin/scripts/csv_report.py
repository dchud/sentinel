#!/usr/bin/env python

# Generate a quick CSV report with the format:
#
# canary_uid - title - first_author - source
#   (where " - " is actually "\t")
#   
# ...for an arbitrary set of search terms.
#
# This functionality should be rolled into the public interface.
#
# $Id$

from optparse import OptionParser
import sys

import canary.context
from canary.gazeteer import Feature
from canary.loader import QueuedRecord
from canary.search import SearchIndex
from canary.study import Study

if __name__ == '__main__':
    usage = "usage: %prog [options] TERM1 [TERM2] ..."
    parser = OptionParser(usage)
    parser.add_option('-b', '--boolean', dest='boolean',
        default='OR',
        help='combine search with OR or AND')
    parser.add_option('-c', '--config', dest='config',
        default='conf/canary_config.py', 
        help='path to configuration file')
    parser.add_option('-d', '--database', dest='database',
        default='file:data/canary_db',
        help='path to database file', metavar='FILE')
    parser.add_option('-f', '--field', dest='field',
        default='all',
        help='field to search')
    parser.add_option('-l', '--locations', dest='locations',
        action='store_true', default=False,
        help='report location data only?')

    (options, args) = parser.parse_args()

    config = canary.context.CanaryConfig()
    config.read_file(options.config)
    context = canary.context.Context(config)
    source_catalog = context.get_source_catalog()
    ctm = source_catalog.get_complete_mapping()
    
    if not args:
        print usage
        sys.exit(0)
        
    query_str = options.boolean.join([' "%s" [%s] ' % (term, options.field) for term in args])
    #print query_str.strip()

    search_index = SearchIndex(context)
    hit_list = []
    hits, searcher = search_index.search(query_str)
    for i, doc in hits:
        hit_list.append(doc.get('uid'))
    searcher.close()
        
    output = []
    for id in hit_list:
        rec = QueuedRecord(context, int(id))
        if options.locations:
            study = Study(context, rec.study_id)
            for loc in study.locations:
                out = []
                out.extend((id, loc.uid, loc.study_id, loc.feature_id))
                feature = Feature(uid=loc.feature_id)
                feature.load(context)
                out.extend((feature.latitude, feature.longitude,
                    feature.name, feature.feature_type, feature.country_code))
                output.append('\t'.join([str(v) for v in out]))
        else:
            mm = rec.get_mapped_metadata(ctm)
            if mm['author']:
                first_author = mm['author'][0]
            else:
                first_author = '-'
            output.append('\t'.join((str(rec.uid), rec.title, first_author, rec.source)))
        
    
    print '\n'.join(output)
    
