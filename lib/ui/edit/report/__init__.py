_q_exports = ['_q_index',
              ]

from quixote.errors import TraversalError

from canary.ui.edit.report import report_ui
from canary.ui.edit.report.report_ui import ReportActions
from canary.ui.pages import not_found

_q_index = report_ui._q_index


def _q_lookup (request, queued_record_id):
    #print 'edit.report.__init__._q_lookup(%s)' % record_id
    try:
        if not queued_record_id == None:
            return ReportActions(queued_record_id)
        else:
            raise TraversalError
    except:
        return not_found('queued record')
