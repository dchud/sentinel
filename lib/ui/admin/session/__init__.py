_q_exports = ['_q_index',
              ]

from quixote.errors import TraversalError

from canary.ui.admin.session import session_ui
from canary.ui.admin.session.session_ui import SessionActions

_q_index = session_ui._q_index


def _q_lookup (request, session_id):
    try:
        if not session_id == None:
            return SessionActions(session_id)
        else:
            raise TraversalError
    except:
        return not_found('session')
