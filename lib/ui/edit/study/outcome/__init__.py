_q_exports = [
    '_q_index',
    'find',
    'add',
    ]

from quixote.errors import TraversalError

from canary.ui.edit.study.outcome import outcome_ui
from canary.ui.edit.study.outcome.outcome_ui import OutcomeActions

_q_index = outcome_ui._q_index
find = outcome_ui.find
add = outcome_ui.add


def _q_lookup (request, outcome_id):
    try:
        if not outcome_id == None:
            return OutcomeActions(outcome_id)
        else:
            raise TraversalError
    except:
        return not_found('outcome')
