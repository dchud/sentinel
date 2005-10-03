#!/usr/bin/env python

# $Id$

from datetime import datetime, timedelta

from canary.cmdline import CommandLine
from canary.context import Context, CanaryConfig
from canary.loader import QueuedRecord
from canary.search import RecordSearcher
from canary.stats import *
from canary.study import Study



if __name__ == '__main__':
    cmdline = CommandLine()
    cmdline.parse_args()
    context = cmdline.context()
    
    collector = StatCollector(context)
    collector.add_handlers(
        CuratorHandler(), 
        ArticleTypeHandler(), 
        ExposureHandler(), 
        OutcomeHandler(), 
        RiskFactorHandler(), 
        SpeciesHandler(), 
        LocationHandler(), 
        MethodologyTypeHandler(),
        )
    
    searcher = RecordSearcher(context)
    records = searcher.search('record-status:%i' % QueuedRecord.STATUS_CURATED)
    
    today = datetime.now()
    one_weeks_records = [rec for rec in records 
        if today - Study(context, rec.study_id).date_modified <= timedelta(7)]
    collector.process(one_weeks_records)
    
    for handler in collector.handlers:
        print handler.__class__, handler.stats
    
