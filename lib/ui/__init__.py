# $Id$

_q_exports = [
    'error',
    'search',
    'record',
    'canary_png',
    'about',
    'admin',
    'edit',
    'login',
    'logout',
    'user',
    'reaper',
    ]

from quixote.errors import PublishError
from quixote.publish import get_publisher
from quixote.util import StaticFile

from canary.qx_defs import NotLoggedInError
from canary.qx_utils import MyStaticFile, load_static_exports
from canary.ui import about, admin, edit, user, record_ui
from canary.ui.pages import _q_index, _q_exception_handler, not_found, reaper
from canary.ui.pages import login, logout
from canary.ui.browse_ui import Browse
from canary.ui.search import search

record = record_ui

config = get_publisher().config

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
            mime_type='application/x-javascript', cache_time=60)
    elif name == 'browse':
        return Browse(request)
    else:
        return not_found()
