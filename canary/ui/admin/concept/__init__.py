# $Id$

_q_exports = [
    '_q_index',
    'find',
    ]

from quixote.errors import TraversalError

from canary.ui.admin.concept import concept_ui
from canary.ui.admin.concept.concept_ui import ConceptActions
from canary.ui.pages import not_found

_q_index = concept_ui._q_index
find = concept_ui.find

def _q_lookup (request, concept_id):
    try:
        if not concept_id == None:
            return ConceptActions(concept_id)
        else:
            raise TraversalError
    except:
        return not_found('concept')
