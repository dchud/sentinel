_q_exports = ['_q_index',
              'add',
              'receive',
              ]

from quixote.errors import TraversalError

from canary.ui.admin.queue import queue_ui
#from canary.ui.admin.queue.queue_ui import QueueActions

_q_index = queue_ui._q_index
add = queue_ui.add
receive = queue_ui.receive


#def _q_lookup (request, queue_id):
#    try:
#        if not queue_id == None:
#            return QueueActions(queue_id)
#        else:
#            raise TraversalError
#    except:
#        return not_found('queue')
