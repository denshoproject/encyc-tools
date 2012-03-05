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



DEST_DIR = '/home/gjost/www/densho/encyclopedia/wiki/templates/'
# Delete existing pages before uploading
force = True
# Templates to upload (points to './templates/NAME.txt')
templates = [
    'Template:Citation/core',
    'Template:Infobox',
    'Template:Navbox',
    ]
EXTENSION = '.mwt'


def fixfilename(fn):
    return fn.replace('/', '-')





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
    
    print
    for template in templates:
        tfname = '%s%s.txt' % (DEST_DIR, fixfilename(template))
        sys.stdout.write('%s > %s' % (template, tfname))
        f1 = open(tfname, 'r')
        dependencies = f1.readlines()
        f1.close()
        print
        for d in dependencies:
            d = d.strip()
            filename = '%s%s%s' % (DEST_DIR, fixfilename(d), EXTENSION)
            sys.stdout.write('\t%s (%s)' % (d, filename))
            print
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
