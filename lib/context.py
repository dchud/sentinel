# $Id$

import log4py
import memcache
import MySQLdb
import pprint
import traceback

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
        context = Context()
        if args:
            uid = args[0]
        elif kwargs:
            uid = kwargs.get('uid', None)
        else:
            uid = -1
        full_cache_key = '%s:%s' % (cls.CACHE_KEY, uid)
        if context.config.use_cache:
            try:
                if uid \
                    and uid >= 0:
                    item = context.cache_get(full_cache_key)
                    if item:
                        print 'HIT %s' % full_cache_key
                        return item
                    else:
                        print 'MISS %s' % full_cache_key
                else:
                    print 'FAIL %s' % full_cache_key
            except:
                print 'ERROR %s\n', traceback.print_exc()
        
        item = object.__new__(cls)
        item.__init__(*args, **kwargs)
        if not uid == -1:
            item.load()
            if context.config.use_cache \
                and not uid == None:
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
            'db_pool_size',
            'db_name',
            'log_dir',
            'static_html_dir',
            'static_image_dir',
            'use_cache',
            'cache_server_list',
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
        if not self.__dict__.has_key('_dbpool'):
            print 'd: loading DBPool'
            self._dbpool = canary.DBPool.DBPool(MySQLdb,
                10,                 #config.db_pool_size,
                self.config.db_host,
                self.config.db_user,
                self.config.db_passwd,
                self.config.db_name)

        if not self.__dict__.has_key('_dbmodel'):
            print 'd: loading DBModel'
            self._dbmodel = canary.db_model.DBModel()
            self._dbmodel.load_from_db()
        
        if not self.__dict__.has_key('_source_catalog'):
            print 'd: loading SourceCatalog'
            self._source_catalog = canary.source_catalog.SourceCatalog()
            self._source_catalog.load_sources(load_terms=True)
        
        if not self.__dict__.has_key('_gazeteer'):
            print 'd: loading gazeteer codes'
            self._gazeteer = canary.gazeteer.Gazeteer()
            self._gazeteer.load()
        
        # If not set to use_cache==True, all memcache calls will be
        # avoided.  See self.cache_*.
        if self.config.use_cache:
            if not self.__dict__.has_key('_cache'):
                self._cache = memcache.Client(self.config.cache_server_list, 
                    debug=0)
        else:
            self._cache = None

        # Set up log4py Logger
        if not self.__dict__.has_key('_logger'):
            self._logger = log4py.Logger().get_instance('Context')
            self._logger.set_target(self.config.log_dir + "/sentinel.log")
            self._logger.set_formatstring(log4py.FMT_DEBUG)
            self._logger.set_loglevel(log4py.LOGLEVEL_DEBUG)
            self._logger.set_rotation(log4py.ROTATE_DAILY)
            self._logger.info('Started logger.')


    def get_cursor (self):
        """ Get a RDBMS cursor, by first grabbing a connection from the 
        pool.  Store the connection in the context; a later client
        call to close_cursor() will close the cursor and free the 
        connection back to the pool."""
        self.connection = self._dbpool.getConnection()
        return self.connection.cursor()

    def close_cursor (self, cursor):
        """ Close the current cursor and connection (back into the pool).
         Assumes one-at-a-time, nonconcurrent processing of quixote
         requests.  See get_cursor()."""
        cursor.close()
        self.connection.close()
        
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
