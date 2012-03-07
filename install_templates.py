# -*- coding: utf-8 -*-
"""
Hacked parts of pagefromfile.py to work with downloaded templates
from get_templates.py.

Syntax: python install_templates.py
"""
# (C) Densho, 2012
# Distributed under the terms of the MIT license.

import os
from subprocess import Popen, PIPE, STDOUT
import sys
import time

import config
from pagefromfile import PageFromFileRobot, PageFromFileReader
import wikipedia as pywikibot



SEP = os.path.sep
if sys.platform == 'win32':
    DEST_DIR = SEP.join(['e:','encyclopedia','wiki','templates'])
else:
    DEST_DIR = '/home/gjost/www/densho/encyclopedia/wiki/templates'

# Delete existing pages before uploading
force = True
# Templates to upload (points to './templates/NAME.txt')
templates = [
    'Template:Citation',
    'Template:Infobox',
    'Template:Navbox',
    'Template:Reflist',
    'Template:Refbegin',
    'Template:Refend',
    ]
EXTENSION = '.mwt'


def fixfilename(fn):
    return fn.replace('/', '-').replace(':', '-')





def main():
    # Adapt these to the file you are using. 'pageStartMarker' and
    # 'pageEndMarker' are the beginning and end of each entry. Take text that
    # should be included and does not occur elsewhere in the text.

    # TODO: make config variables for these.
    filename = "dict.txt"
    pageStartMarker = "{{-start-}}"
    pageEndMarker = "{{-stop-}}"
    titleStartMarker = u"'''"
    titleEndMarker = u"'''"
    
    include = False
    force = False
    append = None
    notitle = False
    summary = None
    minor = False
    autosummary = False
    dry = False

    all_dependencies = []
    
    print
    for template in templates:
        print template
        fn = '%s.txt' % fixfilename(template)
        tfname = SEP.join([DEST_DIR, fn])
        print '%s > %s' % (template, tfname)
        f1 = open(tfname, 'r')
        dependencies = f1.readlines()
        f1.close()
        for d in dependencies:
            print '    %s' % d
            d = d.strip()
            dfn = '%s%s' % (fixfilename(d), EXTENSION)
            filename = SEP.join([DEST_DIR, dfn])
            if filename not in all_dependencies:
                all_dependencies.append(filename)
                #print '\t%s (%s)' % (d, filename)
        print
    all_dependencies.sort()
    
    for filename in all_dependencies:
        reader = PageFromFileReader(filename,
                                    pageStartMarker, pageEndMarker,
                                    titleStartMarker, titleEndMarker,
                                    include, notitle)
        bot = PageFromFileRobot(reader,
                                force, append, summary, minor, autosummary, dry)
        bot.run()
        #print UPLOAD_CMD % dfname
        #p = Popen(UPLOAD_CMD % dfname, shell=True,
        #          stdin=PIPE, stdout=PIPE, stderr=STDOUT,
        #          close_fds=True)
        #response = p.stdout.read()
        #print response
        #time.sleep(120)
    print
        
        

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
