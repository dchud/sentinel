_q_exports = [
    '_q_index',
    'find',
    ]

from quixote.errors import TraversalError

from canary.ui.admin.record import record_ui
from canary.ui.admin.record.record_ui import RecordActions
from canary.ui.pages import not_found

_q_index = record_ui._q_index
find = record_ui.find

def _q_lookup (request, record_id):
    try:
        if not record_id == None:
            return RecordActions(int(record_id))
        else:
            raise TraversalError
    except:
        return not_found('record')
