#!/bin/sh

./bin/scgi_handler.py -p 4001 -l scgi.log -u nobody -m 1 -P scgi.pid
