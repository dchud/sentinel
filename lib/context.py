# $Id$

import os
import pprint
import traceback

import log4py
import memcache
import MySQLdb
import PyLucene

import quixote.config

import canary.db_model
import canary.DBPool
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
            print 'Context:', context, 'uid:', uid
            return item
            
        full_cache_key = '%s:%s' % (cls.CACHE_KEY, uid)
        if context.config.use_cache:
            try:
                item = context.cache_get(full_cache_key)
                if item:
                    print 'HIT %s' % full_cache_key
                    return item
                else:
                    print 'MISS %s' % full_cache_key
            except:
                print 'ERROR %s\n', traceback.print_exc()
        
        item = object.__new__(cls)
        item.__init__(*args, **kwargs)
        item.load(context)
        if context.config.use_cache:
            context.cache_set(full_cache_key, item)
        return item
            
            
class CanaryConfig (quixote.config.Config):
    """
    Add any newly defined config variables to my_vars
    to allow them to be visible in the application.
    """

    def __init__ (self, read_defaults=1):
        quixote.config.Config.__init__(self, read_defaults)

        my_vars = [
            'db_host',
            'db_user',
            'db_passwd',
            'db_name',
            'use_db_pool',
            'db_pool_size',
            'log_dir',
            'static_html_dir',
            'static_image_dir',
            'use_cache',
            'cache_server_list',
            'search_index_dir',
            'site_status',
            'site_status_note',
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
    
    __shared_state = {}
    
    def __init__ (self, config=None):
        self.__dict__ = self.__shared_state
        
        self.config = config
        if not self.config:
            self.config = CanaryConfig()
            self.config.read_file('conf/canary_config.py')
        

        # Set up a dbpool
        # FIXME:  Why isn't config.db_pool_size loading?  Hardcoded for now...
        # FIXME:  Driver name is hardcoded too.
        if self.config.use_db_pool:
            if not self.__dict__.has_key('_dbpool'):
                print 'd: loading DBPool'
                self._dbpool = canary.DBPool.DBPool(MySQLdb,
                    10,                 #config.db_pool_size,
                    self.config.db_host,
                    self.config.db_user,
                    self.config.db_passwd,
                    self.config.db_name)
        else:
            if not self.__dict__.has_key('_connection'):
                self._connection = MySQLdb.connect(db=self.config.db_name,
                    host=self.config.db_host, user=self.config.db_user,
                    passwd=self.config.db_passwd)
            if not self.__dict__.has_key('_cursor'):
                self._cursor = self._connection.cursor()

        if not self.__dict__.has_key('_dbmodel'):
            print 'd: loading DBModel'
            self._dbmodel = canary.db_model.DBModel()
            self._dbmodel.load(self)
        
        if not self.__dict__.has_key('_source_catalog'):
            print 'd: loading SourceCatalog'
            self._source_catalog = canary.source_catalog.SourceCatalog()
            self._source_catalog.load(self, load_terms=True)
        
        if not self.__dict__.has_key('_gazeteer'):
            print 'd: loading gazeteer codes'
            self._gazeteer = canary.gazeteer.Gazeteer()
            self._gazeteer.load(self)
        
        # If not set to use_cache==True, all memcache calls will be
        # avoided.  See self.cache_*.
        if self.config.use_cache:
            if not self.__dict__.has_key('_cache'):
                self._cache = memcache.Client(self.config.cache_server_list, 
                    debug=0)
        else:
            self._cache = None

        # Initialize the search index path
        try:
            if not os.path.exists(self.config.search_index_dir):
                os.mkdir(self.config.search_index_dir)
                self._search_index_store = PyLucene.FSDirectory.getDirectory(
                    self.config.search_index_dir, True)
            else:
                self._search_index_store = PyLucene.FSDirectory.getDirectory(
                    self.config.search_index_dir, False)
        except:
            import traceback
            print traceback.print_exc()

        # Set up log4py Logger
        if not self.__dict__.has_key('_logger'):
            self._logger = log4py.Logger().get_instance('Context')
            self._logger.set_target(self.config.log_dir + "/sentinel.log")
            self._logger.set_formatstring(log4py.FMT_DEBUG)
            self._logger.set_loglevel(log4py.LOGLEVEL_DEBUG)
            self._logger.set_rotation(log4py.ROTATE_DAILY)
            self._logger.info('Started logger.')


    def get_cursor (self):
        """ 
        Will behave differently, depending on whether config.use_db_pool
        is set to True of False.
        
        If True:
        Get a RDBMS cursor, by first grabbing a connection from the 
        pool.  Store the connection in the context; a later client
        call to close_cursor() will close the cursor and free the 
        connection back to the pool.
        
        If False:
        Return the existing cursor.
        """
        if self.config.use_db_pool:
            self.connection = self._dbpool.getConnection()
            return self.connection.cursor()
        else:
            return self._cursor

    def close_cursor (self, cursor):
        """
        Will behave differently, depending on whether config.use_db_pool
        is set to True of False.
        
        If True:
        Close the current cursor and connection (back into the pool).
        Assumes one-at-a-time, nonconcurrent processing of quixote
        requests.  See get_cursor().
        
        If False:
        Do nothing.
        """
        if self.config.use_db_pool:
            cursor.close()
            self.connection.close()
        else:
            # Do nothing (leave the cursor as it is)
            pass
        
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
            print 'GET:', key
            return self._cache.get(key)
    
    def cache_get_multi (self, keys):
        if self.config.use_cache:
            print 'GET_MULTI:', keys
            return self._cache.get_multi(keys)
        
    def cache_set (self, key, val, time=0):
        if self.config.use_cache:
            print 'SET:', key
            return self._cache.set(key, val, time)
        
    def cache_replace (self, key, value, time=0):
        if self.config.use_cache:
            print 'REPLACE:', key
            return self._cache.replace(key, value, time)
        
    def cache_delete (self, key, time=0):
        if self.config.use_cache:
            print 'DELETE:', key
            return self._cache.delete(key, time)

    def configure_logger (self, logger):
        logger.set_target(self.config.log_dir + "/sentinel.log")
        logger.set_formatstring(self._logger.get_formatstring())
        logger.set_loglevel(self._logger.get_loglevel())
        logger.set_rotation(self._logger.get_rotation())

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
