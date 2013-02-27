#!/usr/bin/python
"""
Hacked parts of pagefromfile.py to work with downloaded templates
from get_templates.py.

Syntax: python upload_pages.py
"""
# (C) Densho, 2012
# Distributed under the terms of the MIT license.

from optparse import OptionParser, OptionGroup
import os
from subprocess import Popen, PIPE, STDOUT
import sys
import time

from pagefromfile import PageFromFileRobot, PageFromFileReader
import wikipedia as pywikibot



if sys.platform == 'win32':
    SRC_DIR = 'e:\\encyclopedia\wiki\pages'
else:
    SRC_DIR = '/home/gjost/www/densho/encyclopedia/wiki/pages'
# Delete existing pages before uploading
force = True
# Templates to upload (points to './pages/NAME.mwp')
EXTENSION = '.mwp'



def main():
    parser = OptionParser()
    parser.add_option("-s", "--srcdir", dest="srcdir",
                  help="Directory containing the .mwp pages to upload")
    parser.add_option("-f", "--force",
                     action="store_true", dest="force", default=False,
                     help="Upload even if pages already exist.")
    (options, args) = parser.parse_args()
    
    # Adapt these to the file you are using. 'pageStartMarker' and
    # 'pageEndMarker' are the beginning and end of each entry. Take text that
    # should be included and does not occur elsewhere in the text.
    
    # TODO: make config variables for these.
    filename = "dict.txt"
    pageStartMarker = "{{-start-}}"
    pageEndMarker = "{{-stop-}}"
    titleStartMarker = u"'''"
    titleEndMarker = u"'''"
    
    force = options.force
    if force:
        print 'FORCE UPLOADS ON'
    include = False
    append = None
    notitle = False
    summary = None
    minor = False
    autosummary = False
    dry = False
    
    pages = []
    print options.srcdir
    fnames = os.listdir(options.srcdir)
    fnames.sort()
    for fn in fnames:
        if '.mwp' in fn:
            pages.append(fn)
    print pages
    for page in pages:
        filename = os.path.join(options.srcdir, page)
        print filename
        # reads .mwp file
        reader = PageFromFileReader(filename,
                                    pageStartMarker, pageEndMarker,
                                    titleStartMarker, titleEndMarker,
                                    include, notitle)
        # writes to wiki
        bot = PageFromFileRobot(reader, force, append, summary, minor, autosummary, dry)
        bot.run()
    print


if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()
