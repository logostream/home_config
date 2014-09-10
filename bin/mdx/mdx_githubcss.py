import sys
import markdown
import os

class GithubCssPost(markdown.postprocessors.Postprocessor):
    def run(self, text):
        header = '''
        <link rel="stylesheet" href="%s/bin/github-markdown-css/github-markdown.css">
        ''' % os.environ['HOME']
        return header + "<article class='markdown-body'>%s</arcicle>" % text;

class GithubCssExtension(markdown.Extension):
    def extendMarkdown(self, md, md_globals):
        # reference OrderedDict for more
        md.postprocessors.add('githubcss', GithubCssPost(), '_end');

def makeExtension(configs=None):
    return GithubCssExtension(configs)



