# $Id$

_q_exports = [
    '_q_index',
    ]

from quixote.errors import TraversalError

from canary.ui.edit.study import study_ui
from canary.ui.edit.study.study_ui import StudyActions
from canary.ui.pages import not_found

_q_index = study_ui._q_index


def _q_lookup (request, queued_record_id):
    try:
        if not queued_record_id == None:
            return StudyActions(queued_record_id)
        else:
            raise TraversalError
    except:
        return not_found('queued record')
