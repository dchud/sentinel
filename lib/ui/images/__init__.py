_q_exports = ['_q_index',
              ]

import sys

from quixote.errors import PublishError
from quixote.publish import get_publisher
from quixote.util import StaticFile

from canary.ui.pages import _q_index, _q_exception_handler, not_found
from canary.qx_utils import load_static_exports



this_module = sys.modules[__name__]

# FIXME
#config = get_publisher().get_config()

for ext in ('.jpg', '.jpeg', '.gif', '.png'):
    # FIXME
    #image_files = load_static_exports(config.static_image_dir, ext)
    image_files = load_static_exports('/home/dlc33/projects/sentinel/sentineltestsite/images', ext)
    for file, path in image_files:
	_q_exports.append(file)
	setattr(this_module, file, StaticFile(path, cache_time=300))


# FIXME: do we really want this here?
def _q_lookup (request, name=''):
    return not_found()
