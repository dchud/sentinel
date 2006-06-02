# $Id$

_q_exports = [
    '_q_index',
    'add',
    'update',
    'delete',
    'query',
    ]

from quixote.errors import TraversalError

from canary.ui.edit.human import human_ui
from canary.ui.edit.human.human_ui import HumanActions

_q_index = human_ui._q_index
add = human_ui.add
query = human_ui.query

def _q_lookup (request, human_id):
    try:
        if not human_id == None:
            return HumanActions(human_id)
        else:
            raise TraversalError
    except:
        import traceback
        print traceback.print_exc()
        
        return not_found('human study')
