#!/usr/bin/env python

# $Id$

from quixote import enable_ptl
from scgi.quixote_handler import QuixoteHandler, main

enable_ptl()

from canary.qx_defs import MySessionPublisher



class MyHandler (QuixoteHandler):

    publisher_class = MySessionPublisher
    root_namespace = "canary.ui"
    prefix = ""


if __name__ == '__main__':
    enable_ptl()
    main(MyHandler)
