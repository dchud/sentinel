#!/usr/bin/env python

from canary.cmdline import CommandLine
from canary.context import Context, CanaryConfig
from canary.report import CuratorActivity

cmdline = CommandLine()
cmdline.add_option( '--html', dest='html', action='store_true', default=False, 
    help='output as html' )
cmdline.parse_args()

context = cmdline.context()
report = CuratorActivity(context)

if cmdline.html:
    print report.html()
else:
    print report.text()

