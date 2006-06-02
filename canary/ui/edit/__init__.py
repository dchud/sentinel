# $Id$

_q_exports = [
    '_q_index',
    'batch',
    'find',
    'pubmed',
    'study',
    'human',
    'auto_human',
    ]


from quixote.errors import AccessError, PublishError, TraversalError

from canary.qx_defs import NotLoggedInError
from canary.ui.pageframe import header, footer
from canary.ui.pages import not_found
from canary.ui.edit import batch, edit_ui, study, human

_q_index = edit_ui._q_index
find = edit_ui.find
pubmed = edit_ui.pubmed
auto_human = edit_ui.auto_human

def _q_access (request):
    if request.session.user == None:
        raise NotLoggedInError('Authorized access only.')
    if not (request.session.user.is_editor):
        raise AccessError("You don't have access to this page.")

