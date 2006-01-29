# $Id$

_q_exports = [
    '_q_index',
    'lock',
    'unlock',
    'delete',
    ]

from quixote import get_publisher
from quixote.errors import TraversalError

from canary.ui.user.set import set_ui
from canary.ui.user.set.set_ui import SetActions
from canary.ui.pages import not_found

_q_index = set_ui._q_index


def _q_lookup (request, set_id):
    try:
        if not set_id == None:
            return SetActions(int(set_id))
        else:
            raise TraversalError
    except Exception, e:
        return not_found('set')
