_q_exports = [
    '_q_index',
    'find',
    'add',
    ]

from quixote.errors import TraversalError

from canary.ui.edit.study.exposure import exposure_ui
from canary.ui.edit.study.exposure.exposure_ui import ExposureActions

_q_index = exposure_ui._q_index
find = exposure_ui.find
add = exposure_ui.add


def _q_lookup (request, exposure_id):
    try:
        if not exposure_id == None:
            return ExposureActions(exposure_id)
        else:
            raise TraversalError
    except:
        return not_found('exposure')
