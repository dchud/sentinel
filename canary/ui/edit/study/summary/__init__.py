# $Id$

_q_exports = [
    '_q_index',
    'add',
    ]

from quixote.errors import TraversalError

from canary.ui.edit.study.summary import summary_ui
from canary.ui.edit.study.summary.summary_ui import SummaryActions

_q_index = summary_ui._q_index
add = summary_ui.add


def _q_lookup (request, summary_id):
    try:
        if not summary_id == None:
            return SummaryActions(summary_id)
        else:
            raise TraversalError
    except:
        return not_found('summary')
