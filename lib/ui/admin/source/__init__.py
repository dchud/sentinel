# $Id$

_q_exports = ['_q_index',
              'create',
              ]

from quixote.errors import TraversalError

from canary.ui.admin.source import source_ui
from canary.ui.admin.source.source_ui import SourceActions

_q_index = source_ui._q_index
create = source_ui.create



def _q_lookup (request, source_id):
    try:
        if not source_id == None:
            return SourceActions(source_id)
        else:
            raise TraversalError
    except:
        return not_found('source')
