#!/usr/bin/env python


# Update canary zodb instance old-named user object class.
#
# To include at least the following:
#
# - sentineltestsite.qx_defs.MyDulcineaUser becomes canary.qx_defs.MyDulcineaUser
#
# $Id$

from optparse import OptionParser

from dulcinea.database import ObjectDatabase, get_transaction

import canary 
from canary.qx_defs import MyConfig, MyDulcineaUser

sentineltestsite = canary


if __name__ == '__main__':
    usage = "usage: %prog [options]"
    parser = OptionParser(usage)
    parser.add_option('-d', '--database', dest='database',
        default='file:data/canary_db',
        help='path to database file', metavar='FILE')
    parser.add_option('-c', '--config', dest='config',
        default='conf/canary_config.py', 
        help='path to configuration file')

    (options, args) = parser.parse_args()

    config = MyConfig()
    config.read_file(options.config)
    config.zodb_connection_string = 'file:%s' % options.database
    zodb = ObjectDatabase()
    sessions = zodb.open(config.zodb_connection_string)
    zodb_root = zodb.get_root()
    user_db = zodb_root['user_db']

    try:
        for user in user_db.get_users():
            print 'Updating user', user.get_id()
            user._p_changed = True
        get_transaction().commit()
    except:
        import traceback
        print traceback.print_exc()
        print 'Last user:', user.get_id()
        get_transaction().abort()
