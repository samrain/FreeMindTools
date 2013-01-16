#!/usr/bin/env python
# encoding: utf-8

from __future__ import unicode_literals
from xml.etree import ElementTree
import os
import sys
import yaml



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
    def _getconfFromPy(self,mdFilename):
        mdfile = 'default'
        if  conf4BlogListInGithub.bloglist.has_key(mdFilename):
            mdfile = mdFilename
        return conf4BlogListInGithub.bloglist[mdfile]

    def _getconfFromYaml(self,configFilename,mdFilename):
        mdfile = 'default'
        config = file(configFilename,'rb')
        config.close()
        if  config.has_key(mdFilename):
            mdfile = mdFilename
        return config[mdfile]

    def md2blog(self, md, config, mdFilename):
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

def getconf(conf_dic, title):
    key = 'default.mm'
    if conf_dic.has_key(title):
        key = title
    return conf_dic[key]


def main(argv):
    confile = file('app.yaml','rb')
    config = yaml.load(confile)
    dirconf = 'file_dir'
    mmdir = config[dirconf]['mm']
    mddir = config[dirconf]['md']

    mblog = MakeBlogInGithub()
    transform = MMTransform()

    if len(argv) > 1:
        file_list = [argv[1]]
    else:
        file_list = [f_name for f_name in os.listdir(mmdir) if f_name.decode('utf8').endswith('mm')]

    for f_in_name in file_list:
        conf = getconf(config,f_in_name.decode('utf8'))
        mmFilename = f_in_name
        mdFilename = conf['mdfname']
        mm = file(os.path.join(mmdir,mmFilename),'rb')
        md = file(os.path.join(mddir,mdFilename),'wb')
        mdContent = transform.mm2md(mm.read())
        blogContent = mblog.md2blog(mdContent,conf,mdFilename)
        md.write(blogContent.encode('utf8'))
        mm.close()
        md.close()
        print os.path.join(mddir,mdFilename) + ' is OK!'
    confile.close()
    # textileFilename = 'textile.txt'
    # textile = file(os.path.join(mddir,textileFilename),'wb')
    # textile.write(transform.mm2textile(mm.read()).encode('utf8'))
    # textile.close()

if __name__ == "__main__":
    main(sys.argv)
    # main([])