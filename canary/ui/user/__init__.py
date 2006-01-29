# $Id$

_q_exports = [
    '_q_index',
    'prefs',
    'set',
    'add_record',
    'remove_record',
    'create_set',
    'add_record_set',
    'remove_record_set',
    ]

from quixote.errors import TraversalError

from canary.qx_defs import NotLoggedInError
from canary.ui.user import set, user_ui
from canary.ui.user.user_ui import prefs, add_record, remove_record
from canary.ui.user.user_ui import create_set, add_record_set, remove_record_set

_q_index = user_ui._q_index


def _q_access (request):
    try:
        if request.session == None or request.session.user == None:
            raise NotLoggedInError('You must first log in.')
    except:
        raise NotLoggedInError('You must first log in.')
