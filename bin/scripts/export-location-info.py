#!/usr/bin/env python

# Export a basic delimited summary of curated study
# location information, suitable for importing into access
# for query by ArcGIS.
#
# $Id$


import canary.context
from canary.gazeteer import Feature
from canary.loader import QueuedRecord
from canary.study import Study



if __name__ == '__main__':
    out_file = open('/tmp/export-location-info.txt', 'w')
    all = {}
    context = canary.context.Context()
    for i in range(4000):
        try:
            rec = QueuedRecord(context, i)

            if not rec \
                or not rec.status == rec.STATUS_CURATED:
                raise 'ValueError'

            study = Study(context, rec.study_id)
            if not study.status == study.STATUS_TYPES['curated'] \
                or not (study.article_type >= study.ARTICLE_TYPES['traditional'] \
                    and study.article_type <= study.ARTICLE_TYPES['curated']):
                raise 'ValueError'

            for loc in study.locations:
                out = []
                out.extend((loc.uid, loc.study_id, loc.feature_id))
                feature = Feature(uid=loc.feature_id)
                feature.load(context)
                out.extend((feature.latitude, feature.longitude,
                    feature.name, feature.feature_type, feature.country_code))

        except:
            continue

    out_file.write('\t'.join([str(s) for s in out]) + '\n')

    out_file.close()
