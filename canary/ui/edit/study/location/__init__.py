# $Id$

_q_exports = [
    '_q_index',
    'find',
    'add',
    ]

from quixote.errors import TraversalError

from canary.ui.edit.study.location import location_ui
from canary.ui.edit.study.location.location_ui import LocationActions

_q_index = location_ui._q_index
find = location_ui.find
add = location_ui.add


def _q_lookup (request, location_id):
    try:
        if not location_id == None:
            return LocationActions(location_id)
        else:
            raise TraversalError
    except:
        return not_found('location')
