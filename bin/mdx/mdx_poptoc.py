"""
Table of Contents Extension for Python-Markdown
* * *

(c) 2008 [Jack Miller](http://codezen.org)

Dependencies:
* [Markdown 2.1+](http://packages.python.org/Markdown/)

"""

from __future__ import absolute_import
from __future__ import unicode_literals
from markdown import Extension
from markdown.treeprocessors import Treeprocessor
from markdown.postprocessors import Postprocessor
from markdown.util import etree, parseBoolValue, AMP_SUBSTITUTE
from markdown.extensions.headerid import slugify, unique, itertext, stashedHTML2text
import re


def order_toc_list(toc_list):
    """Given an unsorted list with errors and skips, return a nested one.
    [{'level': 1}, {'level': 2}]
    =>
    [{'level': 1, 'children': [{'level': 2, 'children': []}]}]
    
    A wrong list is also converted:
    [{'level': 2}, {'level': 1}]
    =>
    [{'level': 2, 'children': []}, {'level': 1, 'children': []}]
    """
    
    def build_correct(remaining_list, prev_elements=[{'level': 1000}]):
        
        if not remaining_list:
            return [], []
        
        current = remaining_list.pop(0)
        if not 'children' in current.keys():
            current['children'] = []
        
        if not prev_elements:
            # This happens for instance with [8, 1, 1], ie. when some
            # header level is outside a scope. We treat it as a
            # top-level
            next_elements, children = build_correct(remaining_list, [current])
            current['children'].append(children)
            return [current] + next_elements, []
        
        prev_element = prev_elements.pop()
        children = []
        next_elements = []
        # Is current part of the child list or next list?
        if current['level'] > prev_element['level']:
            #print "%d is a child of %d" % (current['level'], prev_element['level'])
            prev_elements.append(prev_element)
            prev_elements.append(current)
            prev_element['children'].append(current)
            next_elements2, children2 = build_correct(remaining_list, prev_elements)
            children += children2
            next_elements += next_elements2
        else:
            #print "%d is ancestor of %d" % (current['level'], prev_element['level'])
            if not prev_elements:
                #print "No previous elements, so appending to the next set"
                next_elements.append(current)
                prev_elements = [current]
                next_elements2, children2 = build_correct(remaining_list, prev_elements)
                current['children'].extend(children2)
            else:
                #print "Previous elements, comparing to those first"
                remaining_list.insert(0, current)
                next_elements2, children2 = build_correct(remaining_list, prev_elements)
                children.extend(children2)
            next_elements += next_elements2
        
        return next_elements, children
    
    ordered_list, __ = build_correct(toc_list)
    return ordered_list


class TocTreeprocessor(Treeprocessor):
    
    # Iterator wrapper to get parent and child all at once
    def iterparent(self, root):
        for parent in root.getiterator():
            for child in parent:
                yield parent, child
    
    def add_anchor(self, c, elem_id): #@ReservedAssignment
        anchor = etree.Element("a")
        anchor.text = c.text
        anchor.attrib["href"] = "#" + elem_id
        anchor.attrib["class"] = "toclink"
        c.text = ""
        for elem in c.getchildren():
            anchor.append(elem)
            c.remove(elem)
        c.append(anchor)

    def add_permalink(self, c, elem_id):
        permalink = etree.Element("a")
        permalink.text = ("%spara;" % AMP_SUBSTITUTE
            if self.use_permalinks is True else self.use_permalinks)
        permalink.attrib["href"] = "#" + elem_id
        permalink.attrib["class"] = "headerlink"
        permalink.attrib["title"] = "Permanent link"
        c.append(permalink)
    
    def build_toc_etree(self, div, toc_list):
        # Add title to the div
        if self.config["title"]:
            header = etree.SubElement(div, "span")
            header.attrib["class"] = "toctitle"
            header.attrib["onclick"] = "togglePopToc()"
            header.text = self.config["title"]

        def build_etree_ul(toc_list, parent):
            ul = etree.SubElement(parent, "ul")
            for item in toc_list:
                # List item link, to be inserted into the toc div
                if item['level'] > int(self.config['maxlevel']):
                    continue;
                li = etree.SubElement(ul, "li")
                link = etree.SubElement(li, "a")
                link.text = item.get('name', '')
                link.attrib["href"] = '#' + item.get('id', '')
                if item['children']:
                    build_etree_ul(item['children'], li)
            return ul
        
        node = build_etree_ul(toc_list, div)
        node.attrib["id"] = "toc_list"
        return node

    marker_ptn = re.compile(r"\{TOC\}(?:\((.+?)\))?");
    def run(self, doc):

        wrapper = etree.Element("div")
        wrapper.attrib["class"] = "toc_wrapper"
        div = etree.SubElement(wrapper, "div")
        div.attrib["class"] = "toc"
        header_rgx = re.compile("[Hh][123456]")
        
        self.use_anchors = parseBoolValue(self.config["anchorlink"])
        self.use_permalinks = parseBoolValue(self.config["permalink"], False)
        if self.use_permalinks is None:
            self.use_permalinks = self.config["permalink"]
        
        # Get a list of id attributes
        used_ids = set()
        for c in doc.getiterator():
            if "id" in c.attrib:
                used_ids.add(c.attrib["id"])

        toc_list = []
        marker_found = False
        for (p, c) in self.iterparent(doc):
            text = ''.join(itertext(c)).strip()
            if not text:
                continue

            # To keep the output from screwing up the
            # validation by putting a <div> inside of a <p>
            # we actually replace the <p> in its entirety.
            # We do not allow the marker inside a header as that
            # would causes an enless loop of placing a new TOC 
            # inside previously generated TOC.
            marker_mth = self.marker_ptn.match(c.text.strip()) if c.text else None;
            if c.text and marker_mth and \
               not header_rgx.match(c.tag) and c.tag not in ['pre', 'code']:
                for i in range(len(p)):
                    if p[i] == c:
                        p[i] = wrapper
                        break
                if marker_mth.group(1):
                    self.config["title"] = marker_mth.group(1);
                marker_found = True
                            
            if header_rgx.match(c.tag):
                
                # Do not override pre-existing ids 
                if not "id" in c.attrib:
                    elem_id = stashedHTML2text(text, self.markdown)
                    elem_id = unique(self.config["slugify"](elem_id, '-'), used_ids)
                    c.attrib["id"] = elem_id
                else:
                    elem_id = c.attrib["id"]

                tag_level = int(c.tag[-1])
                
                toc_list.append({'level': tag_level,
                    'id': elem_id,
                    'name': text})

                if self.use_anchors:
                    self.add_anchor(c, elem_id)
                if self.use_permalinks:
                    self.add_permalink(c, elem_id)
                
        toc_list_nested = order_toc_list(toc_list)
        self.build_toc_etree(div, toc_list_nested)
        prettify = self.markdown.treeprocessors.get('prettify')
        if prettify: prettify.run(wrapper)
        if not marker_found:
            # serialize and attach to markdown instance.
            toc = self.markdown.serializer(wrapper)
            for pp in self.markdown.postprocessors.values():
                toc = pp.run(toc)
            self.markdown.toc = toc

class TocPost(Postprocessor):
    def run(self, text):
        header = '''
<style>
div.toc_wrapper{position:fixed;z-index:100;margin-left:70%;margin-top:30px;height:700px;overflow:auto;}
div.toc {background:#E6F1F6;border:1px solid #B7C7CF;padding:0.5em;border-radius:3px}
div.toc .toctitle{display:block;margin:0.5em;text-align:center;font-weight:bold}
div.toc a{display:block;margin-right:1em;}
</style>
<script type="text/javascript">
    var g_displayPopToc = true;
    function togglePopToc()
    {
        g_displayPopToc = !g_displayPopToc;
        document.getElementById("toc_list").style.display = g_displayPopToc? "" : "none";
    }
</script>
        '''
        return header + text;

class TocExtension(Extension):
    
    TreeProcessorClass = TocTreeprocessor
    
    def __init__(self, configs=[]):
        self.config = { "slugify" : [slugify,
                            "Function to generate anchors based on header text-"
                            "Defaults to the headerid ext's slugify function."],
                        "title" : [None,
                            "Title to insert into TOC <div> - "
                            "Defaults to None"],
                        "anchorlink" : [0,
                            "1 if header should be a self link"
                            "Defaults to 0"],
                        "permalink" : [0,
                            "1 or link text if a Sphinx-style permalink should be added",
                            "Defaults to 0"],
                        "maxlevel" : [1000,
                            "max level of head to generate"],
                       }

        for key, value in configs:
            self.setConfig(key, value)

    def extendMarkdown(self, md, md_globals):
        tocext = self.TreeProcessorClass(md)
        tocext.config = self.getConfigs()
        # Headerid ext is set to '>prettify'. With this set to '_end',
        # it should always come after headerid ext (and honor ids assinged 
        # by the header id extension) if both are used. Same goes for 
        # attr_list extension. This must come last because we don't want
        # to redefine ids after toc is created. But we do want toc prettified.
        md.treeprocessors.add("toc", tocext, "_end")
        md.postprocessors.add("toc", TocPost(), "_end")


def makeExtension(configs={}):
    return TocExtension(configs=configs)
