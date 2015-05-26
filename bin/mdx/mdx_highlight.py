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

def makeExtension(configs={}):
    return HighLightExtension(configs)




