# $Id$

_q_exports = [
    '_q_index',
    'update',
    ]

from quixote.errors import AccessError

from canary.qx_defs import NotLoggedInError
from canary.ui.assistant import assistant_ui

_q_index = assistant_ui._q_index
update = assistant_ui.update

def _q_access (request):
    if request.session.user == None:
        raise NotLoggedInError('Authorized access only.')
    if not (request.session.user.is_assistant):
        raise AccessError("You don't have access to this page.")
