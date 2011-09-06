#!/usr/bin/env python

import os
import time

TEMP_DIR = '/canary/temp'
MAX_AGE = 60 * 60 * 24 * 2 # Two days old

count = 0
total = 0
for f in os.listdir(TEMP_DIR):
    filename = TEMP_DIR + '/' + f
    statinfo = os.stat(filename)
    file_age = time.time() - statinfo.st_mtime
    if file_age / MAX_AGE >= 1:
        os.remove(filename)
        count += 1
    total += 1

print 'removed %s/%s file(s)' % (count, total)

