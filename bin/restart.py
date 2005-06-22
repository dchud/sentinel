#!/usr/bin/env python2.3

"""
bin/restart.py

Find the current scgi process id and kill that pid's child processes
as a "gentle" restart for SCGI.  Should be smart enough only to kill
children of the local scgi_handler running at pid named in './scgi.pid'.

for an explanation of how it works in SCGI see 

  http://mail.mems-exchange.org/pipermail/quixote-users/2003-February/001243.html

save_popen() taken from a python cookbook recipe comment at

  http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52296
  
  
$Id$
"""


import os, signal, tempfile

def save_popen (command):
    """This is a deadlock save version of popen2 (no stdin), that returns
    an object with errorlevel,out, and err"""
    
    outfile=tempfile.mktemp()
    errfile=tempfile.mktemp()
    errorlevel=os.system("( %s ) > %s 2> %s" %
        (command,outfile,errfile)) >> 8
    out=open(outfile,"r").read()
    err=open(errfile,"r").read()
    os.remove(outfile)
    os.remove(errfile)
    return out.strip()


scgi_pid = open('scgi.pid').read().strip()

# 'grep python' because the first grep might show up in the list
pid_set = save_popen("""ps -ef | grep scgi_handler | grep python | awk '{print $2, $3}'""")
pid_lines = pid_set.split('\n')

for line in pid_lines:
    pid, ppid = line.split(' ')
    if pid == scgi_pid:
        print 'Finding children for pid', pid
    elif ppid == scgi_pid:
        print 'Killing child pid', pid
        os.kill(int(pid), signal.SIGHUP)
