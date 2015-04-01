#!/usr/bin/env python
# python 2 to 3 dealing with unicode....
import sys
import re
if sys.version_info.major == 2:
    from cStringIO import StringIO
    import codecs
    UNICODE = unicode
    def is_str_type(x):
        return isinstance(x, basestring)
    def is_int_type(x):
        return isinstance(x, int) or isinstance(x, long)
    def get_utf_8_string_io_writer():
        string_io = StringIO()
        wrapper = codecs.getwriter("utf8")(string_io)
        return string_io, wrapper
    def flush_utf_8_writer(wrapper):
        wrapper.reset()
    def reverse_dict(d):
        return {v: k for k, v in d.iteritems()}
else:
    from io import StringIO #pylint: disable=E0611,W0403
    UNICODE = str
    def is_str_type(x):
        return isinstance(x, str)
    def is_int_type(x):
        return isinstance(x, int)
    def get_utf_8_string_io_writer():
        string_io = StringIO()
        return string_io, string_io
    flush_utf_8_writer = lambda x: True
    def reverse_dict(d):
        return {v: k for k, v in d.items()}


def slugify(s):
    """Convert any string to a "slug", a simplified form suitable for filename and URL part.
     EXAMPLE: "Trees about bees" => 'trees-about-bees'
     EXAMPLE: "My favorites!" => 'my-favorites'
    N.B. that its behavior should match this client-side slugify function, so
    we can accurately "preview" slugs in the browser:
     https://github.com/OpenTreeOfLife/opentree/blob/553546942388d78545cc8dcc4f84db78a2dd79ac/curator/static/js/curation-helpers.js#L391-L397
    TODO: Should we also trim leading and trailing spaces (or dashes in the final slug)?
    """
    slug = s.lower()                        # force to lower case
    slug = re.sub('[^a-z0-9 -]', '', slug)  # remove invalid chars
    slug = re.sub('\s+', '-', slug)         # collapse whitespace and replace by -
    slug = re.sub('-+', '-', slug)          # collapse dashes
    if not slug:
        slug = 'untitled'
    return slug

def underscored2camel_case(v):
    '''converts ott_id to ottId.'''
    vlist = v.split('_')
    c = []
    for n, el in enumerate(vlist):
        if el:
            if n == 0:
                c.append(el)
            else:
                c.extend([el[0].upper(), el[1:]])
    return ''.join(c)
