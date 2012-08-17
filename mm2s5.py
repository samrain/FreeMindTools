#!/usr/bin/env python
# -*- encoding: latin1 -*-
#
# Copyright 2010 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Patched by Iceberg Luo to support FreeMind 0.9.x    2009

"""Convert a Memory Map File into an S5 presentation

If you create a mind map with FreeMind the title of the mind-map (center circle)
will be the title of the slide.

A top level node called "__meta__" can be used to set the metadata for
the presentation.  The immediate children are keys and it's first child is a value.
  title: Title of presentation, not needed since I get it from the top node
  subtitle: Witty subtitle of the presentation
  author: You probably want to change this.
  company: And this
  template: which subdirectory to use under the "ui" directory, 'default' is default
  presdate: Date of the presentation
  content_type: defaults to 'application/xhtml+xml; charset=utf-8'
  header:
  footer:


If the first character of the first line is a '<' then we won't add
the the <ul> list to the markup.

The icons can have special meaning:
  The "Not OK" icon the slide will be skipped.
  The "OK' icon will have no additional markup on the text (i.e. no <ul>)
  The "Stop" icon will build the slide one line at a time.
  The "Priority 1" icon will use an ordered list
"""

__author__ = 'scott@forusers.com (Scott Kirkwood)'
__version__ = '0.2.3'

import sys
import optparse
from xml.etree import ElementTree
import codecs

class Mm2S5:
  def __init__(self):
    self.et_in = None
    self.meta = {
      'title' : 'Title',
      'subtitle': '',
      'author' : """The Author.
        You don't need to change this code.
        Instead, you should write a __meta__ node in your mm file.
        Refer to the docstring for details.""",
      'company' : 'See above',
      'template' : 'default',
      'presdate' : 'Today',
      'content_type' : 'application/xhtml+xml; charset=utf-8',
      'header' : '',
      'footer' : None,
      'generator' : 'mm2s5.py',
    }

  def open(self, infilename):
    """ Open the .mm file and create a S5 file as a list of lines """
    infile = file(infilename).read()
    self.et_in = self.xmlparse(infile)
    lines = self.convert()
    return lines

  def write(self, outfilename, lines):
    """ Write out the lines, written as a convenience function

    Writing out the HTML in correct UTF-8 format is a little tricky."""

    outfile = codecs.open(outfilename, 'w', 'utf-8')
    outfile.write(u'\n'.join(lines))
    outfile.close()

  def xmlparse(self, text):
    """ import the XML text into self.et_in  """
    return ElementTree.XML(text)

  def convert(self):
    """ Convert self.et_in to a HTML as a list of lines in S5 format """

    self._grab_meta()

    lines = []
    lines.append("""<?xml version="1.0" encoding="UTF-8"?>""")
    lines.append("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
      "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
        <html xmlns="http://www.w3.org/1999/xhtml">""")
    lines.append('<head>')
    lines.append("""
      <title>%(title)s</title>
      <meta name="version" content="S5 1.1" />
      <meta name="generator" content="%(generator)s" />
      <meta name="presdate" content="%(presdate)s" />
      <meta name="author" content="%(author)s" />
      <meta name="company" content="%(company)s" />
      <meta http-equiv="Content-type" content="%(content_type)s" />
      <!-- S5 format see Eric A. Meyer, http://meyerweb.com/eric/tools/s5/ -->
      <link rel="stylesheet" href="ui/%(template)s/slides.css" type="text/css"
        media="projection" id="slideProj" />
      <link rel="stylesheet" href="ui/%(template)s/outline.css" type="text/css" x
        media="screen" id="outlineStyle" />
      <link rel="stylesheet" href="ui/%(template)s/print.css" type="text/css"
        media="print" id="slidePrint" />
      <link rel="stylesheet" href="ui/%(template)s/opera.css" type="text/css"
        media="projection" id="operaFix" />
      <script src="ui/%(template)s/slides.js" type="text/javascript"></script>
      """ % self.meta)
    lines.append('</head>')
    lines.append('<body>')
    lines.append("""<div class="layout">
        <div id="controls"><!-- DO NOT EDIT --></div>
        <div id="currentSlide"><!-- DO NOT EDIT --></div>
        <div id="header">%(header)s</div>
        <div id="footer">%(footer)s</div>
      </div>""" % self.meta)

    lines.append('<div class="presentation">')

    presentation = self.et_in.find('node')
    lines.append('  <div class="slide">')
    lines.append('    <h1>%s</h1>' % (self.meta['title']))
    lines.append('    <h2>%s</h2>' % (self.meta['subtitle']))
    lines.append('    <h3>%s</h3>' % (self.meta['author']))
    lines.append('    <h4>%s</h4>' % (self.meta['company']))
    lines.append('  </div>')

    for page in presentation.findall('node'):
      # Skip the __meta__ node, if any
      if page.attrib['TEXT'] == '__meta__':
        continue

      attribs = self._get_list_attributes(page)
      if 'skip' in attribs:
        continue

      lines.append('  <div class="slide">')
      lines.append('    <h1>%s</h1>' % (page.attrib['TEXT']))
      lines.append('    <div class="slidecontent">')
      self._doList(lines, page, 0)
      lines.append('    </div>') # content
      lines.append('  </div>') # slide

    lines.append('</div>') # Presentation
    lines.append('</body>')
    lines.append('</html>')
    return lines

  def _get_list_attributes(self, page):
    """ If there's a special icon, return some attributes
      Also, handle HTML markup a bit differently
    """
    ret = {}

    for icon in page.findall('icon'):
      icon_type = icon.attrib['BUILTIN']
      if icon_type == 'button_ok':
        ret['no_ul'] = True
      elif icon_type == "stop": # Stop light icon
        ret['ul_class'] = "incremental"
      elif icon_type == 'button_cancel':
        ret['skip'] = True
      elif icon_type == 'full-1':
        ret['ol'] = True

    # Special case, if the first node starts with <
    # Then we'll assume markup and not do
    # a <ul> etc.
    node = page.find('node')
    if node != None and \
      (node.attrib['TEXT'].startswith('<') or
      node.attrib['TEXT'] == '__table__'):
      ret['no_ul'] = True

    return ret

  def _grab_meta(self):
    """ Grab a "page" called __meta__, if any """

    titles = self.et_in.find('node').attrib['TEXT'].split('\n')

    self.meta['title'] = titles[0]
    if len(titles) > 1:
      self.meta['subtitle'] = titles[1]
    for cur_node in self.et_in.getiterator('node'):
      if cur_node.attrib.get('TEXT') == '__meta__': # Probably due to FreeMind 0.9, we might not have TEXT attribute
        for sub_attrib in cur_node.findall('node'):
          key = sub_attrib.attrib['TEXT']
          sub_value = sub_attrib.find('node')
          value = sub_value.attrib['TEXT']
          self.meta[key] = value

    if self.meta['footer'] == None:
      self.meta['footer'] = '<h1>%(company)s</h2><h2>%(title)s</h2>' % self.meta

  def _doList(self, lines, sub, depth):
    """ Recurse this list of items

    Code is a little messier than I would like """

    if sub == None or len(sub) == 0:
      return

    attribs =  self._get_list_attributes(sub)

    if 'ul_class' in attribs:
      ul_class = ' class="%s"' % (attribs['ul_class'])
    else:
      ul_class = ''
    indent = '  ' * (depth + 2)
    if 'no_ul' not in attribs:
      if 'ol' in attribs:
        lines.append('%s<ol%s>' % (indent, ul_class,))
        end = '%s</ol>' % (indent)
      else:
        lines.append('%s<ul%s>' % (indent, ul_class,))
        end = '%s</ul>' % (indent)
    else:
      end = None

    for line in sub.findall('node'):
      text = line.attrib.get('TEXT') # Probably due to FreeMind 0.9, we might not have TEXT attribute
      if not text: # FreeMind 0.9 's HTML node stores text in html format
        p = (line
          ._children[0]#Element richcontent
          ._children[0]#Element html
          ._children[1]#Element body
          ._children[0])#Element p
        if p.text:
          text=p.text
        elif p.tag == 'img':
          text='<img src="%s">' % p.get('src')
      if text == '__table__':
        lines += self._insert_table(text, line, depth)
      else:
        lines += self._insert_line_item(text, line, depth, attribs)
        self._doList(lines, line, depth + 1)

    if end:
      lines.append(end)

  def _insert_line_item(self, text, line, depth, attribs):
    """ Insert a line item <li></li> """

    indent = '  ' * (depth + 3)
    lines = []
    if not text:
      return lines
    text = text.replace('<html>', '')
    if 'LINK'in line.attrib:
      text = '<a href="%s">%s</a>' % (line.attrib['LINK'], text)

    if 'no_ul' not in attribs:
      text = text.replace('\n', '<br/>\n')
      lines.append('%s<li>%s</li>' % (indent, text))
    else:
      lines.append('%s' % (text))

    return lines

  def _insert_table(self, unused_text, line, depth):
    """ If we get a special node called __table__ insert the children
    as rows in a table (descendants are columns in that row) """

    lines = []
    indent = '  ' * (depth + 2)
    table = line
    lines.append('%s<table>' % (indent))
    for row in table.findall('node'):
      lines.append('%s  <tr>' % (indent))
      for col in row.getiterator('node'):
        lines.append('%s    <td>%s</td>' % (indent, col.attrib['TEXT']))

      lines.append('%s  </tr>' % (indent))
    lines.append('%s</table>' % (indent))
    return lines

def show_version():
    print 'mm2s5 version %s.' % __version__
    print 'Written by %s' % __author__

def parse_command_line():
    usage = """%prog <mmfile> [<htmloutput>]
Create a FreeMind (.mm) document (see http://freemind.sourceforge.net/wiki/index.php/Main_Page)
the main node will be the title page and the lower nodes will be pages.
"""
    parser = optparse.OptionParser(usage)
    parser.add_option('-v', '--version', dest='version', action='store_true',
                      help='Show version information and exit.')
    (options, args) = parser.parse_args()
    if options.version:
        show_version()
        sys.exit(0)
    if len(args) == 0:
        parser.print_usage()
        sys.exit(-1)

    infile = args[0]
    if not infile.endswith('.mm'):
        print "Input file must end with '.mm'"
        parser.print_usage()
        sys.exit(-1)

    if len(args) == 1:
        outfile = infile.replace('.mm', '.html')
    elif len(args) == 2:
        outfile = args[1]
    else:
        parser.print_usage()
        sys.exit(-1)

    mm2s5 = Mm2S5()
    lines = mm2s5.open(infile)
    mm2s5.write(outfile, lines)

if __name__ == "__main__":
    parse_command_line()
