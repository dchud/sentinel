_q_exports = [
    '_q_index',
    'create',
    ]

from quixote.errors import TraversalError

from canary.ui.edit.study.methodology import methodology_ui
from canary.ui.edit.study.methodology.methodology_ui import MethodologyActions

_q_index = methodology_ui._q_index
create = methodology_ui.create


def _q_lookup (request, methodology_id):
    try:
        if not methodology_id == None:
            return MethodologyActions(methodology_id)
        else:
            raise TraversalError
    except:
        return not_found('methodology')
