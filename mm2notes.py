#!/usr/bin/env python
#-*- coding:utf-8 -*-

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

"""Convert a Memory Map File into Meeting Notes."""

__author__ = 'samrainhan@google.com (Sam Han)'
__version__ = '0.1'

import sys
from optparse import OptionParser
try:
    from xml.etree.ElementTree import XML
except ImportError:
    from elementtree.ElementTree import XML

import codecs
import cgi
import time

class Mm2Notes:
    def __init__(self):
        self.et_in = None
        self.as_html = True
        self.title_text = ''
        self.full_html = True
        self.order_by_time = False

    def set_order_by_time(self, order_by_time):
        self.order_by_time = order_by_time

    def open(self, infilename):
        """ Open the .mm file and create a notes as a list of lines """
        infile = file(infilename).read()
        self.et_in = self.xmlparse(infile)
        lines = self.convert()
        return lines

    def write(self, outfile, lines):
        """ Write out the lines, written as a convenience function
        """
        outfile.write(u'\n'.join(lines))
        outfile.write('\n')


    def xmlparse(self, text):
        """ import the XML text into self.et_in  """
        return  XML(text)

    def convert(self):
        """ Convert self.et_in to a HTML as a list of lines in S5 format """

        topic = []
        attendees = []
        discussed = []
        actionitems = []
        meetingday = []
        self.title_text = self.et_in.find('node').attrib['TEXT']

        presentation = self.et_in.find('node')

        for node in presentation.findall('node'):
            node_name = node.attrib['TEXT']
            if self.starts_with(node_name, ['attendee', 'people', u'人员']):
                attendees = self.handleAttendees(node)
            elif self.starts_with(node_name, ['topic', 'subject', u'议题']):
                topic = self.handleTopic(node)
            elif self.starts_with(node_name, ['discus', 'minutes',
                    'meeting', 'notes', u'记录']):
                discussed = self.handleDiscussed(node)
            elif self.starts_with(node_name, ['action', 'a.i', 'ai', u'下一步工作']):
                actionitems = self.handleActionItems(node)
            elif self.starts_with(node_name, [u'时间']):
                meetingday = self.handleMeetingDay(node)
            elif self.starts_with(node_name, [u'地点']):
                meetinglocation = self.handleMeetingLocation(node)
        return self.html_wrapper(self.handleTitle() + meetingday + meetinglocation + attendees + topic
                + actionitems + discussed)

    def starts_with(self, name, list):
        for item in list:
            if name.lower().startswith(item):
                return True
        return False

    def html_wrapper(self, list):
      head = [
          '<?xml version="1.0" encoding="UTF-8"?>',
          '<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" ',
          '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">',
          '<html xmlns="http://www.w3.org/1999/xhtml">',
          '<head>',
          '<title>%s</title>' % (self.title_text),
          '</head>',
          '<body>',
      ]
      tail = [
          '</body>',
          '</html>'
      ]
      if self.full_html:
          return head + list + tail
      else:
          return list

    def handleAttendees(self, node):
        topnodes = node.findall('node')
        # find the maximum depth in the attendee lists

        mxd = self.maxdepth(topnodes)
        if mxd >= 3:
            # assume entity / attendee / email and ignore anything else
            names = self.threeLevelAttendees(node)
        elif mxd == 2:
            # assume attendee / email
            names = self.twoLevelAttendees(node)
        elif mxd == 1:
            names = [x.attrib['TEXT'] for x in topnodes]
        else:
            # no names
            names = []
        return [self.open_close('b', u'人员: ') + ', '.join(names) + self.nl()]

    def maxdepth(self, nodes):
       """Returns the maximum depth of tree for the supplied list of nodes."""
       if not nodes:
         # empty list, zero depth
         return 0
       else:
         depths = [self.maxdepth(x.findall('node')) for x in nodes]
         return 1 + max(depths)

    def twoLevelAttendees(self, node):
        """ Top node is the person's name,
        If there's a sub node, it's the email, or something like that
        """
        names = []
        for line in node.findall('node'):
            fullname = line.attrib['TEXT']
            emailnodes = line.findall('node')

            if emailnodes:
                email = emailnodes[0].attrib['TEXT']
            else:
                email = ''
            if len(email) > 0:
                names.append('%s (%s)' % (fullname, email))
            else:
                names.append('%s' % (fullname))

        return names

    def threeLevelAttendees(self, node):
        """ Here the top node is the location, the child nodes are the people """

        locations= []
        for location in node.findall('node'):
            loc_name = location.attrib['TEXT']
            names = self.twoLevelAttendees(location)
            locations.append("%s [%s]" % (loc_name, ', '.join(names)))

        return locations

    def handleTopic(self, node):
        text = []
        for line in node.findall('node'):
            text.append(line.attrib['TEXT'])

        return [self.open_close('b', u'议题: ') + ' '.join(text) + self.nl()]

    def handleMeetingDay(self, node):
        text = []
        for line in node.findall('node'):
            text.append(line.attrib['TEXT'])

        return [self.open_close('b', u'时间: ') + ' '.join(text) + self.nl()]


    def handleMeetingLocation(self, node):
        text = []
        for line in node.findall('node'):
            text.append(line.attrib['TEXT'])

        return [self.open_close('b', u'地点: ') + ' '.join(text) + self.nl()]


    def nl(self):
        if self.as_html:
            return '<br/>\n'
        return '\n'

    def handleDiscussed(self, node):
        people_time = []
        for sub in node.findall('node'):
            name = sub.attrib['TEXT']
            for subsub in sub.findall('node'):
                cur = []
                time = int(subsub.attrib['CREATED'])
                self.nest_text(subsub, cur)
                text = '\n'.join(cur)
                if len(text) > 0:
                    people_time.append((time, name, text))

        if self.order_by_time:
            people_time.sort()
        self.start_time = people_time[0][0]
        last_name = None

        ret = [self.title(u'记录')]
        self.open_tag('ul', ret)
        for curtime, name, text in people_time:
            if name != last_name:
                last_name = name
                if len(ret) > 2:
                    self.close_tag('ul', ret)
                    self.close_tag('li', ret)
                self.open_tag('li', ret)
                if self.order_by_time:
                    ret.append(self.show_user_time(name, curtime))
                else:
                    ret.append(name)
                self.open_tag('ul', ret)

            self.open_tag('li', ret)
            ret.append(text)
            self.close_tag('li', ret)

        self.close_tag('ul', ret)
        self.close_tag('li', ret)
        self.close_tag('ul', ret)

        return ret

    def handleTitle(self):
        if self.as_html:
            return ["<h3>%s</h3>" % (self.title_text)]
        return ["%s" %  (self.title_text)]

    def handleActionItems(self, node):
        ret = []
        ret.append(self.title(u'下一步工作'))


        self.open_tag('ul', ret)
        for sub in node.findall('node'):
            self.open_tag('li', ret)
            self.nest_text(sub, ret)
            self.close_tag('li', ret)

        self.close_tag('ul', ret)
        return ret

    def show_user_time(self, name, curtime):
        return '%s (%s)' % (name, self.format_time(curtime))

    def nest_text(self, node, ret):
        ret.append(self.escape(node.attrib['TEXT']))
        subnodes = node.findall('node')

        if len(subnodes) > 0:
            self.open_tag('ul', ret)
            for sub in node.findall('node'):
                self.open_tag('li', ret)
                self.nest_text(sub, ret)
                self.close_tag('li', ret)

            self.close_tag('ul', ret)

    def title(self, name):
        if self.as_html:
            return '<b>%s</b><br/>' % (name)
        return name

    def open_tag(self, tag, list):
        if self.as_html:
            list.append('<%s>' % tag)

    def close_tag(self, tag, list):
        if self.as_html:
            list.append('</%s>' % tag)

    def open_close(self, tag, text, list = None):
        if list == None:
            return self._open_close(tag, text)
        list.append(self._open_close(tag, text))

    def _open_close(self, tag, text):
        if self.as_html:
            return '<%s>%s</%s>' % (tag, cgi.escape(text), tag)
        else:
            return text

    def escape(self, text):
        if self.as_html:
            return cgi.escape(text)
        return text

    def format_time(self, curtime):
        timesecs = (curtime - self.start_time) / (1000)

        minutes = timesecs // 60
        sec = timesecs % 60

        if minutes == 0 and sec == 0:
            t = time.localtime(self.start_time / 1000.0)
            tzn = time.tzname[0]
            return '%02d:%02d:%02d %s'  % (t[3], t[4], t[5], tzn)
        if minutes == 0:
            return '%d secs' % (sec)
        if sec == 0:
            return '%d min' % (minutes)
        return '%d min %d sec' % (minutes, sec)

def parse_command_line():
    usage = """%prog <mmfile> -o [<htmloutput>]
Create a FreeMind (.mm) document (see http://freemind.sourceforge.net/wiki/index.php/Main_Page)
the main node will be the title page and the lower nodes will be pages.
"""
    parser = OptionParser(usage)
    parser.add_option('-o', '--output', dest="outfile")
    parser.add_option('-m', '--minutes', dest="order_by_time",
        action='store_true',
        help="Order the minutes by time and show the time")
    (options, args) = parser.parse_args()
    if len(args) == 0:
        parser.print_usage()
        sys.exit(-1)

    infile = args[0]
    if not infile.endswith('.mm'):
        print "Input file must end with '.mm'"
        parser.print_usage()
        sys.exit(-1)

    outfile = sys.stdout
    if options.outfile:
        # Writing out the HTML in correct UTF-8 format is a little tricky.
        print "Outputting to '%s'" % (options.outfile)
        outfile = codecs.open(options.outfile, 'w', 'utf-8')

    mm2notes = Mm2Notes()
    lines = mm2notes.open(infile)
    mm2notes.set_order_by_time(options.order_by_time)

    mm2notes.write(outfile, lines)

if __name__ == "__main__":
    parse_command_line()
