# $Id$

import os
import shelve
from time import time
from cPickle import load, dump

import log4py
from mx.DateTime import localtime

from quixote import get_publisher
from quixote.errors import AccessError
from quixote.form2 import Form
from quixote.publish import SessionPublisher
from quixote.session import Session, SessionManager

import canary.context
import canary.user
from canary.utils import MyLogger


# Sql* classes adapted from Titus Brown's examples at:
#
#   http://issola.caltech.edu/~t/transfer/sql_example/session.py
#

class SqlQuixoteSession (object, Session):

    def __init__ (self, request, id):
        Session.__init__(self, request, id)
        self.messages = ''
        self._dirty = 0
        self._form_tokens = []
        #self._Session__access_time = self.__access_time
        #self._Session__creation_time = self.__creation_time
        #self._Session__remote_address = self.remote_address

    def __getattr__ (self, att):
        if att == '_Session__remote_address':
            return self.__remote_address
        elif att == '_Session__creation_time':
            return self.__creation_time

    def add_message (self, msg=''):
        if len(self.messages) == 0:
            self.messages = str(msg)
        else:
            self.messages += '~~%s' % str(msg)
        self._dirty = 1

    def has_messages (self):
        return len(self.messages) > 0

    def clear_messages (self):
        self.messages = ''
        self._dirty = 1

    def set_user (self, user):
        """
        Set the user!  The change in user will be detected by Quixote
        through the 'is_dirty' function and saved accordingly.
        """
        #print 'set user:', user.id
        if not self.user or user.id != self.user.id:
            self._dirty = 1
        self.user = user

    def has_info (self):
        """
        Is this session worthy of storage?
        """
        return self.user

    def is_dirty (self):
        """
        Check to see if this session needs to be stored again, e.g. if
        the user has changed.
        """
        return self._dirty

    def _set_access_time (self, resolution):
        Session._set_access_time(self, resolution)
        self._dirty = 1


class SqlTableMap:
    """
    Intercept dictionary requests and channel them to the SQL database.
    """

    def __init__ (self):
        """
        WAS: Store the database connection.
        """
        self.uncommitted = {}

    def get_conn (self):
        """
        Return the database connection after doing a rollback.
        """
        context = canary.context.Context()
        conn = context.connection
        #try:    
        #    conn.rollback()
        #except NotSupportedError:
        #    pass
        return conn

    def keys (self):
        """
        Get a list of the session IDs in the database.
        """
        context = canary.context.Context()
        cursor = context.get_cursor()
        #context.execute("SELECT uid FROM sessions")
        cursor.execute("SELECT session_id FROM sessions")
        context.close_cursor(cursor)

        return [id for (id,) in cursor.fetchall()]

    def values (self):
        """
        Load all of the sessions in the database.
        """
        context = canary.context.Context()
        cursor = context.get_cursor()
        cursor.execute("""
            SELECT session_id, user_id, remote_addr, creation_time, 
                access_time, messages, form_tokens
            FROM sessions
            """)
        context.close_cursor(cursor)
        return [self._create_from_db(session_id, user_id, addr, c, a, msg, tokens) \
            for (session_id, user_id, addr, c, a, msg, tokens) in cursor.fetchall() ]

    def items (self):
        """
        Get a list of the (key, value) pairs in the database.
        """
        d = {}
        for v in self.values():
            d[v.id] = v

        return d

    def get (self, session_id, default=None):
        """
        Get the given item from the database.
        """

        #cursor = self.get_conn().cursor()
        context = canary.context.Context()
        cursor = context.get_cursor()
        cursor.execute("""
            SELECT session_id, user_id, remote_addr, creation_time, 
                access_time, messages, form_tokens
            FROM sessions
            WHERE session_id=%(session_id)s
            """, {'session_id': session_id})

        assert cursor.rowcount <= 1
        if cursor.rowcount == 1:
            (session_id, user_id, addr, c, a, msg, tokens) = cursor.fetchone()
            context.close_cursor(cursor)
            return self._create_from_db(session_id, user_id, addr, c, a, msg, tokens)
        else:
            context.close_cursor(cursor)
            return default
            
    def __getitem__ (self, session_id):
        """
        Get the given session from the database.
        """
        return self.get(session_id)

    def has_key (self, session_id):
        """
        Does this session exist in the database?
        """
        if self.get(session_id) == None:
            return 0
        return 1

    def __setitem__ (self, session_id, session):
        """
        Store the given session in the database.
        """
        self.uncommitted[session_id] = session

    def __delitem__ (self, session_id):
        """
        Delete the given session from the database.
        """
        if session_id:

            if self.uncommitted.has_key(session_id):
                del self.uncommitted[session_id]

            #print 'Deleting session'
            #conn = self.get_conn()
            #cursor = self.get_conn().cursor()
            #cursor = conn.cursor()
            context = canary.context.Context()
            cursor = context.get_cursor()
            cursor.execute("""
                DELETE FROM sessions 
                WHERE session_id=%(session_id)s
                """, {'session_id': session_id})
            context.close_cursor(cursor)
            #conn.commit()

    def _save_to_db (self, session):
        """
        Save a given session to the database.
        """

        #conn = self.get_conn()
        #cursor = conn.cursor()
        context = canary.context.Context()
        cursor = context.get_cursor()

        # ORIGINAL: save a db-thrash by checking for update possibility
        # instead of the following, which always does an extra delete-
        # and-insert:
        # 
        # don't allow multiple session IDs; this also removes it from
        # the uncommitted dictionary.
        del self[session.id]

        #if self.uncommitted.has_key(session.id):
        #    del self.uncommitted[session.id]

        #if self.has_key(session.id):
        #    cursor.execute("""
        #        UPDATE sessions
        #        SET access_time = %s, messages = %s
        #        WHERE session_id = %s
        #        """, (str(localtime(session.get_access_time())), session.messages,
        #        session.id))
        #else:
        cursor.execute("""
            INSERT INTO sessions
            (session_id, user_id, remote_addr, 
            creation_time, 
            access_time, 
            messages,
            form_tokens)
            VALUES 
            (%s, %s, %s, 
            %s, 
            %s, 
            %s,
            %s)
            """, (session.id, session.user.id, session.get_remote_address(),
               str(localtime(session.get_creation_time())),
               str(localtime(session.get_access_time())),
               str(session.messages),
               str('~~'.join(session._form_tokens))))

        context.close_cursor(cursor)
        #conn.commit()

    def _create_from_db (self, session_id, user_id, addr, create_time, 
        access_time, messages, tokens=[]):
        """
        Create a new session from database data.

        This goes through the new-style object function __new__ rather than
        through the __init__ function.
        """
        session = SqlQuixoteSession.__new__(SqlQuixoteSession)
        session.id = session_id
        session.user = canary.user.get_user_by_id(user_id)
        # FIXME: one '_' to be removed for qx-1.0
        #session.__remote_address = addr
        #session.__creation_time = create_time.ticks()
        #session.__access_time = access_time.ticks()
        session._set_access_time(access_time.ticks())
        session.__remote_address = addr
        session.__creation_time = create_time.ticks()
        session.messages = messages
        session._form_tokens = tokens.split('~~')

        return session

    def _abort_uncommitted (self, session):
        """
        Toss a session without committing any changes.
        """
        if self.uncommitted.has_key(session.id):
            del self.uncommitted[session.id]


class SqlSessionManager (SessionManager):
    """
    A session manager that uses the SqlTableMap to map sessions into an
    SQL database.
    """
    def __init__(self):
        SessionManager.__init__(self, SqlQuixoteSession, SqlTableMap())

    def abort_changes(self, session):
        if session:
            self.sessions._abort_uncommitted(session)

    def commit_changes(self, session):
        if session and session.has_info():
            self.sessions._save_to_db(session)



class CanaryPublisher (SessionPublisher):

    def __init__ (self, *args, **kwargs):

        try:
            self.context = kwargs['context']
            print 'Found context'
        except KeyError:
            self.context = canary.context.Context()
            print 'Started context'
            
        self.config = self.context.config
        
        SessionPublisher.__init__(self, root_namespace='canary.ui', 
            session_mgr=SqlSessionManager(), config=self.config)

        self.setup_logs()



class NotLoggedInError (AccessError):
    """
    To be called when the requested action requires a logged in user.
    Whether that user has access rights or not can only be determined
    after the user actually logs in.
    """
    status_code = 403
    title = "Access denied"
    description = "Authorized access only."




class MyForm (Form):
    """
    Automatically creates a logger instance on any arbitrary Form.
    """
    def __init__ (self, *args, **kwargs):
        Form.__init__(self, *args, **kwargs)
        self.logger = log4py.Logger().get_instance(self)
        context = canary.context.Context()
        context.configure_logger(self.logger)
