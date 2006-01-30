# $Id$

import logging
import random
import sha

import canary
from canary import dtuple
from canary.utils import DTable

logger = logging.getLogger('canary.user')


# Copied from dulcinea.user
def hash_password (password):
    """Apply a one way hash function to a password and return the result."""
    return sha.new(password).hexdigest()

def get_user_by_id (context, id):
    """     
    Find user for existing user id.
    """
    if id == None:
        return None
    user = User(id=id)
    try:
        user.load(context)
        return user
    except 'InvalidUserId', e:
        context.logger.error('Could not load user %s', id)
        return None


def get_user_by_email (context, email):
    """
    Find user for existing account by email address.
    """
    if email == None:
        return None
    user = User(email=email)
    try:
        user.load(context)
        return user
    except 'InvalidUserId', e:
        context.logger.error('Could not load user %s', email)
        return None
    

def get_user_by_uid (context, uid):
    """     
    Find user for existing uid.
    """
    if uid == None:
        return None
    user = User(uid=uid)
    try:
        user.load(context)
        return user
    except Exception, e:
        context.logger.error('Could not load user %s (%s)', uid, e)
        return None
        

def get_user_by_yale_netid (context, netid):
    """
    Find user for existing Yale netid.
    """
    if netid == None:
        return None
    cursor = context.get_cursor()
    cursor.execute("""
        SELECT id
        FROM users
        WHERE netid = %s
        """, netid)
    rows = cursor.fetchall()
    if not len(rows) == 1:
        return None
    return get_user_by_id(context, rows[0][0])
    

def get_users (context):
    """ Return all users.  """
    users = {}
    cursor = context.get_cursor()
    cursor.execute("""
        SELECT * 
        FROM users
        """)
    fields = [d[0] for d in cursor.description]
    desc = dtuple.TupleDescriptor([[f] for f in fields])
    rows = cursor.fetchall()
    for row in rows:
        user = User()
        row = dtuple.DatabaseTuple(desc, row)
        for field in fields:
            user.set(field, row[field])
        users[user.id] = user
    return users


class User (DTable):

    TABLE_NAME = 'users'

    def __init__ (self, uid=-1, id='', name='', email='', netid=''):
        self.uid = uid
        self.id = id
        self.is_active = int(True)
        self.is_admin = int(False)
        self.is_editor = int(False)
        self.name = name
        self.passwd = ''
        self.is_assistant = int(False)
        self.email = email
        self.netid = ''
        self.token = ''
        self.wants_news = int(False)
        self.searches = []
        # key=record.uid, value=Userrecord
        self.records = {}
        # key=set.uid, value=UserRecord
        self.record_set_map = {}
        self.sets = []
        self.logger = logging.getLogger(str(self.__class__))

    def __str__ (self):
        return self.id or "*no id*"

    # -- Password methods ----------------------------------------------
    # Taken nearly verbatim from dulcinea.user
    
    def set_password (self, new_password):
        """Set the user's password to 'new_password'."""
        self.passwd = hash_password(new_password)


    def valid_password (self, password):
        """Return true if the provided password is correct."""
        if not password:
            return False
        return self.passwd == hash_password(password)

    def unverify (self):
        self.is_active = int(False)
        self.token = str(random.randrange(216688554,753377224))
    
    def verify (self, token):
        if token == self.token:
            self.is_active = int(True)
            self.token = ''
            return True
        return False

    def get_id (self):
        """Compatibility method for quixote and old canary code."""
        return self.id

    def load (self, context):
            
        cursor = context.get_cursor()
            
        if self.id:
            cursor.execute("""
                SELECT * 
                FROM users
                WHERE id LIKE %s
                """, (self.id))
            fields = [d[0] for d in cursor.description]
            desc = dtuple.TupleDescriptor([[f] for f in fields])
            row = cursor.fetchone()
            if row:
                row = dtuple.DatabaseTuple(desc, row)
                for field in fields:
                    self.set(field, row[field])
            else:
                self.logger.debug('No user "%s"', self.id)
                raise 'InvalidUserId'
        elif self.email:
            cursor.execute("""
                SELECT * 
                FROM users
                WHERE email LIKE %s
                """, (self.email))
            fields = [d[0] for d in cursor.description]
            desc = dtuple.TupleDescriptor([[f] for f in fields])
            row = cursor.fetchone()
            if row:
                row = dtuple.DatabaseTuple(desc, row)
                for field in fields:
                    self.set(field, row[field])
            else:
                self.logger.debug('No user "%s"', self.email)
                raise 'InvalidUserId'
        
        # Load records 
        cursor.execute("""
            SELECT * 
            FROM user_records
            WHERE user_id = %s
            ORDER BY uid
            """, self.uid)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        for row in cursor.fetchall():
            row = dtuple.DatabaseTuple(desc, row)
            self.records[row['record_id']] = UserRecord(uid=row['uid'], 
                user_id=self.uid, record_id=row['record_id'], notes=row['notes'])
                
        # Load sets
        cursor.execute("""
            SELECT uid
            FROM user_sets
            WHERE user_id = %s
            ORDER BY LOWER(name)
            """, self.uid)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        set_ids = []
        for row in cursor.fetchall():
            row = dtuple.DatabaseTuple(desc, row)
            set_ids.append(row['uid'])
        try:
            set_map = context.cache_get_multi(list('%s:%s' % (UserSet.CACHE_KEY, id) for id in set_ids))
            self.sets.extend(list(set_map['%s:%s' % (UserSet.CACHE_KEY, id)] for id in set_ids))
        except:
            for id in set_ids:
                self.sets.append(UserSet(context, id))

        # Load record->set assignments
        for set in self.sets:
            cursor.execute("""
                SELECT record_id
                FROM user_set_records
                WHERE user_set_id = %s
                ORDER BY uid
                """, set.uid)
            fields = [d[0] for d in cursor.description]
            desc = dtuple.TupleDescriptor([[f] for f in fields])
            for row in cursor.fetchall():
                row = dtuple.DatabaseTuple(desc, row)
                # Save the id in the set's in-memory list of records
                set.records.append(row['record_id'])
                # Get the whole UserRecord
                rec = self.records[row['record_id']]
                # Save the UserRecord in the set map
                try:
                    self.record_set_map[set.uid].append(rec)
                except:
                    self.record_set_map[set.uid] = [rec]
                    
        
    def save (self, context):
        cursor = context.get_cursor()
        try:
            if self.uid == -1:
                insert_phrase = 'INSERT INTO %s' % self.TABLE_NAME
                cursor.execute(insert_phrase + """
                    (uid, id, name, passwd, email,
                    is_active, is_admin, 
                    is_editor, is_assistant, netid,
                    token, wants_news)
                    VALUES 
                    (NULL, %s, %s, %s, %s,
                    %s, %s, 
                    %s, %s, %s,
                    %s, %s)
                    """, (self.id, self.name, self.passwd, self.email,
                    int(self.is_active), int(self.is_admin), 
                    int(self.is_editor), int(self.is_assistant), self.netid,
                    self.token, self.wants_news)
                    )
                self.uid = self.get_new_uid(context)
                self.logger.info('User %s created with uid %s', self.id, self.uid)
            else:
                update_phrase = 'UPDATE %s ' % self.TABLE_NAME
                cursor.execute(update_phrase + """
                    SET id=%s, passwd=%s, name=%s, email=%s, 
                    is_active=%s, is_admin=%s, 
                    is_editor=%s, is_assistant=%s, netid=%s,
                    token=%s, wants_news=%s
                    WHERE uid = %s
                    """, (self.id, self.passwd, self.name, self.email, 
                    int(self.is_active), int(self.is_admin), 
                    int(self.is_editor), int(self.is_assistant), self.netid,
                    self.token, int(self.wants_news),
                    self.uid)
                    )
                self.logger.info('User %s updated', self.id)
        except Exception, e:
            self.logger.error(e)
        

    def delete (self, context):
        """ Delete this user from the database."""
       
        cursor = context.get_cursor()
        try:
            if self.uid >= 0:
                cursor.execute("""
                    DELETE FROM users 
                    WHERE uid = %s
                    """, self.uid)
        except Exception, e:
            self.logger.error(e)
            
        
        

class UserSet (canary.context.Cacheable, DTable):
    """
    A group of records saved by some user.  UserRecords can be in zero-to-many
    UserSets.
    
    When a UserRecord is deleted, all references to that record in UserSets are
    deleted.
    
    When a UserSet is deleted, the user might keep the UserRecord, but the set
    and all its assignments are deleted.
    """
    
    TABLE_NAME = 'user_sets'
    
    CACHE_KEY = 'userset'
    
    CACHE_CHECK_FIELD = 'name'
    
    load = canary.context.Cacheable.load

    def __init__ (self, context=None, uid=-1, user_id=-1, name='', is_locked=False):
        try:
            if getattr(self, self.CACHE_CHECK_FIELD):
                return
        except AttributeError:
            pass
        self.uid = uid
        self.user_id = user_id
        self.name = name
        self.is_locked = is_locked
        # in-memory only: a list of record_ids
        self.records = []
        self.shares = []
    
    def add (self, context, user_record):
        """Add a record to this set."""
        cursor = context.get_cursor()
        try:
            cursor.execute("""
                INSERT INTO user_set_records
                (uid, user_set_id, record_id)
                VALUES (NULL, %s, %s)
                """, (self.uid, user_record.record_id))
            if context.config.use_cache:
                context.cache_delete('%s:%s' % (self.CACHE_KEY, self.uid))
        except Exception, e:
            context.logger.error(e)
            
    def remove (self, context, user_record):
        """Remove a record from this set."""
        cursor = context.get_cursor()
        try:
            cursor.execute("""
                DELETE FROM user_set_records
                WHERE user_set_id = %s
                AND record_id = %s
                """, (self.uid, user_record.record_id))
            if context.config.use_cache:
                context.cache_delete('%s:%s' % (self.CACHE_KEY, self.uid))
        except Exception, e:
            context.logger.error(e)
        
    def save (self, context):
        cursor = context.get_cursor()
        try:
            if self.uid == -1:
                insert_phrase = 'INSERT INTO %s' % self.TABLE_NAME
                cursor.execute(insert_phrase + """
                    (uid, user_id, name, is_locked)
                    VALUES 
                    (NULL, %s, %s, %s)
                    """, (self.user_id, self.name, int(self.is_locked))
                    )
                self.uid = self.get_new_uid(context)
                context.logger.info('UserSet "%s" created with uid %s', self.name, self.uid)
            else:
                update_phrase = 'UPDATE %s ' % self.TABLE_NAME
                cursor.execute(update_phrase + """
                    SET name=%s, is_locked=%s
                    WHERE uid = %s
                    """, (self.name, int(self.is_locked),
                    self.uid)
                    )
                context.logger.info('UserSet %s updated', self.uid)
                
            if context.config.use_cache:
                context.cache_set('%s:%s' % (self.CACHE_KEY, self.uid), self)
        except Exception, e:
            context.logger.error(e)

    def delete (self, context):
        cursor = context.get_cursor()
        try:
            # First delete all records assigned to this set
            cursor.execute("""
                DELETE FROM user_set_records
                WHERE user_set_id = %s
                """, self.uid)
            
            # Then remove the set
            delete_phrase = 'DELETE FROM %s' % self.TABLE_NAME
            cursor.execute(delete_phrase + """
                WHERE uid = %s
                """, self.uid)
            DTable.delete(self, context)
            if context.config.use_cache:
                context.cache_delete('%s:%s' % (self.CACHE_KEY, self.uid))
        except Exception, e:
            context.logger.error(e)


class UserRecord (canary.context.Cacheable, DTable):
    
    TABLE_NAME = 'user_records'
    
    CACHE_KEY = 'userrecord'
    
    CACHE_CHECK_FIELD = 'name'
    
    load = canary.context.Cacheable.load
    
    def __init__ (self, context=None, uid=-1, user_id=-1, record_id=-1, 
        notes='', date_created=None):
        try:
            if self.user_id:
                return
        except AttributeError:
            pass
        self.uid = uid
        self.user_id = user_id
        self.record_id = record_id
        self.notes = notes
        self.date_created = date_created
        self.sets = []
        
    def save (self, context):
        cursor = context.get_cursor()
        try:
            if self.uid == -1:
                insert_phrase = 'INSERT INTO %s' % self.TABLE_NAME
                cursor.execute(insert_phrase + """
                    (uid, user_id, record_id, notes, date_created)
                    VALUES 
                    (NULL, %s, %s, %s, NOW())
                    """, (self.user_id, self.record_id, self.notes)
                    )
                self.uid = self.get_new_uid(context)
                context.logger.info('UserRecord %s created with uid %s', self.record_id, self.uid)
            else:
                # NOTE: only updates notes field!
                update_phrase = 'UPDATE %s ' % self.TABLE_NAME
                cursor.execute(update_phrase + """
                    SET notes=%s
                    WHERE uid = %s
                    """, (self.notes,
                    self.uid)
                    )
                context.logger.info('UserRecord %s updated', self.uid)
        except Exception, e:
            context.logger.error(e)

    def delete (self, context):
        cursor = context.get_cursor();
        try:
            # First delete all sets to which this record was assigned
            cursor.execute("""
                DELETE FROM user_set_records
                WHERE record_id = %s
                """, self.record_id)
            
            # Then delete the record itself
            DTable.delete(self, context)
            if context.config.use_cache:
                context.cache_delete('%s:%s' % (self.CACHE_KEY, self.uid))
        except Exception, e:
            context.logger.error(e)
        
        
class UserSearch (canary.context.Cacheable, DTable):
    
    TABLE_NAME = 'user_searches'

    CACHE_KEY = 'usersearch'

    def __init__ (self, uid=-1, user_id=-1, query=''):
        self.uid = uid
        self.user_id = user_id
        self.query = query
        self.email_frequency = 'Never'
        self.date_created = None
        self.date_viewed = None
