# $Id$

_q_exports = [
    'contact_us',
    'study_methodologies',
    'linkage',
    'tour',
    'disclaimer',
    'questionnaire',
    ]

import sys

from quixote import get_publisher
from quixote.util import StaticFile

from canary.qx_defs import NotLoggedInError
from canary.qx_utils import MyStaticFile, load_static_exports
from canary.ui.pages import not_found
from canary.ui.about import about_ui


this_module = sys.modules[__name__]


contact_us = about_ui.contact_us
study_methodologies = about_ui.study_methodologies
linkage = about_ui.linkage
tour = about_ui.tour
disclaimer = about_ui.disclaimer
questionnaire = about_ui.questionnaire


config = get_publisher().config
html_files = load_static_exports(config.static_html_dir)
for file, path in html_files:
    _q_exports.append(file)
    setattr(this_module, file, MyStaticFile(path, 
        mime_type='text/html', cache_time=30))


def _q_lookup (request, name=''):
    if name == 'ecohealth-2005-animals.pdf':
        return StaticFile(config.static_html_dir + '/ecohealth-2005-animals.pdf', 
            mime_type='application/pdf')
    elif name == 'ecohealth-2004-outfoxing.pdf':
        return StaticFile(config.static_html_dir + '/ecohealth-2004-outfoxing.pdf', 
            mime_type='application/pdf')
    else:
        return not_found()

