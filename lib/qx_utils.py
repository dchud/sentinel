# Various utilities to help quixote along or otherwise simplify
# quixote usage.
#
# $Id$

import os
import re

from quixote.html import htmltext, TemplateIO
from quixote.http_response import Stream
from quixote.util import StaticFile

from canary.ui.pageframe import header, footer
from canary.utils import get_title_from_path


class MyStaticFile (StaticFile):
    """
    Enables templated rendering of static html text (also enables
    simple maintenance of static html files isolated by dir)
    """

    def orig__call__(self, request):
        contents = htmltext('')
        if self.mime_type == 'text/html':
            file_name = request.get_path()[1:]     # drop leading '/'
            contents += header(get_title_from_path(file_name))
            contents += htmltext(StaticFile.__call__(self, request))
            contents += footer()
        return contents

    def __call__(self, request):
        r = TemplateIO(html=0)
        file_name = request.get_path()[1:]     # drop leading '/'
        r += header(get_title_from_path(file_name))
        body = StaticFile.__call__(self, request)
        if isinstance(body, Stream):
            for hunk in body:
                r += hunk
        else:
            r += body
        r += footer()
        return r.getvalue()



def load_static_exports (dir, ext='.html'):
    """
    Load all static pages into a list for appending to _q_exports[]
    """
    files = os.listdir(dir)
    new_exports = []
    ext_length = 0 - len(ext)
    dot_to_underscore = re.compile('\.')
    for file in files:
        if file[ext_length:] == ext:
            new_file = dot_to_underscore.sub('_', file)
            # strip '.html' so the urls look prettier; other (mostly image) exts
            # aren't seen so don't botther usually
            if ext == '.html':
                new_file = new_file[:-5]
            # FIXME: hardcoded path separator
            new_exports.append((new_file, dir + '/' + file))
            #print 'appended', new_file

    return new_exports
