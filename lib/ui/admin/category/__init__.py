_q_exports = [
    '_q_index',
    'create',
    'find',
    'list',
    'add',
    'remove',
    ]

from quixote.errors import TraversalError

from canary.ui.pages import not_found
from canary.ui.admin.category import category_ui
from canary.ui.admin.category.category_ui import CategoryActions

_q_index = category_ui._q_index
create = category_ui.create
find = category_ui.find
list = category_ui.list
add = category_ui.add
remove = category_ui.remove

def _q_lookup (request, category_id):
    try:
        if category_id:
            return CategoryActions(int(category_id))
        else:
            raise TraversalError
    except:
        import traceback
        print traceback.print_exc()
        return not_found('category')
