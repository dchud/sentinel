# $Id$

_q_exports = [
    'error',
    'search',
    'record',
    'news',
    'canary_png',
    'advanced_search',
    'opensearch',
    'unapi',
    'about',
    'admin',
    'edit',
    'login',
    'logout',
    'register',
    'verify',
    'user',
    'assistant',
    'reaper',
    'resetpass',
    ]

import cStringIO
import sys

from quixote.errors import PublishError
from quixote.publish import get_publisher
from quixote.util import StaticFile

from canary.qx_defs import NotLoggedInError
from canary.qx_utils import MyStaticFile, load_static_exports
from canary.ui import about, admin, assistant, edit, user, record_ui, opensearch
from canary.ui.browse_ui import Browse
from canary.ui.pages import _q_index, _q_exception_handler, not_found, reaper
from canary.ui.pages import login_general, login_yale, logout
from canary.ui.pages import register, verify, resetpass
from canary.ui.pages import news, robots, unapi, TempImage
from canary.ui.search import search, advanced_search


record = record_ui

config = get_publisher().config

this_module = sys.modules[__name__]
login = getattr(this_module, 'login_%s' % config.authn_mode)


def error (request):
    raise PublishError(public_msg = "Oops, an error occured.")


def _q_lookup (request, name=''):
    if name == 'favicon.ico':
        return request.redirect('/images/favicon.ico')
    elif name == 'wdd_styles.css':
        return StaticFile(config.static_html_dir + '/wdd_styles.css',
            mime_type='text/css', cache_time=60)
    elif name == 'wdd_print.css':
        return StaticFile(config.static_html_dir + '/wdd_print.css',
            mime_type='text/css', cache_time=60)
    elif name == 'script.js':
        return StaticFile(config.static_html_dir + '/script.js',
            mime_type='text/javascript', cache_time=60)
    elif name == 'mochikit.js':
        return StaticFile(config.static_html_dir + '/MochiKit.js',
            mime_type='text/javascript', cache_time=60)
    elif name == 'robots.txt':
        if config.enable_robots_txt:
            return robots()
        else:
            return not_found()
    elif name == 'browse':
        return Browse(request)
    elif name == 'timage':
        return TempImage()
    else:
        return not_found()
