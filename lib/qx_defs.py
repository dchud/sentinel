import os
import shelve
from stat import ST_MTIME
from time import time
from cPickle import load, dump

from DBPool import DBPool
import log4py
import MySQLdb

from quixote import get_publisher
from quixote.config import Config
from quixote.errors import AccessError
from quixote.form2 import Form
from quixote.publish import SessionPublisher
from quixote.session import Session, SessionManager

from dulcinea.database import ObjectDatabase, get_transaction
from dulcinea.persistent_session import DulcineaSession, DulcineaSessionManager
from dulcinea.user import DulcineaUser
from dulcinea.user_database import DulcineaUserDatabase

from canary.source_catalog import SourceCatalog
from canary.utils import MyLogger

class MyConfig(Config):
    """Add any newly defined config variables to my_vars
    to allow them to be visible in the application."""

    def __init__ (self, read_defaults=1):
        Config.__init__(self, read_defaults)

        my_vars = [
            'zodb_connection_string',
            'db_host',
            'db_user',
            'db_passwd',
            'db_pool_size',
            'db_name',
            'log_dir',
            'static_html_dir',
            'static_image_dir',
            ]

        for var in my_vars:
            Config.config_vars.append(var)



class MySessionPublisher(SessionPublisher):

    def __init__ (self, *args, **kwargs):

        # Load app-specific configuration, extra vars specified in qx_defs.MyConf
        self.config = MyConfig()
        config = self.config
        config.read_file('conf/canary_config.py')

        # testing Dulcinea: DulcineaSessionManager defaults session_class=DulcineaSession
        self._zodb = ObjectDatabase()
        sessions = self._zodb.open(config.zodb_connection_string)

        self._zodb_root = self._zodb.get_root()

        if not self._zodb_root.has_key('session_mgr'):
            self._zodb_root['session_mgr'] = DulcineaSessionManager(session_mapping=sessions)
            get_transaction().commit()
        session_mgr = self._zodb_root['session_mgr']

        # testing zodb for users
        if not self._zodb_root.has_key('user_db'):
            self._zodb_root['user_db'] = DulcineaUserDatabase()
            get_transaction().commit()


        # Set up a dbpool
        # FIXME:  Why isn't config.db_pool_size loading?  Hardcoded for now...
        # FIXME:  Driver name is hardcoded too.
        self._dbpool = DBPool(MySQLdb,
                              5,                 #config.db_pool_size,
                              config.db_host,
                              config.db_user,
                              config.db_passwd,
                              config.db_name)

        # establish a cursor to initialize stuff
        init_cursor = self._dbpool.getConnection().cursor()

        from canary.db_model import DBModel
        print 'd: loading DBModel'
        self._dbmodel = DBModel()
        self._dbmodel.load_from_db(init_cursor)
        
        print 'd: loading SourceCatalog'
        self._source_catalog = SourceCatalog()
        self._source_catalog.load_sources(init_cursor, load_terms=True)
        
        init_cursor.close()

        # Set up log4py Logger
        self._logger = log4py.Logger().get_instance(self)
        self._logger.set_target(config.log_dir + "/sentinel.log")
        self._logger.set_formatstring(log4py.FMT_DEBUG)
        self._logger.set_loglevel(log4py.LOGLEVEL_DEBUG)
        self._logger.set_rotation(log4py.ROTATE_DAILY)
        self._logger.info('Started logger.')

        # Init superclass
        # session_mgr = self.session_mgr
        # FIXME: should root_namespace be hardcoded?
        SessionPublisher.__init__(self,
                                  root_namespace='canary.ui',
                                  session_mgr=session_mgr,
                                  config=config)

        self.setup_logs()

    def get_config (self):
        return self.config

    def get_cursor (self):
        return self._dbpool.getConnection().cursor()

    def get_dbmodel (self):
        return self._dbmodel
    
    def set_dbmodel (self, db_model):
        self._dbmodel = db_model

    def get_user_db (self):
        return self._zodb_root['user_db']

    def get_root (self):
        return self._zodb_root

    def configure_logger (self, logger):
        logger.set_target(self.get_config().log_dir + "/sentinel.log")
        logger.set_formatstring(self._logger.get_formatstring())
        logger.set_loglevel(self._logger.get_loglevel())
        logger.set_rotation(self._logger.get_rotation())

    def get_source_catalog (self):
        return self._source_catalog

    def set_source_catalog (self, catalog):
        self._source_catalog = catalog


class NotLoggedInError (AccessError):
    """
    To be called when the requested action requires a logged in user.
    Whether that user has access rights or not can only be determined
    after the user actually logs in.
    """
    status_code = 403
    title = "Access denied"
    description = "Authorized access only."


class MyDulcineaUser (DulcineaUser):

    def __init__ (self, user_id=None):
        DulcineaUser.__init__(self, user_id)
        self.is_active = True
        self.is_admin = False
        self.is_editor = False
        self.email = ''
        self.name = ''


class MyForm (Form):
    """
    Automatically creates a logger instance on any arbitrary Form.
    """
    def __init__ (self):
        Form.__init__(self)
        self.logger = log4py.Logger().get_instance(self)
        get_publisher().configure_logger(self.logger)
