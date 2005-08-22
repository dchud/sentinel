# $Id$

_q_exports = [
    '_q_index',
    'create',
    ]

from quixote.errors import TraversalError

from canary.ui.admin.dv_data.group import group_ui
from canary.ui.admin.dv_data.group.group_ui import GroupActions

_q_index = group_ui._q_index
create = group_ui.create



def _q_lookup (request, group_id):
    try:
        if not group_id == None:
            return GroupActions(group_id)
        else:
            raise TraversalError
    except:
        return not_found('group')
