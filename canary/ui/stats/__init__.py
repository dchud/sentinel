# $Id$

_q_exports = [
    '_q_index',
    'query',
    ]

from quixote.errors import AccessError

from canary.qx_defs import NotLoggedInError
from canary.ui.stats import stats_ui

_q_index = stats_ui._q_index
query = stats_ui.query

def _q_access (request):
    if request.session.user == None:
        raise NotLoggedInError('Authorized access only.')
    if not (request.session.user.is_admin \
        or request.session.user.is_editor \
        or request.session.user.is_assistant):
        raise AccessError("You don't have access to this page.")
