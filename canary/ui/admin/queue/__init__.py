# $Id$

_q_exports = [
    '_q_index',
    'add',
    'create',
    'list',
    'receive',
    'dedupe',
    ]

from quixote.errors import TraversalError

from canary.ui.pages import not_found
from canary.ui.admin.queue import queue_ui
from canary.ui.admin.queue.queue_ui import QueueActions

_q_index = queue_ui._q_index
add = queue_ui.add
create = queue_ui.create
list = queue_ui.list
receive = queue_ui.receive
dedupe = queue_ui.dedupe


def _q_lookup (request, batch_id):
    try:
        if not batch_id == None:
            return QueueActions(int(batch_id))
        else:
            raise TraversalError
    except:
        return not_found('queue')
