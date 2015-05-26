import sys
import markdown
import os

class GithubCssPost(markdown.postprocessors.Postprocessor):
    def run(self, text):
        header = '''
        <link rel="stylesheet" href="{0}/bin/github-markdown-css/github-markdown.css">
        <script type="text/javascript" src="{0}/bin/jquery.min.js"></script>
        '''.format(os.environ['HOME']) + '''
            <style>
                .markdown-body {
                    min-width: 200px;
                    max-width: 790px;
                    margin: 0 auto;
                    margin-left: 20%;
                    padding: 30px;
                }
                .markdown-body p {
                    margin-bottom: 6px;
                    line-height: 1.5;
                }
                .markdown-body dl dt {
                    margin-top: 8px
                }
                .markdown-body dl dd {
                    margin-bottom: 8px
                }
                .markdown-body .container {
                    padding: 0 15px;
                    border-left: 4px solid#ddd;
              }
            </style>
        ''';
        return header + "<article class='markdown-body'>%s</arcicle>" % text;

class GithubCssExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        # reference OrderedDict for more
        md.postprocessors.add('githubcss', GithubCssPost(), '_end');

def makeExtension(*args, **configs):
    assert len(args) == 0 or len(configs)==0
    if len(args):
        assert len(args) == 1
        print >> sys.stderr, "warning: older version of markdown_py api."
        configs = dict(args[0])

    return GithubCssExtension(configs)
