import os

from distutils import core
from quixote.qx_distutils import qx_build_py

kw = {'name': "canary",
    'version': "0.1",
    'description': "Beta version of the Canary Database Project site",
    'author': "Dan Chudnov",
    'author_email': "daniel.chudnov@yale.edu",
    'package_dir': {'canary': 'lib'},
    'packages': [
        'canary',
        'canary.ui',
        'canary.ui.about',
        'canary.ui.admin',
        'canary.ui.admin.dv_data',
        'canary.ui.admin.dv_data.group',
        'canary.ui.admin.dv_data.value',
        'canary.ui.admin.queue',
        'canary.ui.admin.session',
        'canary.ui.admin.source',
        'canary.ui.admin.term',
        'canary.ui.admin.user',
        'canary.ui.edit',
        'canary.ui.edit.batch',
        'canary.ui.edit.report',
        'canary.ui.html',
        'canary.ui.user',
        ],
    'data_files': [
        ('/home/dlc33/sites/canary_project/images', [
            'lib/ui/images/favicon.ico',
            'lib/ui/images/brynn_canaries_alpha_left.png', 
            'lib/ui/images/yusm_logo.png',
            ]),
        ],
    'cmdclass': {'build_py': qx_build_py}}


core.setup(**kw)
