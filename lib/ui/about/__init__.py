_q_exports = [
    'contact_us',
    ]

import sys

from canary.qx_utils import MyStaticFile, load_static_exports
from canary.ui.pages import not_found
from canary.ui.about import about_ui


this_module = sys.modules[__name__]


contact_us = about_ui.contact_us


# FIXME
#config = get_publisher().get_config()
#html_files = load_static_exports(config.static_html_dir)
html_files = load_static_exports('/home/dlc33/projects/canary/lib/ui/html')
for file, path in html_files:
    _q_exports.append(file)
    setattr(this_module, file, MyStaticFile(path,
                                            mime_type='text/html',
                                            cache_time=30))


def _q_lookup (request, name=''):
    return not_found()
