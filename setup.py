# $Id$

import os

from distutils import core
from quixote.qx_distutils import qx_build_py

kw = {'name': "canary",
    'version': "0.2",
    'description': "Beta version of the Canary Database Project site",
    'author': "Dan Chudnov",
    'author_email': "daniel.chudnov@yale.edu",
    'package_dir': {'canary': 'canary'},
    'packages': [
        'canary',
        'canary.ui',
        'canary.ui.about',
        'canary.ui.admin',
        'canary.ui.admin.dv_data',
        'canary.ui.admin.dv_data.group',
        'canary.ui.admin.dv_data.value',
        'canary.ui.admin.queue',
        'canary.ui.admin.record',
        'canary.ui.admin.session',
        'canary.ui.admin.source',
        'canary.ui.admin.term',
        'canary.ui.admin.category',
        'canary.ui.admin.concept',
        'canary.ui.admin.user',
        'canary.ui.assistant',
        'canary.ui.edit',
        'canary.ui.edit.batch',
        'canary.ui.edit.study',
        'canary.ui.edit.study.exposure',
        'canary.ui.edit.study.risk_factor',
        'canary.ui.edit.study.outcome',
        'canary.ui.edit.study.species',
        'canary.ui.edit.study.location',
        'canary.ui.edit.study.methodology',
        'canary.ui.html',
        'canary.ui.user',
        ],
    'cmdclass': {'build_py': qx_build_py}}

core.setup(**kw)
