# misc useful utilities

from log4py import Logger
import re


class MyLogger (Logger):
    """
    Convenience wrapper around log4py.Logger to avoid needing to
    sprinkle str() calls around whenever common logger funcs are called
    inside of PTL templates.
    FIXME:  utterly incomplete, and these calls are actually (self, *msgs)
    """

    # Note:  we are not able to tweak the init params for Logger here.
    def __init__ (self):
        Logger.__init__(self)

    def debug (self, msg):
        Logger.debug(self, str(msg))

    def warn (self, msg):
        Logger.warn(self, str(msg))

    def error (self, msg):
        Logger.error(self, str(msg))

    def info (self, msg):
        Logger.info(self, str(msg))


class DTable:
    
    def set (self, field, value):
        """
        Dynamic field setting for simpler database lookups
        """
        if value == None:
            setattr(self, str(field), str(''))
        else:
            setattr(self, str(field), value)
       
       
    def get_new_uid (self, cursor):
        
        try:
            cursor.execute('SELECT LAST_INSERT_ID() AS new_uid')
            row = cursor.fetchone()
            new_uid = row[0]
        except:
            new_uid = -1
        return new_uid


def do_query(cursor, query):
    if cursor == None:
        return None
    cursor.execute(query)
    return cursor.fetchall()


def read_file (file):
    contents = open(file).read()
    return contents


def get_title_from_path (path):
    """
    Take a path, probably for a MyStaticFile, in the form of
    'sample_path_name', and return "Sample Path Name", suitable
    for passing to header as the page title.
    """
    underscore_to_space = re.compile('_')
    new_path = underscore_to_space.sub(' ', path)
    from string import capwords
    return capwords(new_path)


# derived from ASPN cookbook recipe (and comments) at:
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66439
def is_valid_email (address):
    re_email = re.compile('^[^\s]+@[^\s]+\.[^\s]{2,3}$')
    if re_email.search(address) == None:
        return False
    else:
        return True

def is_valid_password (passwd):
    if passwd == None:
        return False
    elif len(passwd) < 4:
        return False
    else:
        return True


def send_email (from_addr, to_addr, subject='', body='', server='localhost'):
    import smtplib
    if not subject == '':
        subject = 'Subject: %s' % subject

    try:
        server = smtplib.SMTP(server)
        server.set_debuglevel(0)
        server.sendmail(from_addr, to_addr, '%s\n%s\n' % (subject, body))
        server.quit()
    except:
        # FIXME: something more graceful please.
        return


# simple self-tests
if __name__ == '__main__':
    print 't: get_title_from_path("foo_bar_baz")'
    print get_title_from_path("foo_bar_baz")