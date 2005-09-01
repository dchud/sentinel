# $Id$

_q_exports = [
    '_q_index',
    'create',
    ]

from quixote import get_publisher
from quixote.errors import TraversalError

from canary.ui.admin.user import user_ui
from canary.ui.admin.user.user_ui import UserActions
from canary.ui.pages import not_found

_q_index = user_ui._q_index
create = user_ui.create


def _q_lookup (request, user_id):
    try:
        if not user_id == None:
            return UserActions(user_id)
        else:
            raise TraversalError
    except Exception, e:
        return not_found('user')
