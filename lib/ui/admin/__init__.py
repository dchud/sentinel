_q_exports = [
    'queue',
    'session',
    'source',
    'source_map',
    'sources',
    'term',
    'user',
    'users',
    'concept',
    'dv_data',
    'reload_sources',
    'zodb_keys',
    ]

import string

from quixote.errors import AccessError, PublishError, TraversalError
from dulcinea.database import get_transaction

from canary.ui.admin import admin_ui
from canary.ui.admin import queue
from canary.ui.admin import session
from canary.ui.admin import source
from canary.ui.admin import term
from canary.ui.admin import user
from canary.ui.admin import concept
from canary.ui.admin import dv_data
from canary.ui.pageframe import header, footer
from canary.ui.pages import not_found
from canary.qx_defs import NotLoggedInError

_q_index = admin_ui._q_index
users = admin_ui.users
source_map = admin_ui.source_map
sources = admin_ui.sources
reload_sources = admin_ui.reload_sources
zodb_keys = admin_ui.zodb_keys


def _q_access (request):
    if request.session.user == None:
        raise NotLoggedInError('Authorized access only.')
    if not (request.session.user.is_admin):
        raise AccessError("You don't have access to this page.")


