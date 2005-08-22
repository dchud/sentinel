# $Id$

_q_exports = [
    '_q_index',
    'find',
    'add',
    ]

from quixote.errors import TraversalError

from canary.ui.edit.study.risk_factor import risk_factor_ui
from canary.ui.edit.study.risk_factor.risk_factor_ui import RiskFactorActions

_q_index = risk_factor_ui._q_index
find = risk_factor_ui.find
add = risk_factor_ui.add


def _q_lookup (request, risk_factor_id):
    try:
        if not risk_factor_id == None:
            return RiskFactorActions(risk_factor_id)
        else:
            raise TraversalError
    except:
        return not_found('risk_factor')
