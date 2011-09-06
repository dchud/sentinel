#!/usr/bin/env python

import os

from quixote import enable_ptl
from scgi.quixote_handler import QuixoteHandler, main

enable_ptl()
os.environ['GCJ_PROPERTIES'] = "disableLuceneLocks=true"

from canary.qx_defs import CanaryPublisher


class CanaryHandler (QuixoteHandler):

    publisher_class = CanaryPublisher
    root_namespace = "canary.ui"
    prefix = ""


if __name__ == '__main__':
    enable_ptl()
    main(CanaryHandler)
