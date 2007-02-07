# misc useful utilities
# $Id$

from cStringIO import StringIO
import Image, ImageDraw
import os
import re
import time
import traceback
import urllib

import elementtree.ElementTree as etree
from elementtree.ElementTree import Element, SubElement
import feedparser

from canary import dtuple

linkages = ['relationships',
    'interspecies',
    'exposure_linkage',
    'outcome_linkage',
    'genomic']
        

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
        return new_uid
    

    def load (self, context):
        cursor = context.get_cursor()
        if self.uid:
            cursor.execute("""SELECT * FROM """ + self.TABLE_NAME +
                """
                WHERE uid LIKE %s
                """, (self.uid))
            fields = [d[0] for d in cursor.description]
            desc = dtuple.TupleDescriptor([[f] for f in fields])
            row = cursor.fetchone()
            if row:
                row = dtuple.DatabaseTuple(desc, row)
                for field in fields:
                    self.set(field, row[field])
            else:
                context.logger.debug('No %s "%s"', self.TABLE_NAME, self.uid)
                print 'No %s "%s"' % (self.TABLE_NAME, self.uid)
                raise 'InvalidId'
                

    def delete (self, context):
        cursor = context.get_cursor()
        try:
            if self.uid >= 0:
                cursor.execute("""DELETE FROM """ + self.TABLE_NAME +
                    """
                    WHERE uid = %s
                    """, self.uid)
        except Exception, e:
            context.logger.error(e)


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

def is_valid_user_id (context, id):
    if not id:
        return False
    if ' ' in id:
        return False
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

    image_name = '%s.png' % time.time()
    image_data_encoded = StringIO()
    im.save(image_data_encoded, 'png')
    # NOTE: Add to cache, but only for 600 seconds (names are time-based, 
    # so we really only need a few milliseconds, but just to be safe).
    # Theoretically, these could be name-bound to the query url, then
    # we'd really be doing caching... instead we cache each time only
    # for responding to a single user request and dispose of the image
    # immediately.
    # 
    # Also, verify the cache set was successful.
    if config.use_cache:
        cache_result = context.cache_set('image:%s' % image_name, 
            image_data_encoded.getvalue(), time=600)
    # Save to file, whether or not it gets cached (#173)
    im.save('%s/%s' % (config.temp_image_dir, image_name))
    return image_name


def make_sideways_e (context, studies):
    """
    For an arbitrary set of studies, make a sideways E
    showing the proportion of the records that have the 
    five standard record linkages.
    """
    config = context.config
    
    #border_color = '#324362'
    border_color = '#888888'
    fg_color = '#A6BFF2'
    bg_color = '#EEEDC0'

    width= 45
    height = 20
    bar_width = 4

    count = len(studies)
    d = {}
    for att in linkages:
        d[att] = 0
        
    for study in studies:
        for att in linkages:
            if getattr(study, 'has_%s' % att):
                d[att] += 1

    im = Image.new("RGB", (width, height), 'white')
    draw = ImageDraw.Draw(im)
    draw.line(((0, height-1), (width, height-1)), fill=border_color)
    for linkage in linkages:
        xoffset = 2  + (linkages.index(linkage) * 9)
        draw.rectangle(((xoffset, height-1), (xoffset+bar_width, 0)),
            outline=border_color, fill=bg_color)
        if count \
            and d[linkage]:
            bar_height = int((height-1) * (float(d[linkage]) / count))
            draw.rectangle((
                (xoffset+1, 18),
                (xoffset+bar_width-1, (18-bar_height+1))
                ),
                fill=fg_color)

    del draw
    image_name = '%s-e.png' % time.time()
    image_data_encoded = StringIO()
    im.save(image_data_encoded, 'png') 
    # NOTE: Add to cache, but only for 600 seconds (names are time-based, 
    # so we really only need a few milliseconds, but just to be safe).
    # Theoretically, these could be name-bound to the query url, then
    # we'd really be doing caching... instead we cache each time only
    # for responding to a single user request and dispose of the image
    # immediately.
    # 
    # Also, verify the cache set was successful.
    if config.use_cache:
        cache_result = context.cache_set('image:%s' % image_name, 
            image_data_encoded.getvalue(), time=600)
    # Save to file, whether or not it gets cached (#173)
    im.save('%s/%s' % (context.config.temp_image_dir, image_name))
    return image_name


def clean_temp_image_dir (context):
    """
    Walk through the temp_image_dir and eliminate anything
    older than an hour.  Assumes files are named in time_millis,
    with dot+three or more extensions, e.g. '1115775081.08.png' and an optional
    prefix, e.g. 'records-1234567890.12.mods.endnote'.
    """
    config = context.config
    now = int(time.time())
    interval = 60 * 60
    re_epoch_time = re.compile(r'[a-z-]*([0-9]{10})\..*')
    for root, dirs, files in os.walk(config.temp_image_dir):
        for file in files:
            match = re_epoch_time.findall(file)
            if match:
                file_time = int(match[0])
                if now - file_time >= interval:
                    os.remove('%s/%s' % (config.temp_image_dir, file))


def parse_feed (url):
    d = feedparser.parse(str(url))
    return d.entries



FORMATS = {'mods': 'mods', 'endnote': 'end', 'bibtex': 'bib', 'ris': 'ris'}
    
def rec2format (context, recs, output_format='mods'):
    try:
        config = context.config
        source_catalog = context.get_source_catalog()
        ctm = source_catalog.get_complete_mapping()
        
        root = Element('modsCollection')
        root.set('xmlns', 'http://www.loc.gov/mods/v3')
        root.set('xmlns:xlink', 'http://www.w3.org/1999/xlink')
        root.set('version', '3.0')
        root.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
        root.set('xsi:schemaLocation',
            'http://www.loc.gov/mods/v3 http://www.loc.gov/standards/mods/v3/mods-3-0.xsd')
        
        for rec in recs:
            try:
                mods = SubElement(root, 'mods')
                mm = rec.get_mapped_metadata(ctm)
                if mm.get('title', ''):
                    titleInfo = SubElement(mods, 'titleInfo')
                    title = SubElement(titleInfo, 'title')
                    title.text = mm['title']
                if mm.get('author', []):
                    for au in mm['author']:
                        name = SubElement(mods, 'name')
                        name.set('type', 'personal')
                        # Note: bibutils looks for family/given split
                        if ' ' in au:
                            family, given = au.split(' ')
                            namePart = SubElement(name, 'namePart')
                            namePart.set('type', 'given')
                            namePart.text = given
                            namePart = SubElement(name, 'namePart')
                            namePart.set('type', 'family')
                            namePart.text = family
                        else:
                            namePart = SubElement(name, 'namePart')
                            namePart.set('type', 'family')
                            namePart.text = au
                        role = SubElement(name, 'role')
                        roleTerm = SubElement(role, 'roleTerm')
                        roleTerm.set('type', 'text')
                        roleTerm.text = 'author'
                typeOfResource = SubElement(mods, 'typeOfResource')
                typeOfResource.text = 'text'
                
                # The following block is about the "host" journal in which this
                # article appeared
                relatedItem = SubElement(mods, 'relatedItem')
                relatedItem.set('type', 'host')
                titleInfo = SubElement(relatedItem, 'titleInfo')
                title = SubElement(titleInfo, 'title')
                title.text = mm['journal']
                if mm.get('issn', ''):
                    identifier = SubElement(relatedItem, 'identifier')
                    identifier.set('type', 'issn')
                    identifier.text = mm['issn']
                originInfo = SubElement(relatedItem, 'originInfo')
                issuance = SubElement(originInfo, 'issuance')
                issuance.text = 'continuing'
                part = SubElement(relatedItem, 'part')
                if mm.get('volume', ''):
                    detail = SubElement(part, 'detail')
                    detail.set('type', 'volume')
                    number = SubElement(detail, 'number')
                    number.text = mm['volume']
                if mm.get('issue', ''):
                    detail = SubElement(part, 'detail')
                    detail.set('type', 'issue')
                    number = SubElement(detail, 'number')
                    number.text = mm['issue']
                if mm.get('pages', ''):
                    extent = SubElement(part, 'extent')
                    extent.set('unit', 'page')
                    if '-' in mm['pages']:
                        start, end = mm['pages'].split('-')
                        st = SubElement(extent, 'start')
                        st.text = start
                        en = SubElement(extent, 'end')
                        en.text = end
                    else:
                        st = SubElement(extent, 'start')
                        st.text = mm['pages']
                if mm.get('pubdate', ''):
                    date = SubElement(part, 'date')
                    date.text = mm['pubdate'][:4]
                
                for subtype in ['subject', 'keyword']:
                    for sub in mm.get(subtype, []):
                        subject = SubElement(mods, 'subject')
                        if subtype == 'subject':
                            subject.set('authority', 'mesh')
                        topic = SubElement(subject, 'topic')
                        topic.text = sub
                    
            except:
                print traceback.print_exc()
        
        mods_out = etree.tostring(root)
        if output_format == 'mods': 
            return mods_out
        elif output_format in FORMATS.keys():
            bibutils_format_name = FORMATS[output_format]
            filename = '%s/records-%s.mods' % (config.temp_image_dir, time.time())
            fp = open(filename, 'w')
            fp.write(mods_out)
            fp.close()
            bibutils_call = '/usr/local/bin/xml2%s %s > %s.%s' % (bibutils_format_name,
                filename, filename, output_format)
            os.system(bibutils_call)
            time.sleep(3)
            return open('%s.%s' % (filename, output_format)).read()
            
    except:
        print traceback.print_exc()



def get_sfx_link (context, source_id, unique_identifier, resolver=None):
    source_catalog = context.get_source_catalog()
    source = source_catalog.get_source(source_id)
    query_string = source.sfx_pattern.replace('[[UI]]', unique_identifier)
    canarydb_sid = 'sid=info:sid/canarydatabase.org:canarydb'
    # FIXME!
    base_url = 'http://sfx.library.yale.edu/sfx_local?'
    if resolver:
        base_url = resolver.base_url
    if base_url.endswith('?'):
        return '%s%s&amp;%s' % (base_url, canarydb_sid, query_string)
    else:
        return '%s?%s&amp;%s' % (base_url, canarydb_sid, query_string)
