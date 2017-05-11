#!/bin/sh

/canary/sentinel/bin/scgi_handler.py -p 4001 -l /canary/sentinel/scgi.log -u root -m 10 -P /var/run/canary.pid
