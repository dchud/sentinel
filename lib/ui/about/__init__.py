_q_exports = [
    'contact_us',
    'study_methodologies',
    'relevance',
    'tour',
    'disclaimer',
    'questionnaire',
    ]

import sys

from quixote import get_publisher

from canary.qx_defs import NotLoggedInError
from canary.qx_utils import MyStaticFile, load_static_exports
from canary.ui.pages import not_found
from canary.ui.about import about_ui


this_module = sys.modules[__name__]


contact_us = about_ui.contact_us
study_methodologies = about_ui.study_methodologies
relevance = about_ui.relevance
tour = about_ui.tour
disclaimer = about_ui.disclaimer
questionnaire = about_ui.questionnaire


# FIXME
config = get_publisher().config
#html_files = load_static_exports('/home/dlc33/projects/canary/lib/ui/html')
html_files = load_static_exports(config.static_html_dir)
for file, path in html_files:
    _q_exports.append(file)
    setattr(this_module, file, MyStaticFile(path, 
        mime_type='text/html', cache_time=30))


def _q_lookup (request, name=''):
    return not_found()


#def _q_access (request):
#    if request.get_path() in (
#        '/about/contact_us',
#        '/about/description',
#        '/about/disclaimer',
#        '/about/project_mission',
#        '/about/tour',
#        ):
#        return
#    try:
#        if request.session == None or request.session.user == None:
#            raise NotLoggedInError('You must first log in.')
#    except:
#        raise NotLoggedInError('You must first log in.')
