import sys
import markdown
import os
import subprocess as sp

class TOpenPattern(markdown.inlinepatterns.Pattern):

    def __init__(self):
        # looks like this won't match the contents in `code` or ```code block```
        # wish list: wiki://, archwiki://, mygit://
        markdown.inlinepatterns.Pattern.__init__(self, r'\{\{((repo|classic|mygit)://.*?)\}\}')

    def handleMatch(self, m):
        # group start with 2:
        # https://pythonhosted.org/Markdown/extensions/api.html#inlinepatterns
        p = sp.Popen(['topen', '-l', 'redir', m.group(2)], stdout=sp.PIPE)
        return p.communicate()[0].strip()

class TOpenExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        md.inlinePatterns.add('topen', TOpenPattern(), '<escape')

def makeExtension(*args, **configs):
    assert len(args) == 0 or len(configs)==0
    if len(args):
        assert len(args) == 1
        print >> sys.stderr, "warning: older version of markdown_py api."
        configs = dict(args[0])

    return TOpenExtension(configs)
