_q_exports = [
    '_q_index',
    'create',
    ]

from quixote.errors import TraversalError

from canary.ui.edit.study.substudy import substudy_ui
from canary.ui.edit.study.substudy.substudy_ui import SubstudyActions

_q_index = substudy_ui._q_index
create = substudy_ui.create


def _q_lookup (request, substudy_id):
    try:
        if not substudy_id == None:
            return SubstudyActions(substudy_id)
        else:
            raise TraversalError
    except:
        return not_found('substudy')
