_q_exports = [
    '_q_index',
    'find',
    'add',
    ]

from quixote.errors import TraversalError

from canary.ui.edit.study.species import species_ui
from canary.ui.edit.study.species.species_ui import SpeciesActions

_q_index = species_ui._q_index
find = species_ui.find
add = species_ui.add


def _q_lookup (request, species_id):
    try:
        if not species_id == None:
            return SpeciesActions(species_id)
        else:
            raise TraversalError
    except:
        return not_found('species')
