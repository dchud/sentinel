_q_exports = [
    '_q_index',
    'create',
    ]

from quixote.errors import TraversalError

from canary.ui.admin.dv_data.value import value_ui
from canary.ui.admin.dv_data.value.value_ui import ValueActions

_q_index = value_ui._q_index
create = value_ui.create


def _q_lookup (request, value_id):
    try:
        if not value_id == None:
            return ValueActions(value_id)
        else:
            raise TraversalError
    except:
        return not_found('value')
