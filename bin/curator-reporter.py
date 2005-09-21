#!/usr/bin/env python

"""
curator-reporter.python

Simple text report engine; generates a report for a single curator 
for a set of curated records by id name.

$Id$
"""

import dtuple
import MySQLdb
import os
import sys
from optparse import OptionParser

from canary.gazeteer import Feature
from canary.study import Study


def render_study (cursor, study, pmid):
    print 'canaryid: %s  pmid: %s  curator: %s' % \
        (study.uid, pmid, study.curator_user_id)
    bools = []
    for bool_attr in [
        'exposures',
        'outcomes', 
        'relationships',
        'interspecies',
        'exposure_linkage',
        'outcome_linkage',
        'genomic',
        ]:
        if getattr(study, 'has_%s' % bool_attr):
            print '\t%s:\tX' % bool_attr
        else:
            print '\t%s:\t-' % bool_attr
    
    if len(study.exposures) > 0:
        print 'Exposures:'
        exps = [exp.term for exp in study.exposures]
        exps.sort()
        for exp in exps:
            print '\t' + exp

    if len(study.outcomes) > 0:
        print 'Outcomes:'
        outs = [out.term for out in study.outcomes]
        outs.sort()
        for out in outs:
            print '\t' + out
    
    if len(study.species) > 0:
        print 'Species:'
        specs = [sp.term for sp in study.species]
        specs.sort()
        for sp in specs:
            print '\t' + sp
     
    if len(study.locations) > 0:
        print 'Locations:'
        features = []
        for loc in study.locations:
            feature = Feature(loc.feature_id)
            feature.load(cursor)
            features.append(feature)
        feats = [f.name for f in features]
        feats.sort()
        for f in feats:
            print '\t' + f
    
    if len(study.methodologies) > 0:
        
        print 'Methodologies:'
        for meth in study.methodologies:
            study_type = meth.get_study_type(True)
            if study_type == 'experimental' \
                and meth.is_mesocosm:
                study_type = 'experimental (mesocosm)'
            elif study_type == 'cohort' \
                and meth.is_enclosure:
                study_type = 'cohort (enclosure)'
                
            print ' ~ '.join([
                'study_type',
                'N',
                'routes',
                'sampling',
                'controls',
                'timing',
                ])
                
            print ' ~ '.join([
                study_type, 
                meth.sample_size, 
                ', '.join(meth.get_routes(True)),
                meth.get_sampling(True), 
                meth.get_controls(True),
                meth.get_timing(True),
                ])
    
    print '\n -=-=-=-=- \n'



if __name__ == '__main__':

    usage = "usage: %s [options] [CURATOR]" % os.path.basename(sys.argv[0])
    parser = OptionParser()
    parser.add_option("-d", "--database",
        action="store", dest="database", default="dev",
        help="database name to query")
    parser.add_option("-f", "--file", 
        action="store", dest="filename", default="",
        help="read PMID list from FILE", metavar="FILE")
    parser.add_option("-o", "--outfile",
        action="store", dest="out_filename", default="out.txt",
        help="write PMID to OUTFILE")
    parser.add_option("-q", "--quiet",
        action="store_false", dest="verbose", default=True,
        help="don't print status messages to stdout")
    parser.add_option("-v", "--verbose",
        action="store_true", dest="verbose", default=False,
        help="print status messages to stdout")

    (options, args) = parser.parse_args()
    
    if len(args) < 1:
        if not options.filename:
            print usage 
            sys.exit()
    else:
        curator_id = args[0] 
    
    studies = []
    
    conn = MySQLdb.connect(db='canary-%s' % options.database, 
        user='dlc33', passwd='floogy')
    cursor = conn.cursor()
    

    if options.filename:
        # use pmid_list so pmids can be sorted for easier side-by-side comparison
        pmid_list = []
        for line in open(options.filename):
            pmid_list.append(int(line.strip()))
            pmid_list.sort()

        for pmid in pmid_list:
            cursor.execute("""
                SELECT studies.uid AS study_id, queued_records.uid AS queued_record_id
                FROM queued_records, studies
                WHERE queued_records.study_id = studies.uid
                AND studies.status = 2
                AND queued_records.unique_identifier = %s
                """, pmid)
            fields = [d[0] for d in cursor.description]
            desc = dtuple.TupleDescriptor([[f] for f in fields])
            row = cursor.fetchone()
            if row:
                row = dtuple.DatabaseTuple(desc, row)
                study = Study(row['study_id'])
                study.load(cursor)
                studies.append((study, pmid))
    
    else:
        # sort by unique_identifier for easier side-by-side comparison
        cursor.execute("""
            SELECT studies.uid AS study_id, queued_records.uid AS queued_record_id,
                queued_records.unique_identifier
            FROM studies, queued_records
            WHERE studies.uid = queued_records.study_id
            AND studies.status = 2
            AND studies.curator_user_id = %s
            ORDER BY ABS(queued_records.unique_identifier)
            """, curator_id)
        
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        for row in rows:
            row = dtuple.DatabaseTuple(desc, row)
            study = Study(row['study_id'])
            pmid = row['unique_identifier']
            study.load(cursor)
            studies.append((study, pmid))
    
    out_file = open(options.out_filename, 'w')
    for study, ui in studies:
        out_file.write(str(ui) + '\n')
        render_study(cursor, study, ui)

    cursor.close()
    conn.close()
    
    out_file.close()
