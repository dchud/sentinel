# misc useful utilities
# $Id$

import Image, ImageDraw
from log4py import Logger
import os
import re
import time

import canary.context


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
    """
    Convenience class for rdbms-persisted object types.  Allows simple
    loading of data for single-valued fields using set() and for multi-valued
    fields using append().
    """
    
    def set (self, field, value):
        """
        Dynamic field setting for simpler database lookups
        """
        if value == None:
            setattr(self, str(field), str(''))
        else:
            setattr(self, str(field), value)
       
    #def append (self, field, value):
    #    list_attr = getattr(self, str(field))
    #    if not value in list_attr:
    #        list_attr.append(value)
    
       
    def get_new_uid (self, context):
        cursor = context.get_cursor()
        try:
            cursor.execute('SELECT LAST_INSERT_ID() AS new_uid')
            row = cursor.fetchone()
            new_uid = int(row[0])
        except:
            new_uid = -1
        context.close_cursor(cursor)
        return new_uid
        


def read_file (file):
    contents = open(file).read()
    return contents


def get_title_from_path (path):
    """
    Take a path, probably for a MyStaticFile, in the form of
    'sample_path_name', and return "Sample Path Name", suitable
    for passing to header as the page title.
    
    Remove the leading "about/" as needed.
    """
    underscore_to_space = re.compile('_')
    if path.startswith('about/'):
        path = path[len('about/'):]
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

def render_capitalized (term):
    stop_words = ['of', 'the']
    old_terms = str(term).split(' ')
    new_terms = []
    for t in term.split(' '):
        if t in stop_words:
            new_terms.append(t)
        else:
            new_terms.append(t.lower().capitalize())
    return ' '.join(new_terms)


def fix_double_quotes (s):
    """Replace html entity "&quot;" with '"'."""
    s = str(s)
    s2 = s.replace('&quot;', '"')
    return s2
    

def make_sparkline (context, d, context_years=()):
    """
    For an arbitrary dictionary, make a simple sparkline with keys
    on the x-axis and values on the y-axis.
    """
    config = context.config
    max_val = float(max(d.values())) or 1
    keys = d.keys()
    keys.sort()
    vals = []
    im = Image.new("RGB", ((len(d)+2)*3, 20), 'white')
    draw = ImageDraw.Draw(im)
    if context_years:
        context_min_year, context_max_year = context_years
        min_year = min(keys)
        draw.rectangle([((context_min_year-min_year)*3)-3, 0, 
            ((context_max_year-min_year)*3)+3, 120], 
            outline='#dddddd', fill='#eeeeee')
        
    for key in keys:
        val = d[key]
        vals.append(18 - int(15*(val/max_val)))
        if val > 0:
            x_center = keys.index(key) * 3
            y_center = 18 - int(15*(val/max_val))
            draw.ellipse([x_center-2, y_center-2, x_center+2, y_center+2],
                outline='#A7C0F2', fill='#ABC6F8')
    coords = zip([x*3 for x in range(len(d))], vals)
    draw.line(coords, fill="#888888")
    del draw

    file_name = '%s.png' % time.time()
    im.save('%s/%s' % (config.temp_image_dir, file_name))
    return file_name


def clean_temp_image_dir (context):
    """
    Walk through the temp_image_dir and eliminate anything
    older than an hour.  Assumes files are named in time_millis,
    with dot+three extensions, e.g. '1115775081.08.png'.
    """
    config = context.config
    now = int(time.time())
    interval = 60 * 60
    for root, dirs, files in os.walk(config.temp_image_dir):
        for file in files:
            file_time = int(file[:file.index('.')])
            if now - file_time >= interval:
                os.remove('%s/%s' % (config.temp_image_dir, file))
