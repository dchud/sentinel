#!/bin/bash
#
# canary        
#
# chkconfig: 2345 85 15
# description:  Start up canary scgi service

# Source function library.
. /etc/init.d/functions

start()
{
        echo "starting canary"
        su - dlc33 -c 'cd ~/sites/canarydb.med.yale.edu/current; bin/startup.sh &'

        RETVAL=$?
        return $RETVAL
}

stop()
{
        # maybe implement this sometime :)
        echo "stop is not supported"
}


case "$1" in
 start)
        start
        RETVAL=$?
    ;;
 stop)
        stop
        RETVAL=$?
    ;;
 restart)
        echo "please use restart.sh in the canary directory"
        RETVAL=$?
    ;;
 *)
    echo $"Usage: $0 {start|stop}"
    exit 1
    ;;
esac

exit $RETVAL

