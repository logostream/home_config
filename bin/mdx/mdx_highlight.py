import sys
import markdown
import os

class HighLightPost(markdown.postprocessors.Postprocessor):
    def run(self, text):
        header = '''
<link rel="stylesheet" href="%s/bin/highlight.js/styles/default.css">
<script type="text/javascript" src="%s/bin/highlight.js/highlight.pack.js"></script>
<script type="text/javascript">hljs.initHighlightingOnLoad();</script>
        ''' % (os.environ['HOME'], os.environ['HOME'])
        return header + text;

class HighLightExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        # reference OrderedDict for more
        md.postprocessors.add('highlight', HighLightPost(), '_end');

def makeExtension(*args, **configs):
    assert len(args) == 0 or len(configs)==0
    if len(args):
        assert len(args) == 1
        print >> sys.stderr, "warning: older version of markdown_py api."
        configs = dict(args[0])

    return HighLightExtension(configs)
