# $Id$

_q_exports = ['_q_index',
              ]

from quixote.errors import TraversalError

from canary.ui.edit.batch import batch_ui
from canary.ui.edit.batch.batch_ui import BatchActions

_q_index = batch_ui._q_index


def _q_lookup (request, batch_id):
    try:
        if not batch_id == None:
            return BatchActions(batch_id)
        else:
            raise TraversalError
    except:
        return not_found('batch')
