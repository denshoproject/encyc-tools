# -*- coding: utf-8 -*-
"""
Given a (hardcoded) list of page titles, downloads the pages from
Wikipedia (hardcoded) and writes them to template files that can be
uploaded by install_templates.py.

Syntax: python get_templates.py
"""
# (C) Densho, 2012
# Distributed under the terms of the MIT license.

import codecs
import os
import sys
import time

import wikipedia as pywikibot



# ----------------------------------------------------------------------
DEST_DIR = '/home/gjost/www/densho/encyclopedia/wiki/templates/'
# Download even if already downloaded
force = False
# wait between file downloads
wait = 0
# Templates and their dependencies
templates = {
    'Template:Citation': [
        'Template:Cite_book',
        'Template:Cite book/doc',
        'Template:Cite_journal',
        'Template:Cite_news',
        'Template:Cite_press_release',
        'Template:Cite_web',
        'Template:AuthorMask_doc',
        'Template:Citation_Style_documentation',
        'Template:Citation_Style_documentation/id1',
        'Template:Citation_Style_documentation/id2',
        'Template:Citation_Style_documentation/url',
        'Template:Citation/authors',
        'Template:Citation/core',
        'Template:Citation/core/doc',
        'Template:Citation/doc',
        'Template:Citation/identifier',
        'Template:Citation/make_link',
        'Template:Citation/patent',
        'Template:Cite_press_release',
        'Template:Citation_Style_documentation',
        'Template:Documentation',
        'Template:Documentation_subpage',
        'Template:Documentation/docspace',
        'Template:Documentation/end_box',
        'Template:Documentation/end_box2',
        'Template:Documentation/start_box',
        'Template:Documentation/start_box2',
        'Template:Documentation/template_page',
        'Template:Fmbox',
        'Template:For2',
        'Template:Harvard_citation',
        'Template:Harvard_citation_no_brackets',
        #'Template:Harvid',
        'Template:Hatnote',
        'Template:Hide_in_print',
        'Template:OL',
        'Template:Only_in_print',
        'Template:Para',
        'Template:Pp-meta',
        'Template:Pp-template',
        'Template:Purge',
        'Template:Reflist',
        #'Template:SfnRef',
        'Template:Template_other',
        'Template:Tl',
        'Template:UF-COinS',
        'Template:Visible_anchor',
        ],
    'Template:Infobox': [
        'Template:Clear',
        'Template:Documentation',
        'Template:Documentation_subpage',
        'Template:Documentation/docspace',
        'Template:Documentation/end_box',
        'Template:Documentation/end_box2',
        'Template:Documentation/start_box',
        'Template:Documentation/start_box2',
        'Template:Documentation/template_page',
        'Template:Fmbox',
        'Template:Infobox',
        'Template:Infobox/doc',
        'Template:Infobox/row',
        'Template:Navbar',
        'Template:Nowrap',
        'Template:Para',
        'Template:Pp-meta',
        'Template:Pp-template',
        'Template:Purge',
        'Template:Template_other',
        'Template:Tl',
        'Template:Transclude',
        ],
    'Template:Navbox': [
        'Template:-',
        'Template:Documentation',
        'Template:Documentation_subpage',
        'Template:Documentation/docspace',
        'Template:Documentation/end_box',
        'Template:Documentation/end_box2',
        'Template:Documentation/start_box',
        'Template:Documentation/start_box2',
        'Template:Documentation/template_page',
        'Template:Fmbox',
        'Template:Hatnote',
        'Template:High-risk',
        'Template:Loop15',
        'Template:Main',
        'Template:Navbar',
        'Template:Navbox',
        'Template:Navbox_suite',
        'Template:Navbox/doc',
        'Template:Navigation_templates',
        'Template:Oldid',
        'Template:Ombox',
        'Template:Ombox/core',
        'Template:Para',
        'Template:Pp-meta',
        'Template:Pp-template',
        'Template:Purge',
        'Template:Rellink',
        'Template:Selfref',
        'Template:Spaces',
        'Template:Strikethrough',
        'Template:Tag',
        'Template:Template_other',
        'Template:Tl',
        'Template:Tlf',
        'Template:Tlx',
        'Template:Tn',
        'Template:Transclude',
        'Template:URL',
        #'Template:·',
        ],
    }
# ----------------------------------------------------------------------


CMD = 'python get.py -family:wikipedia -lang:en "%s"'
TEMPLATE = """{{-start-}}
'''%s'''
%s
{{-stop-}}"""
EXTENSION = '.mwt'

def fixfilename(fn):
    return fn.replace('/', '-')


def download():
    
    for template,dependencies in templates.items():
        
        print template
        
        # prepend template to its list of dependencies
        dependencies.reverse()
        dependencies.append(template)
        dependencies.reverse()
        print dependencies
        
        # write dependencies list to file -- install_templates will use this
        tfname = '%s%s.txt' % (DEST_DIR, fixfilename(template))
        f1 = open(tfname, 'w')
        f1.write('\n'.join(dependencies))
        f1.close
        print 'dep OK'
        
        # download and write dependencies files
        i = 0
        for title in dependencies:
            i = i + 1
            sys.stdout.write('%s/%s' % (i, len(dependencies)))
            
            # filename
            localtitle = fixfilename(title)
            fname = '%s%s%s' % (DEST_DIR, localtitle, EXTENSION)
            print'  %s > %s' % (title, fname)
            
            if os.path.exists(fname) and not force:
                print ' ALREADY DOWNLOADED'
            else:
                # download
                family = pywikibot.Family('wikipedia')
                page = pywikibot.Page(pywikibot.getSite(fam=family),
                                      title.encode('utf-8'))
                contents = TEMPLATE % (title,
                                       page.get().strip())
                if contents:
                    f = codecs.open(fname, 'w', 'utf-8')
                    f.write(contents)
                    f.close()
                print ' OK'
                
        print
        time.sleep(wait)


if __name__ == "__main__":
    try:
        download()
    finally:
        pywikibot.stopme()
