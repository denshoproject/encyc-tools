"""sync_wanted.py

Queries local MediaWiki for wanted files/pages/templates.
Tries to GET these from en.wikipedia.org and PUT them on local wiki.

Replaces get_templates.py and install_templates.py, which relied on
manually-updated lists of templates.

NOTE: Templates often include other templates/pages/files, so you
will probably have to run this script multiple times.
"""

from datetime import datetime
import codecs
import os
import sys

from bs4 import BeautifulSoup
import requests
import simplejson

import wikipedia as pywikibot
from pagefromfile import PageFromFileRobot, PageFromFileReader



DEBUG = True
force = False

SEP = os.path.sep

DEST_SITE = 'http://beater/mediawiki'
DEST_API = '%s/api.php?format=json' % DEST_SITE

SRC_SITE = 'http://en.wikipedia.org/wiki'

if sys.platform == 'win32':
    BASE_PATH = ['e:','encyclopedia','wiki']
else:
    BASE_PATH = ['/home', 'gjost', 'www', 'densho', 'encyclopedia', 'wiki',]

# cross-platform local filesystem paths
def path_append(path1, dir):
    path2 = []
    [path2.append(x) for x in path1]
    path2.append(dir)
    return SEP.join(path2)
TEMPLATES_PATH = path_append(BASE_PATH, 'templates')
PAGES_PATH = path_append(BASE_PATH, 'pages')
FILES_PATH = path_append(BASE_PATH, 'files')

UPLOAD_TEMPLATE = """{{-start-}}
'''%s'''
%s
{{-stop-}}"""
UPLOAD_TEMPLATE_PAGE_START = "{{-start-}}"
UPLOAD_TEMPLATE_PAGE_END = "{{-stop-}}"
UPLOAD_TEMPLATE_TITLE_START = "'''"
UPLOAD_TEMPLATE_TITLE_END = "'''"

TEMPLATE_EXTENSION = '.mwt'
PAGE_EXTENSION = '.mwp'



def fixfilename(fn):
    """Remove chars we don't like from filenames.
    """
    return fn.replace('/', '-').replace(':', '-')

def get_qppage(api_url, qppage):
    """Query MediaWiki API for things.
    """
    results = []
    url = '%s&action=query&list=querypage&qppage=%s' % (api_url, qppage)
    if DEBUG:
        print url
    r = requests.get(url)
    query = simplejson.loads(r.text)
    for r in query['query']['querypage']['results']:
        results.append(r['title'])
    results.sort()
    return results



def get_template(title):
    """Retrieve a template from Wikipedia; follow and save redirects.
    
    Use Pywikipediabot to download 
    """
    if DEBUG:
        print 'get_template(%s)' % title
    CMD = 'python get.py -family:wikipedia -lang:en "%s"'
    localtitle = fixfilename(title)
    fname = '%s/%s%s' % (TEMPLATES_PATH, localtitle, TEMPLATE_EXTENSION)
    if DEBUG:
        print'  %s > %s' % (title, os.path.basename(fname))
    if os.path.exists(fname) and not force:
        pass
    else:
        family = pywikibot.Family('wikipedia')
        try:
            page = pywikibot.Page(pywikibot.getSite(fam=family), title.encode('utf-8'))
        except:
            page = None
        text = None
        if page:
            try:
                text = page.get()
            except pywikibot.IsRedirectPage:
                target = page.getRedirectTarget()
                if DEBUG:
                    print '    REDIRECT'
                    print '    %s > %s' % (title, target)
                get_template(target.title())
                text = '#REDIRECT [[%s]]' % page.getRedirectTarget()
            except:
                print 'ERROR getting template!'
        if text:
            try:
                contents = UPLOAD_TEMPLATE % (title, text.strip())
            except:
                print 'ERROR preparing template contents!'
                contents = None
            if contents:
                f = codecs.open(fname, 'w', 'utf-8')
                f.write(contents)
                f.close()

def put_template(title):
    """Upload a template to MediaWiki
    """
    if DEBUG:
        print 'put_template(%s)' % title
    filename = "dict.txt"
    include = False
    force = False
    append = None
    notitle = False
    summary = None
    minor = False
    autosummary = False
    dry = False
    #
    fn = '%s%s' % (fixfilename(title), TEMPLATE_EXTENSION)
    filename = SEP.join([TEMPLATES_PATH, fn])
    if DEBUG:
        print '%s > %s' % (title, filename)
    reader = PageFromFileReader(filename,
                                UPLOAD_TEMPLATE_PAGE_START, UPLOAD_TEMPLATE_PAGE_END, 
                                UPLOAD_TEMPLATE_TITLE_START, UPLOAD_TEMPLATE_TITLE_END, 
                                include, notitle)
    bot = PageFromFileRobot(reader,
                            force, append, summary, minor, autosummary, dry)
    bot.run()

def sync_templates(api_url):
    """Get list of wanted templates, get from Wikipedia, install.
    """
    print 'CHECKING FOR WANTED TEMPLATES...'
    titles = get_qppage(DEST_API, 'Wantedtemplates')
    if titles:
        print titles
        print 'GET-ing TEMPLATES'
        for title in titles:
            get_template(title)
        print 'PUT-ing TEMPLATES'
        for title in titles:
            put_template(title)
    else:
        print 'No wanted templates!'
    print 'DONE'
    print
    # check for more...
    return get_qppage(DEST_API, 'Wantedtemplates')



def get_page(title):
    """Retrieve a page from Wikipedia; follow and save redirects.
    
    Use Pywikipediabot to download 
    """
    if DEBUG:
        print 'get_page(%s)' % title
    localtitle = fixfilename(title)
    fname = '%s/%s%s' % (PAGES_PATH, localtitle, PAGE_EXTENSION)
    if DEBUG:
        print'  %s > %s' % (title, os.path.basename(fname))
    if os.path.exists(fname) and not force:
        pass
    else:
        family = pywikibot.Family('wikipedia')
        page = pywikibot.Page(pywikibot.getSite(fam=family), title.encode('utf-8'))
        try:
            text = page.get()
        except pywikibot.IsRedirectPage:
            target = page.getRedirectTarget()
            if DEBUG:
                print '    REDIRECT'
                print '    %s > %s' % (title, target)
            get_template(target.title())
            text = '#REDIRECT [[%s]]' % page.getRedirectTarget()
        except:
            print 'ERROR!!!'
            text = None
        if text:
            contents = UPLOAD_TEMPLATE % (title, text.strip())
            f = codecs.open(fname, 'w', 'utf-8')
            f.write(contents)
            f.close()

def put_page(title):
    """Upload a page to local MediaWiki
    """
    if DEBUG:
        print 'put_page(%s)' % title
    filename = "dict.txt"
    include = False
    force = False
    append = None
    notitle = False
    summary = None
    minor = False
    autosummary = False
    dry = False
    #
    fn = '%s%s' % (fixfilename(title), PAGE_EXTENSION)
    filename = SEP.join([PAGES_PATH, fn])
    if DEBUG:
        print '%s > %s' % (title, filename)
    reader = PageFromFileReader(filename,
                                UPLOAD_TEMPLATE_PAGE_START, UPLOAD_TEMPLATE_PAGE_END, 
                                UPLOAD_TEMPLATE_TITLE_START, UPLOAD_TEMPLATE_TITLE_END, 
                                include, notitle)
    bot = PageFromFileRobot(reader,
                            force, append, summary, minor, autosummary, dry)
    bot.run()

def sync_pages(api_url):
    """GETS list of wanted pages, GETS from Wikipedia, PUTs on local.
    """
    print 'CHECKING FOR WANTED PAGES...'
    titles = get_qppage(DEST_API, 'Wantedpages')
    if titles:
        print titles
        print 'GET-ing PAGES'
        for title in titles:
            get_page(title)
        print 'PUT-ing PAGES'
        for title in titles:
            put_page(title)
    else:
        print 'No wanted pages!'
    print 'DONE'
    print
    # check for more...
    return get_qppage(DEST_API, 'Wantedpages')



def main():
    templates = get_qppage(DEST_API, 'Wantedtemplates')
    pages = get_qppage(DEST_API, 'Wantedpages')
    #files = get_qppage(DEST_API, 'Wantedfiles')
    files = []
    n = 0
    while (templates or pages or files) and n < 10:
        print '----------------------------------------------------------------------'
        print 'ROUND %s' % n
        templates = sync_templates(DEST_API)
        pages = sync_pages(DEST_API)
        #files = sync_files(DEST_API)
        print
        # no infinite loops...
        n = n + 1

if __name__ == '__main__':
    main()
