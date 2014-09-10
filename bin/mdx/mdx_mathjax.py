import sys
import markdown
import os

class MathJaxPattern(markdown.inlinepatterns.Pattern):

    def __init__(self):
        # looks like this won't match the contents in `code` or ```code block```
        markdown.inlinepatterns.Pattern.__init__(self, r'(?<![\\])(\$\$?)(.+?)\2')

    def handleMatch(self, m):
        node = markdown.util.etree.Element('script')
        if len(m.group(2)) == 1:
            assert m.group(2) == '$';
            node.set('type', 'math/tex');
        else:
            assert m.group(2) == '$$';
            node.set('type', 'math/tex; mode=display');
        node.text = markdown.util.AtomicString(m.group(3))
        return node

class MathJaxPost(markdown.postprocessors.Postprocessor):
    def run(self, text):
        header = '''
<script type="text/x-mathjax-config">
MathJax.Hub.Config({
    config: ["MMLorHTML.js"],
    jax: ["input/TeX", "output/HTML-CSS", "output/NativeMML"],
    extensions: ["MathMenu.js", "MathZoom.js"],
    TeX: {
        equationNumbers: {autoNumber: "AMS"},
        extensions: ["AMSmath.js", "AMSsymbols.js"],
    },
    displayAlign: "left",
    "HTML-CSS": {
        styles: {".MathJax_Display": {"padding-left": "15px", "border-left":"4px solid #DDD"}}
    }
});
</script>
<script type="text/javascript" src="%s/bin/mathjax/MathJax.js"></script>
        ''' % os.environ['HOME']
        return header + text;

class MathJaxExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        # Needs to come before escape matching because \ is pretty important in LaTeX
        md.inlinePatterns.add('mathjax', MathJaxPattern(), '<escape')
        # reference OrderedDict for more
        md.postprocessors.add('mathjax', MathJaxPost(), '_end');

def makeExtension(configs=None):
    return MathJaxExtension(configs)


