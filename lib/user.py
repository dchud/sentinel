import sha

from canary import dtuple
from canary.utils import DTable


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
    except:
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
    except:
        return None

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
    context.close_cursor(cursor)
    return users


class User (DTable):

    TABLE_NAME = 'users'

    def __init__ (self, uid=-1, id='', name='', email=''):
        self.uid = uid
        self.id = id
        self.is_active = int(True)
        self.is_admin = int(False)
        self.is_editor = int(False)
        self.name = name
        self.passwd = ''
        self.is_assistant = int(False)
        self.email = email
        # FIXME: signups not yet implemented
        #self.token = ''

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
                raise 'InvalidUserError', 'No user "%s"' % self.id
        context.close_cursor(cursor)
        
        
    def save (self, context):
        
        cursor = context.get_cursor()
        try:
            if self.uid == -1:
                insert_phrase = 'INSERT INTO %s' % self.TABLE_NAME
                cursor.execute(insert_phrase + """
                    (uid, id, name, passwd, email,
                    is_active, is_admin, 
                    is_editor, is_assistant)
                    VALUES 
                    (NULL, %s, %s, %s, %s,
                    %s, %s, 
                    %s, %s)
                    """, (self.id, self.name, self.passwd, self.email,
                    int(self.is_active), int(self.is_admin), 
                    int(self.is_editor), int(self.is_assistant))
                    )
                self.uid = self.get_new_uid(context)
                print 'User %s created with uid %s' % (self.id, self.uid)
            else:
                update_phrase = 'UPDATE %s ' % self.TABLE_NAME
                cursor.execute(update_phrase + """
                    SET id=%s, passwd=%s, name=%s, email=%s, 
                    is_active=%s, is_admin=%s, 
                    is_editor=%s, is_assistant=%s
                    WHERE uid = %s
                    """, (self.id, self.passwd, self.name, self.email, 
                    int(self.is_active), int(self.is_admin), 
                    int(self.is_editor), int(self.is_assistant),
                    self.uid)
                    )
                print 'User %s updated' % self.id
            #if context.config.use_cache:
            #    full_cache_key = '%s:%s' % (self.CACHE_KEY, self.id)
            #    context.cache_set(full_cache_key, self)
        except:
            import traceback
            print traceback.print_exc()
        context.close_cursor(cursor)


    def delete (self, context):
        """ Delete this user from the database."""
       
        cursor = context.get_cursor()
        try:
            if self.uid >= 0:
                cursor.execute("""
                    DELETE FROM users 
                    WHERE uid = %s
                    """, self.uid)
        except:
            import traceback
            print traceback.print_exc()
            
        context.close_cursor(cursor)
