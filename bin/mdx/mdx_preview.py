import sys
import markdown
import os
import re

NAME_RE = re.compile(r'[^A-Z_a-z\u00c0-\u00d6\u00d8-\u00f6\u00f8-\u02ff\u0370-\u037d'
                     r'\u037f-\u1fff\u200c-\u200d\u2070-\u218f\u2c00-\u2fef'
                     r'\u3001-\ud7ff\uf900-\ufdcf\ufdf0-\ufffd'
                     r'\:\-\.0-9\u00b7\u0300-\u036f\u203f-\u2040]+')

def _handle_double_quote(s, t):
    k, v = t.split('=')
    return k, v.strip('"')

def _handle_single_quote(s, t):
    k, v = t.split('=')
    return k, v.strip("'")

def _handle_key_value(s, t):
    return t.split('=')

def _handle_word(s, t):
    if t.startswith('.'):
        return 'class', t[1:]
    if t.startswith('#'):
        return 'id', t[1:]
    return t, t

_scanner = re.Scanner([
    (r'[^ ]+=".*?"', _handle_double_quote),
    (r"[^ ]+='.*?'", _handle_single_quote),
    (r'[^ ]+=[^ ]*', _handle_key_value),
    (r'[^ ]+', _handle_word),
    (r' ', None)
])

def get_attrs(str):
    """ Parse attribute list and return a list of attribute tuples. """
    return _scanner.scan(str)[0]

def assign_attrs(elem, attrs):
    """ Assign attrs to element. """
    for k, v in attrs:
        # assign attr k with v
        # override class
        elem.set(sanitize_name(k), v)

def sanitize_name(name):
    """
    Sanitize name as 'an XML Name, minus the ":"'.
    See http://www.w3.org/TR/REC-xml-names/#NT-NCName
    """
    return NAME_RE.sub('_', name)

class PreviewPattern(markdown.inlinepatterns.Pattern):

    def __init__(self):
        # looks like this won't match the contents in `code` or ```code block```
        markdown.inlinepatterns.Pattern.__init__(self, r'\{\{!([^:]*?)\:(.*?)\}\}(?:\{\:(.*?)\})?')

    def handleMatch(self, m):
        # refer the https://pythonhosted.org/Markdown/extensions/attr_list.html
        # and source of markdown.extensions.attr_list
        # for tailing attr list format, which like {.class #id key=value key}
        title, url, attr_list = m.groups()[1:-1]
        node = markdown.util.etree.fromstring('''
        <a class="fancybox" title="{0}" href="{1}">
            <span class="preview-title">{0}</span>
            <img alt="{0}" src="{1}" class="preview-medium"/>
        </a>
        '''.format(title, url))
        if attr_list:
            attrs = get_attrs(attr_list)
            img = node.find('img');
            assign_attrs(img, attrs)
        return node

class PreviewPost(markdown.postprocessors.Postprocessor):
    def run(self, text):
        header = '''
<link rel="stylesheet" href="{0}/bin/fancybox/source/jquery.fancybox.css" type="text/css" media="screen" />
<script type="text/javascript" src="{0}/bin/fancybox/source/jquery.fancybox.pack.js"></script>
        '''.format(os.environ['HOME']) + '''
<script>
    $(document).ready(function() {
        $('.fancybox').fancybox({
            helpers: {
                title : {
                    type : 'float'
                }
            },
            scrolling: 'yes',
            autoSize: false,
            fitToView: false,
        });
    });
</script>
<style>
    .fancybox .preview-title {
        position: absolute;
        color: white;
        background: #000;
        opacity: .5;
        font-size: smaller;
        padding: 0px 5px 0px 5px;
        max-width: 160px
    }
    .fancybox img.preview-large {
        width:240px;
        margin-right:8px;
    }
    .fancybox img.preview-medium {
        width:160px;
        margin-right:8px;
    }
</style>
        ''';
        return header + text;

class PreviewExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns.add('preview', PreviewPattern(), '>escape')
        # reference OrderedDict for more
        md.postprocessors.add('preview', PreviewPost(), '_end');

def makeExtension(configs={}):
    return PreviewExtension(configs)

