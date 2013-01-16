#!/usr/bin/env python
# encoding: utf-8

from __future__ import unicode_literals
from xml.etree import ElementTree
import os
import conf4BlogListInGithub
import sys



class MMTransform():
    """freemind's file(.mm) transform tools"""

    def mm2md(self, mmFileContent):
        md = []
        mmtree = ElementTree.XML(mmFileContent)
        for node in mmtree.find('node').findall('node'):
            self._mm2SimpleMd(node, md)
        linesep = os.linesep
        return linesep.join(md)

    def mm2textile(self, mmFileContent):
        textile = []
        mmtree = ElementTree.XML(mmFileContent)
        for node in mmtree.find('node').findall('node'):
            self._mm2SimpleTextile(node, textile)
        linesep = os.linesep
        return linesep.join(textile)

    def _mm2SimpleMd(self, node, md, num=1):
        if node.get('TEXT'):
            branchcontent = []
            i = 0
            j = 0
            linesep = ''
            if num < 3:
                linesep = os.linesep
                if node.getchildren():
                    branchcontent.append(linesep)
                    branchcontent.append('#')
                    while i < num:
                        branchcontent.append('#')
                        i = i+1
                    branchcontent.append(' ')
            else:
                if node.getchildren():
                    while j < num-3:
                        branchcontent.append(' ')
                        j = j+1
                    branchcontent.append('- ')
            self._dumpstr(node,md,branchcontent,linesep)
            self._recursionMm2SimpleMd(node,md,num)


    def _dumpstr(self, node, md, branchcontent, linesep=''):
        branchcontent.append(node.attrib['TEXT'])
        branchcontent.append(linesep)
        md.append(''.join(branchcontent))

    def _recursionMm2SimpleTextile(self,node,md,num):
        for childbranch in node.getchildren():
            self._mm2SimpleTextile(childbranch, md, num + 1)

    def _recursionMm2SimpleMd(self,node,md,num):
        for childbranch in node.getchildren():
            self._mm2SimpleMd(childbranch, md, num + 1)

    def _mm2SimpleTextile(self, node, md, num=1):
        if node.get('TEXT'):
            branchcontent = []
            i = 0
            linesep = ''
            if num < 3:
                linesep = os.linesep
                if node.getchildren():
                    branchcontent.append(os.linesep)
                    branchcontent.append('h')
                    branchcontent.append(str(num))
                    branchcontent.append('. ')
            else:
                if node.getchildren():
                    while i < num-2:
                        branchcontent.append('*')
                        i = i+1
                    branchcontent.append(' ')
            self._dumpstr(node,md,branchcontent,linesep)
            self._recursionMm2SimpleTextile(node,md,num)


class MakeBlogInGithub():
    """make blog by markdown file in github.com"""
    def _getconf(self,mdFilename):
        mdfile = 'default'
        if  conf4BlogListInGithub.bloglist.has_key(mdFilename):
            mdfile = mdFilename
        return conf4BlogListInGithub.bloglist[mdfile]

    def md2blog(self, md, mdFilename):
        config = self._getconf(mdFilename)
        prefix = []
        prefix.append('---')
        prefix.append('layout : '+config['layout'])
        prefix.append('category : ' + config['category'])
        prefix.append('tags : [' + ', '.join(config['tags'].split(',')) + ']')
        prefix.append('title : ' + config['title'])
        prefix.append('---')
        prefix.append('[思维导图文件下载]('+config['mmLink']+')')
        prefix.append(md)
        return os.linesep.join(prefix)

def usage():
    print '''
    '''


def main(argv):
    mmdir = '/home/rain/download'
    mddir = '/home/rain/download'
    # mddir = '/home/rain/doc/samrain.github.com/_posts'
    mblog = MakeBlogInGithub()
    mmFilename = 'MySQL主从同步.mm'
    if len(argv) > 1:
        mmFilename = argv[1].decode('utf8')
    textileFilename = 'textile.txt'
    mdFilename = mblog._getconf(mmFilename)['mdfname']

    mm = file(os.path.join(mmdir,mmFilename),'rb')
    md = file(os.path.join(mddir,mdFilename),'wb')
    # textile = file(os.path.join(mddir,textileFilename),'wb')
    
    transform = MMTransform()
    mdContent = transform.mm2md(mm.read())
    blogContent = mblog.md2blog(mdContent,mdFilename)
    md.write(blogContent.encode('utf8'))
    # textile.write(transform.mm2textile(mm.read()).encode('utf8'))
    mm.close()
    md.close()
    # textile.close()
    print os.path.join(mddir,mdFilename) + ' is OK!'

    

if __name__ == "__main__":
    main(sys.argv)