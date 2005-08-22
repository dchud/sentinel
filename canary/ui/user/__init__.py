# $Id$

_q_exports = [
    '_q_index',
    ]

from quixote.errors import TraversalError

from canary.qx_defs import NotLoggedInError
from canary.ui.pages import not_found
from canary.ui.user import user_ui

_q_index = user_ui._q_index



def _q_access (request):
    try:
        if request.session == None or request.session.user == None:
            raise NotLoggedInError('You must first log in.')
    except:
        raise NotLoggedInError('You must first log in.')
