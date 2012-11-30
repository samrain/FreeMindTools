#!/usr/bin/env python
# -*- encoding: utf-8 -*-

from xml.etree import ElementTree
import os
import conf4BlogListInGithub


class MMTransform():
    """freemind's file(.mm) transform tools"""

    def mm2md(self, mmFileContent):
        md = []
        mmtree = ElementTree.XML(mmFileContent)
        for node in mmtree.find('node').findall('node'):
            self._mm2SimpleMd(node, md)
        return '\r\n\r\n'.join(md)

    def mm2notes(self, mmFileContent):
        pass

    def mm2s5(self, mmFileContent):
        pass

    def _mm2SimpleMd(self, node, md, num=0):
        if node.get('TEXT'):
            branchcontent = []
            '''when find html tag,not transform'''
            if node.attrib['TEXT'].find('<'):
                if num == 1:
                    branchcontent = ['- ']
                elif num == 0:
                    branchcontent = ['# ']
                else:
                    branchcontent = ['        ']
            branchcontent.append(node.attrib['TEXT'])
            md.append(''.join(branchcontent))

            for childbranch in node.getchildren():
                self._mm2SimpleMd(childbranch, md, num + 1)


class MakeBlogInGithub():
    """make blog by markdown file in github.com"""
    def _getconf(self,mdFilename):
        return conf4BlogListInGithub.bloglist[mdFilename]

    def md2blog(self, md, mdFilename):
        config = self._getconf(mdFilename)
        prefix = []
        prefix.append('---')
        prefix.append('layout : '+config['layout'])
        prefix.append('category : ' + config['category'])
        prefix.append('tags : ' + '[' + ', '.join(config['tags'].split(',')) + ']')
        prefix.append('title : ' + config['title'])
        prefix.append('---')
        prefix.append('[思维导图文件下载]('+config['mmLink']+')')
        prefix.append(md)
        return '\r\n\r\n'.join(prefix)
         


def main():
    mmdir = '/home/rain/download'
    mddir = '/home/rain/doc/samrain.github.com/_posts'
    mblog = MakeBlogInGithub()
    mmFilename = '程序员的阅读清单.mm'
    mdFilename = mblog._getconf(mmFilename)['mdfname']

    mm = file(os.path.join(mmdir,mmFilename),'r')
    md = file(os.path.join(mddir,mdFilename),'w')
    transform = MMTransform()
    
    md.write(mblog.md2blog(transform.mm2md(mm.read()).encode('utf8'), mmFilename))
    # md.write(transform.mm2md(mm.read()).encode('utf8'))
    mm.close()
    md.close()

    

if __name__ == "__main__":
    main()