# $Id$

import logging
import logging.handlers
import os
import pprint
import traceback

import memcache
import MySQLdb
import PyLucene

import quixote.config

import canary.db_model
from canary import dtuple
import canary.gazeteer
import canary.source_catalog


class Cacheable (object):
    """
    Mix-in for any object that can be cached in memory.
    """
    
    # Subclasses must define
    CACHE_KEY = ''
    
    def __new__ (cls, *args, **kwargs):
        context = None
        uid = -1
        
        if args:
            context = args[0]
            uid = args[1]
        elif kwargs:
            context = kwargs.get('context', None)
            uid = kwargs.get('uid', None)
        
        if context == None \
            or uid == -1:
            item = object.__new__(cls)
            item.__init__(*args, **kwargs)
            return item
            
        full_cache_key = '%s:%s' % (cls.CACHE_KEY, uid)
        if context.config.use_cache:
            try:
                item = context.cache_get(full_cache_key)
                if item:
                    context.logger.debug('HIT %s', full_cache_key)
                    return item
                else:
                    context.logger.debug('MISS %s', full_cache_key)
                    pass
            except Exception, e:
                context.logger.error('ERROR %s', e)
                
        item = object.__new__(cls)
        item.__init__(*args, **kwargs)
        item.load(context)
        if context.config.use_cache:
            context.cache_set(full_cache_key, item)
        return item
    
    
    def load (self, context):
        # Can't load a new one; it hasn't been saved yet.
        if self.uid == -1:
            return

        # Is it already loaded?  Convenience check for client calls
        # don't need to verify loads from the cache.
        if context.config.use_cache:
            try:
                if getattr(self, self.CACHE_CHECK_FIELD):
                    # Already loaded
                    return
            except AttributeError:
                # Note already loaded, so continue
                pass
        
        cursor = context.get_cursor()
        cursor.execute("""SELECT * FROM """ + self.TABLE_NAME + """
            WHERE uid = %s
            """, self.uid)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        row = cursor.fetchone()
        if row:
            row = dtuple.DatabaseTuple(desc, row)
            for k, v in row.items():
                self.set(k, v) 
        else:
            context.logger.error('No %s with uid %s' % (self.__class__.__name__,
                self.uid))
                
    
    def cache_set (self, context):
        if context.config.use_cache:
            context.cache_set('%s:%s' % (self.CACHE_KEY, self.uid), self)


    def cache_delete (self, context):
        if context.config.use_cache:
            context.cache_delete('%s:%s' % (self.CACHE_KEY, self.uid))

            
class CanaryConfig (quixote.config.Config):
    """
    Add any newly defined config variables to my_vars
    to allow them to be visible in the application.
    """

    def __init__ (self, read_defaults=1):
        quixote.config.Config.__init__(self, read_defaults)

        my_vars = [
            'site_base_url',
            'db_host',
            'db_user',
            'db_passwd',
            'db_name',
            'log_level',
            'log_format',
            'log_dir',
            'static_html_dir',
            'static_image_dir',
            'temp_image_dir',
            'use_cache',
            'cache_server_list',
            'search_index_dir',
            'site_status',
            'site_status_note',
            'enable_robots_txt',
            'robots_txt',
            'authn_mode',
            ]

        for var in my_vars:
            quixote.config.Config.config_vars.append(var)
            


class Context:
    """ Context is the shared state of the canary application.
    Sharing state in this way allows immediate access to the whole API
    from anywhere else in the API, especially access to the db and memcache.
    
    Exactly follows "Borg" non-pattern as described at:
    
      http://www.onlamp.com/pub/a/python/2002/07/11/recipes.html?page=2
    
    NOTE:  because of its structure all context atts must be checked-for
    at instantiation.  Perhaps this will slow it down significantly?
    """
    
    #__shared_state = {}

    def __init__ (self, config=None):
        #self.__dict__ = self.__shared_state
        
        self.config = config
        if not self.config:
            self.config = CanaryConfig()
            self.config.read_file('conf/canary_config.py')
 
        # Get a logger to use
        self.init_logging()
        self.logger = logging.getLogger(str(self.__class__))
        self.logger.debug('Started logger')

        if not self.__dict__.has_key('_connection'):
            self.logger.info('Getting db connection')
            self._connection = MySQLdb.connect(db=self.config.db_name,
                host=self.config.db_host, user=self.config.db_user,
                passwd=self.config.db_passwd)
        if not self.__dict__.has_key('_cursor'):
            self._cursor = self._connection.cursor()

        if not self.__dict__.has_key('_dbmodel'):
            self.logger.info('loading DBModel')
            self._dbmodel = canary.db_model.DBModel()
            self._dbmodel.load(self)
        
        if not self.__dict__.has_key('_source_catalog'):
            self.logger.info('loading SourceCatalog')
            self._source_catalog = canary.source_catalog.SourceCatalog()
            self._source_catalog.load(self, load_terms=True)
        
        if not self.__dict__.has_key('_gazeteer'):
            self.logger.info('loading gazeteer codes')
            self._gazeteer = canary.gazeteer.Gazeteer()
            self._gazeteer.load(self)
        
        # If not set to use_cache==True, all memcache calls will be
        # avoided.  See self.cache_*.
        if self.config.use_cache:
            if not self.__dict__.has_key('_cache'):
                self.logger.info('Connecting to cache')
                self._cache = memcache.Client(self.config.cache_server_list, 
                    debug=0)
        else:
            self._cache = None

        # Initialize the search index path
        try:
            if not os.path.exists(self.config.search_index_dir):
                self.logger.info('Creating new lucene index: %s',
                    self.config.search_index_dir)
                os.mkdir(self.config.search_index_dir)
                self._search_index_store = PyLucene.FSDirectory.getDirectory(
                    self.config.search_index_dir, True)
            else:
                self.logger.info('opening lucene directory: %s',
                    self.config.search_index_dir)
                self._search_index_store = PyLucene.FSDirectory.getDirectory(
                    self.config.search_index_dir, False)
        except Exception, e:
            self.logger.error('Unable to initialize search index')
            self.logger.error(traceback.format_stack())
            
    def get_cursor (self):
        """ 
        Return the existing cursor.
        """
        return self._cursor
        
    def get_dbmodel (self):
        return self._dbmodel
    
    def set_dbmodel (self, db_model):
        self._dbmodel = db_model

    def get_source_catalog (self):
        return self._source_catalog

    def set_source_catalog (self, catalog):
        self._source_catalog = catalog
        
    def get_gazeteer (self):
        return self._gazeteer
        
    def cache_get (self, key):
        if self.config.use_cache:
            self.logger.debug('GET: %s', key)
            return self._cache.get(key)
    
    def cache_get_multi (self, keys):
        if self.config.use_cache:
            self.logger.debug('GET_MULTI: %s', keys)
            return self._cache.get_multi(keys)
        
    def cache_set (self, key, val, time=0):
        if self.config.use_cache:
            self.logger.debug('SET: %s', key)
            return self._cache.set(key, val, time)
        
    def cache_replace (self, key, value, time=0):
        if self.config.use_cache:
            self.logger.debug('REPLACE: %s', key)
            return self._cache.replace(key, value, time)
        
    def cache_delete (self, key, time=0):
        if self.config.use_cache:
            self.logger.debug('DELETE: %s', key)
            return self._cache.delete(key, time)

    def init_logging (self):
        """
        Set up the base logger for all other logs to use.
        This should really only get called once in the lifetime of a
        process.
        """

        # setup the rotating file handler
        # (loc, mode, maxBytes, backupCount)
        handler = logging.handlers.TimedRotatingFileHandler(
            self.config.log_dir + '/sentinel.log', when='D', interval=1)

        # set the format for log entries
        formatter = logging.Formatter(self.config.log_format)
        handler.setFormatter(formatter)

        # configure the base logger
        logger = logging.getLogger('canary')
        logger.setLevel(self.config.log_level)
        logger.addHandler(handler)

    def get_search_index_writer (self, clobber=False):
        search_index_store = PyLucene.FSDirectory.getDirectory(
            self.config.search_index_dir, clobber)
        return PyLucene.IndexWriter(search_index_store, 
            PyLucene.StandardAnalyzer(), clobber)
    
    def get_search_index_reader (self):
        return PyLucene.IndexReader.open(self.config.search_index_dir)
       
    def get_searcher (self):
        return PyLucene.IndexSearcher(PyLucene.FSDirectory.getDirectory(
            self.config.search_index_dir, False))
