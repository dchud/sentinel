# $Id$

from cStringIO import StringIO
import traceback
import urllib

from elementtree import ElementTree as etree
from elementtree.ElementTree import Element, SubElement

import canary
from canary import dtuple
from canary.utils import DTable


def find_resolver (context, ip_address='127.0.0.1'):
    """For a given web user's IP address, find an appropriate resolver from
    OCLC's registry.  We don't want to clobber OCLC's server, though.  So first 
    check local cache, though, and if it's not available locally then query OCLC
    and be sure to save the Resolver when we're done."""
    
    r = Resolver(context, -1, ip_address)
    if r.base_url:
        return r
        
    r.load_from_db(context)
    if r.base_url:
        return r
        
    r.load_from_xml(context)
    r.save(context)
    if r.base_url == 'http://worldcatlibraries.org/registry/gateway':
        return None
    else:
        return r
    

class Resolver (canary.context.Cacheable, DTable):
    """Represents a single institutional OpenURL resolver.  Provides enough
    functionality to determine, for a given site user's IP_ADDRESS, whether
    such a resolver is available, and if not, provides reasonable default
    values pointing to OCLC's Find in a Library resolver."""
    
    TABLE_NAME = 'resolvers'
    
    CACHE_KEY = 'resolver'
    
    CACHE_CHECK_FIELD = 'base_url'
    
    CACHE_ID_FIELD = 'ip_address'
    
    # This should probably be in Config, but it's easy enough to change here
    LOOKUP_URL = 'http://worldcatlibraries.org/registry/lookup'
    NS = 'http://worldcatlibraries.org/registry/resolver'

    load = canary.context.Cacheable.load
    
    def __init__ (self, context=None, uid=-1, ip_address='127.0.0.1'):
        try:
            if self.uid >= 0:
                return
        except AttributeError:
            pass
        self.uid = uid
        self.ip_address = ip_address
        self.record_xml = ''
        self.base_url = self.icon_url = self.link_text = self.institution = ''
        self.supports_01 = self.supports_10 = False
        self.date_modified = ''
        

    def load (self, context):
        # Is it already loaded?  Convenience check for client calls
        # don't need to verify loads from the cache.
        if context.config.use_cache:
            try:
                if getattr(self, self.CACHE_CHECK_FIELD):
                    # Already loaded
                    return
            except AttributeError:
                # Not already loaded, so continue
                pass
        
        self.load_from_db(context)
        if not self.base_url:
            self.load_from_xml(context)
        

    def load_from_db (self, context):
        cursor = context.get_cursor()
        cursor.execute("""SELECT * FROM """ + self.TABLE_NAME + """
            WHERE ip_address = %s
            """, self.ip_address)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        row = cursor.fetchone()
        if row:
            row = dtuple.DatabaseTuple(desc, row)
            for k, v in row.items():
                self.set(k, v) 
        else:
            context.logger.error('No %s with %s %s in local database' % (self.__class__.__name__,
                self.CACHE_ID_FIELD, getattr(self, self.CACHE_ID_FIELD)))


    def load_from_xml (self, context):
        url = '%s?IP=%s' % (self.LOOKUP_URL, self.ip_address)
        try:
            fp = urllib.urlopen(url)
            self.record_xml = fp.read()
            fp.close()
            # NOTE: Is it safe to pickle an ElementTree tree?  
            # Don't bind to self if not.
            self.tree = etree.parse(StringIO(self.record_xml))
            records = self.tree.findall('.//{%s}resolverRegistryEntry' % self.NS)
            if not records:
                raise 'InvalidIPAddress'
            for attr, studly in [
                ('institution', 'institutionName'),
                ('base_url', 'baseURL'),
                ('icon_url', 'linkIcon'),
                ('link_text', 'linkText')]:
                try:
                    setattr(self, attr, self.tree.findall('.//{%s}%s' % \
                        (self.NS, studly))[0].text)
                except:
                    setattr(self, attr, '')
        except:
            # Assign default OCLC "Find in a Library" values as useful fallback
            self.institution = 'OCLC'
            self.base_url = 'http://worldcatlibraries.org/registry/gateway'
            
        if not self.link_text:
            self.link_text = 'Find in a library'
        if not self.icon_url:
            # Note: without a context 
            self.icon_url = '%s/images/findinalibrary_badge.gif' % \
                context.config.site_base_url


    def save (self, context):
        cursor = context.get_cursor()
        try:
            if self.uid == -1:
                insert_phrase = 'INSERT INTO %s' % self.TABLE_NAME
                cursor.execute(insert_phrase + """
                    (uid, ip_address, record_xml, institution, base_url,
                    icon_url, link_text, 
                    supports_01, supports_10, date_modified)
                    VALUES 
                    (NULL, %s, %s, %s, 
                    %s, %s, %s, 
                    %s, %s, NOW())
                    """, (self.ip_address, self.record_xml, self.institution, 
                        self.base_url, self.icon_url, self.link_text, 
                        int(self.supports_01), int(self.supports_10))
                    )
                self.uid = self.get_new_uid(context)
                context.logger.info('Resolver created with uid %s', self.uid)
            else:
                update_phrase = 'UPDATE %s ' % self.TABLE_NAME
                cursor.execute(update_phrase + """
                    SET record_xml = %s, base_url = %s,
                        institution = %s, icon_url = %s, link_text = %s,
                        supports_01 = %s, supports_10 = %s, date_modified = NOW()
                    WHERE ip_address = %s
                    """, (self.record_xml, self.base_url,
                        self.institution, self.icon_url, self.link_text,
                        int(self.supports_01), int(self.supports_10), 
                        self.ip_address)
                    )
                context.logger.info('Resolver %s updated', self.uid)
            if context.config.use_cache:
                context.cache_set('%s:%s' % (self.CACHE_KEY, 
                    getattr(self, self.CACHE_ID_FIELD)), self)
        except Exception, e:
            context.logger.error(e)
