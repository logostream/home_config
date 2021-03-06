import sys
import markdown
import os
import subprocess as sp

class AnchorPattern(markdown.inlinepatterns.Pattern):

    def __init__(self):
        # looks like this won't match the contents in `code` or ```code block```
        # wish list: wiki://, archwiki://, mygit://
        markdown.inlinepatterns.Pattern.__init__(self, r'\{\{#(.*?)\}\}')

    def handleMatch(self, m):
        # group start with 2:
        # https://pythonhosted.org/Markdown/extensions/api.html#inlinepatterns
        anchor = markdown.util.etree.fromstring('<a name="%s"/>' % m.group(2))
        return anchor

class AnchorExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns.add('anchor', AnchorPattern(), '<escape')

def makeExtension(*args, **configs):
    assert len(args) == 0 or len(configs)==0
    if len(args):
        assert len(args) == 1
        print >> sys.stderr, "warning: older version of markdown_py api."
        configs = dict(args[0])

    return AnchorExtension(configs)

