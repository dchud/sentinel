_q_exports = ['_q_index',
              'login',
              'logout',
              ]

from quixote.errors import TraversalError

from canary.ui.pages import not_found
from canary.ui.user import user_ui

_q_index = user_ui._q_index
login = user_ui.login
logout = user_ui.logout


def _q_lookup (request, action):
    try:
        if action == 'login':
            if request.session.user == None:
                return login(request)
            else:
                request.redirect('/user')
        elif action == 'logout':
            return logout(request)
        else:
            raise TraversalError

    except:
        return not_found('user')
