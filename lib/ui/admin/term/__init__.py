_q_exports = ['_q_index',
              'create',
              ]

from quixote.errors import TraversalError

from canary.ui.admin.term import term_ui
from canary.ui.admin.term.term_ui import TermActions

_q_index = term_ui._q_index
create = term_ui.create



def _q_lookup (request, term_id):
    try:
        if not term_id == None:
            return TermActions(term_id)
        else:
            raise TraversalError
    except:
        return not_found('term')
