_q_exports = ['error',
              'search',
              'record',
              'heading',
              'journal',
              'year',
              'study_type',
              'canary_png',
              'about',
              'admin',
              'edit',
              'images',
              'user',
              ]

import sys

from quixote.errors import PublishError
from quixote.publish import get_publisher
from quixote.util import StaticFile

from canary.ui import record_ui, year_ui, heading_ui, journal_ui, study_type_ui
from canary.ui import about
from canary.ui import admin
from canary.ui import edit
from canary.ui import user
from canary.ui.browse import Browse
from canary.ui.pages import _q_index, _q_exception_handler, not_found
#from canary.pages import LoginForm, logout
from canary.qx_utils import MyStaticFile, load_static_exports
from canary.ui.search import search


# this is only here (?) because i was tweaking the image for fun; should
# actually be made available by the load_static_exports call for images below
#canary_png = StaticFile('/home/dlc33/projects/sentinel/sentineltestsite/images/brynn_canaries.png')

def error (request):
    raise PublishError(public_msg = "Oops, an error occured.")


this_module = sys.modules[__name__]

# FIXME
#config = get_publisher().get_config()
#html_files = load_static_exports(config.static_html_dir)
#html_files = load_static_exports('/home/dlc33/projects/sentinel/sentineltestsite/html')
#for file, path in html_files:
#    _q_exports.append(file)
#    setattr(this_module, file, MyStaticFile(path,
#                                            mime_type='text/html',
#                                            cache_time=30))

css_files = load_static_exports('/home/dlc33/projects/sentinel/sentineltestsite/html',
                                '.css')
for file, path in css_files:
    _q_exports.append(file)
    setattr(this_module, file, StaticFile(path, cache_time=60))

#for ext in ('.jpg', '.jpeg', '.gif', '.png'):
    # FIXME
    #image_files = load_static_exports(config.static_image_dir, ext)
#    image_files = load_static_exports('/home/dlc33/projects/sentinel/sentineltestsite/images', ext)
#    for file, path in image_files:
#        _q_exports.append(file)
#        setattr(this_module, file, StaticFile(path, cache_time=300))

# favorites icon (sigh...)
favicon = StaticFile('/home/dlc33/projects/sentinel/sentineltestsite/images/favicon.ico')


record = record_ui
year = year_ui
heading = heading_ui
journal = journal_ui
study_type = study_type_ui

def _q_lookup (request, name=''):
    if name == 'search':
        return search(request)
    elif name == 'browse':
        return Browse(request)
    elif name == 'favicon.ico':
        return favicon
    elif name == 'login':
    	return request.redirect('/user/login')
    elif name == 'logout':
    	return request.redirect('/user/logout')
    else:
        return not_found()
