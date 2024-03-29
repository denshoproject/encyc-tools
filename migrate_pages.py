# -*- encoding: utf-8 -*-

import codecs
import os
import re
import sys

from bs4 import BeautifulSoup, UnicodeDammit
from bs4.dammit import EntitySubstitution



DEBUG = False
SRC_DIR  = '/home/gjost/www/densho/encyclopedia/wiki/documents'
DEST_DIR = '/home/gjost/www/densho/encyclopedia/wiki/pages'
# Template that pywikipediabot.pagefromfile understands.
TEMPLATE = """{{-start-}}
'''%s'''%s{{-stop-}}"""
# output file extension
EXTENSION = 'mwp'



def demoronizer(text):
    """
    Converts Microsoft proprietary characters (e.g. smart quotes, em-dashes)
    to sane characters
    http://code.djangoproject.net/browser/django/trunk/django/utils/text.py?rev=378
    """
    # Sources:
    # http://stsdas.stsci.edu/bps/pythontalk8.html
    # http://www.waider.ie/hacks/workshop/perl/rss-fetch.pl
    # http://www.fourmilab.ch/webtools/demoroniser/
    text = text.replace(u'\x91', u"'")
    text = text.replace(u'\x92', u"'")
    text = text.replace(u'\x93', u'"')
    text = text.replace(u'\x94', u'"')
    text = text.replace(u'\xd2', u'"')
    text = text.replace(u'\xd3', u'"')
    text = text.replace(u'\xd5', u"'")
    text = text.replace(u'\xad', u'--')
    text = text.replace(u'\xd0', u'--')
    text = text.replace(u'\xd1', u'--')
    text = text.replace(u'\xe2\x80\x98', u"'") # weird single quote (open)
    text = text.replace(u'\xe2\x80\x99', u"'") # weird single quote (close)
    text = text.replace(u'\xe2\x80\x9c', u'"') # weird double quote (open)
    text = text.replace(u'\xe2\x80\x9d', u'"') # weird double quote (close)
    text = text.replace(u'\xe2\x81\x84', u'/')
    text = text.replace(u'\xe2\x80\xa6', u'...')
    text = text.replace(u'\xe2\x80\x94', u'--')
    return text.strip()


def map_spans_to_tags(html, debug=False):
    """Extract <span>s-to-tags mapping from GoogleDocs page HTML.
    
    Google Docs don't use actual tags like <strong>, <em>, or <u>.
    Instead they use something like <span class="c7">.
    This function examines the CSS styles in <head><styles> and maps
    Google's span classes to actual, real tags.
    
    CSS terminology:
        selector, selector { #                                  |
          property: value;   # declaration |                    +- rule
          property: value;   # declaration +- declaration block |
          property: value;   # declaration |                    |
        }                    #                                  |
    """
    styles = {}
    EXCLUDED_TAGS = ['h1','h2','h3','h4','h5','h6','title','subtitle',]
    # soup
    soup = BeautifulSoup(html)
    if debug:
        print soup.prettify()
    # map function
    def mapper(styles, rule, value, tag):
        """
        rule:  selector { declaration }
               selector { property: value; }
        value: 'bold', 'italic', '40px'
        tag:   <strong>, <em>, <img>
        """
        if rule['declaration'].find(value) > -1:
            if styles.get(tag, None):
                styles[rule['selector']].append(tag)
            else:
                styles[rule['selector']] = [tag]
        return styles
    # break up raw CSS from <head><style> tag into selectors and declarations
    lines = []
    styletag = None
    if soup('style') and soup('style')[0] and soup('style')[0].contents[0]:
        if styletag:
            for line in styletag.split('}'):
                ab = line.split('{')
                if len(ab) == 2:
                    lines.append({'selector':    ab[0].replace('.', ''),
                                  'declaration': ab[1].replace('}', ''),})
    # extract the rules we're interested in
    for rule in lines:
        if rule['selector'] not in EXCLUDED_TAGS:
            styles = mapper(styles, rule, 'bold',      'strong')
            styles = mapper(styles, rule, 'italic',    'em')
            styles = mapper(styles, rule, 'underline', 'u')
            styles = mapper(styles, rule, 'center',    'center')
    if debug:
        print styles
    return styles


def convert_spans_tags(html, spans_tags, debug=False):
    """
    """
    # first convert all the <span class="cN">...</span> to
    # sensible regular HTML
    for c in spans_tags.keys():
        p = u'<span class="[a-z0-9 ]*%s[a-z0-9 ]*">([\w .,:-‘&;()]+)</span>'
        pattern = p % c
        fwd = []; rvs = []
        [fwd.append('<%s>' % t) for t in spans_tags[c]]
        spans_tags[c].reverse()
        [rvs.append('</%s>' % t) for t in spans_tags[c]]
        replace = r'%s\1%s' % (''.join(fwd), ''.join(rvs))
        if debug:
            print pattern
            print replace
            print
        html = re.sub(pattern, replace, html)
    return html


def remove_empty_tags(html, debug=False):
    """
    """
    html = html.replace('&nbsp;', ' ')
    # spaces (<span class="c17"> </span>)
    pattern = '<[a-z0-9=" ]+> +</[a-z]+>'
    while re.search(pattern, html):
        html = re.sub(pattern, ' ', html)
    # truly empty tags
    pattern = '<[a-z0-9=" ]+></[a-z]+>'
    while re.search(pattern, html):
        html = re.sub(pattern, '', html)
    return html


def convert_headword_links(html, debug=False):
    """Convert headword <a> links to [[wiki links]].
    
    Examples:
        <a class="c5" href="http://headword">Nisei</a>
        <a class="c5" href="http://headword">Hung Wai Ching</a>
        <a href="http://headword" class="c5">martial law</a>
    """
    soup = BeautifulSoup(html)
    for tag in soup.find_all('a', href="http://headword"):
        new_string = '[[%s]]' % tag.string
        tag.parent.replace_with(new_string)
    return unicode(soup)


def convert_headers(html, spans_tags, debug=False):
    """Convert Google Docs headers to plain h(1-6).
    
    h1 - <p class="[center]"><span class="[bold]">
         <p class="[center]"><strong>
    h2 - <p><span class="[bold]">
         <p><strong>
    Executive decision: convert them all to h2 except the first, which is h1.
    """
    title = ''
    soup = BeautifulSoup(html)
    # get CSS styles used in headers
    center_class = ''
    bold_class = ''
    for k,v in spans_tags.iteritems():
        if 'center' in v:
            center_class = k
        if 'strong' in v:
            bold_class = k
    # first header --> page title
    # h1 - <p class="[center]"><span class="[bold]">
    for h in soup.find_all(name='p', attrs={'class':center_class}):
        #new_tag = soup.new_tag('h2')
        #new_tag.string = h.string
        #h.replace_with(new_tag)
        title = h.string
        h.decompose()
        break
    # the rest of the headers
    # h2 - <p><span class="[bold]">
    for p in soup.find_all(name='p'):
        for s in p.find_all(name='span', attrs={'class':bold_class}):
            #print s.parent
            new_string = '\n\n==%s==\n\n' % s.string
            s.parent.replace_with(new_string)
    #assert False
    return unicode(soup), title


def convert_paragraphs(html):
    # hN
    for n in range(1,7):
        html = html.replace('<h%s>' % n,'\n<h%s>' % n)
        html = html.replace('</h%s>' % n,'</h%s>\n' % n)
    # <p>
    pattern = r'<p[a-z0-9 _="#]*>'
    html = re.sub(pattern, '\n', html)
    pattern = r'</p>'
    html = re.sub(pattern, '\n', html)
    return html


def remove_tags(html, rmthese=[], debug=False):
    if rmthese:
        for tag in rmthese:
            pattern = r'<%s[a-z0-9 _="#]*>' % tag
            html = re.sub(pattern, '', html)
            pattern = r'</%s>' % tag
            html = re.sub(pattern, '', html)
    else:
        p = re.compile(r'<.*?>')
        html = p.sub('', html)
    return html


def remove_whitespace(html, debug=False):
    p = re.compile(r'\s+')
    html = p.sub(' ', html)
    return html


def find_references(html, debug=False):
    """
    Find the list of references at the end of the document.
    Example:
        <div>
         <p class="c2">
          <a href="\#ftnt_ref11" name="ftnt11">
           [11]
          </a>
          <span class="c8">
           Dorothy Ochiai Hazama and Jane Okamoto Komeiji,
          </span>
          <span class="c1 c8">
           Okage Same De: The Japanese in Hawai‘i 1885-1985
          </span>
          <span class="c8">
           (Honolulu: Bess Press, 1986), 130.
          </span>
         </p>
        </div>
    """
    references = {}
    soup = BeautifulSoup(html)
    # find div.p.<a name="ftnt*">
    for a in soup.find_all(href=re.compile('#ftnt_ref[0-9]+')):
        numraw = a.contents[0]
        num = numraw.replace('[','').replace(']','')
        href = a['href'].replace('#', '')
        name = a['name']
        note = str(a.parent)
        note = remove_tags(note, rmthese=['a','p','span'])
        note = note.replace(str(numraw), '')
        note = remove_whitespace(note).strip()
        references[name] = {'href':href, 'note':note}
        if debug:
            print num, href, name
            print note
        # remove original note
        a.parent.parent.decompose()
    # rm <hr>, insert anchor for references
    hr = soup.hr
    if hr:
        hr.replace_with('\n\n==References==\n{{Reflist}}\n\n')
    return unicode(soup), references


def replace_references(html, references, debug=False):
    """Move footnotes from bottom to within text, in MediaWiki <ref> format.

    Google Docs:
        <sup><a href="\#ftnt11" name="ftnt_ref11">[11]</a></sup>
    MediaWiki:
        <ref name="ftnt_ref11">Dorothy Ochiai Hazama and Jane Okamoto Komeiji, \
        ''Okage Same De: The Japanese in Hawai\xe2\x80\x98i 1885-1985'' \
        (Honolulu: Bess Press, 1986), 130.</ref>
    
    NOTE: The href and name in the in-text note and the ones in the footnote
    at the bottom are flipped! (i.e. the name in the footnote is the href of the
    <sup><a> in the text.)
    NOTE: <em> tags are converted to WikiText ''.
    """
    soup = BeautifulSoup(html)
    for name in references.keys():
        ref = references[name]
        href = '#%s' % name
        name = ref['href']
        note = ref['note']
        note = note.replace('<em>', "''").replace('</em>', "''")
        a = soup.find('a', attrs={'name':name, 'href':href})
        if a:
            a.parent
            if debug:
                print name
                print href
                print ref['note']
                print '<a href="%s" name="%s">' % (href, name)
                print a
            new_tag = soup.new_tag('ref')
            new_tag['name'] = name
            new_tag.string = note
            a.replace_with(new_tag)
    return unicode(soup)

def substitute_html_entities(html):
    return EntitySubstitution.substitute_html(html)


def convert_tags_to_wikitext(html):
    """One last pass...
    """
    # <em>
    html = html.replace('<em>', "''").replace('</em>', "''")
    # <br/>
    html = html.replace('<br/>', '').replace('<br />', '')
    # <a>
    pattern = r'<a class="[a-z0-9 ]+" href="(http://[a-zA-Z0-9 _.,-;:/?&#%]+)">([a-zA-Z0-9 _.,-;:‘/?&#%]+)</a>'
    replace = r'[\1 \2]'
    html = re.sub(pattern, replace, html)
    # empty <a> tags
    pattern = r'<a class="[a-z0-9 ]+" href="(http://[a-zA-Z0-9 _.,-;:/?&#%]+)"></a>'
    html = re.sub(pattern, '', html)
    # the last <span> tags
    html = html.replace('<span>','').replace('</span>','')
    # spacing
    html = html.replace('\n\n\n', '\n\n')
    return html

def bury_the_body(html):
    # <body class="c10">, </body>
    #pattern = u'<body[a-z0-9 :;-="#]*>'
    pattern = u'<body[a-z0-9 -="]*>'
    html = re.sub(pattern, '', html)
    html = html.replace('</body>', '').replace('<html>', '').replace('</html>', '')
    return html



# ----------------------------------------------------------------------



def rm_empty_span(html):
    """Removes all the <span> tags with no style attrs.
    """
    soup = BeautifulSoup(html)
    tags = ['span', 'p']
    for tag in tags:
        for t in soup.find_all(tag):
            if not t.attrs:
                t.replace_with_children()
    return unicode(soup)

def convert_pspan(html):
    whitelist = {'italic':'em',
                 'underline':'u',
                 'bold':'strong',}
    soup = BeautifulSoup(html)
    tags = ['span', 'p']
    for tag in tags:
        for t in soup.find_all(tag):
            if t.attrs['style']:
                n = 0
                convert_to = None
                for propval in t.attrs['style'].split(';'):
                    pv = propval.split(':')
                    for value in whitelist.keys():
                        if pv and (len(pv) == 2) and (value in pv[1]):
                            n = n + 1
                            convert_to = whitelist[value]
                if not n:
                    del t['style']
                elif n and convert_to:
                    t.name = convert_to
                    t.attrs = None
    return unicode(soup)

def convert_inline_headers(html, debug=False):
    """Convert Google Docs headers to plain h(1-6).
    
    h2 - <p><span style="font-weight:bold;">
         <p><strong>
    Executive decision: convert them all to h2 except the first, which is h1.
    """
    title = None
    soup = BeautifulSoup(html)
    # h2 - <p><span class="[bold]">
    for p in soup.find_all(name='p'):
        for s in p.find_all(attrs={'style':re.compile('bold')}):
            if s.string and s.string.strip():
                # title is first match
                if not title:
                    title = s.string
                    s.parent.decompose()
                else:
                    new_string = '\n\n==%s==\n\n' % s.string
                    s.parent.replace_with(new_string)
    return unicode(soup), title

def convert_external_links(html):
    soup = BeautifulSoup(html)
    for a in soup.find_all(name='a'):
        href = a.attrs['href']
        txt = a.string
        # screen out
        n = 0
        if ('headword' in href): n = n + 1
        if (href == '#'):        n = n + 1
        if ('#cmnt' in href):    n = n + 1
        if (href == '') or (href == None): n = n + 1
        # replace
        if n == 0:
            if (href and txt) and (txt != href):
                ns = '[%s %s]' % (href, txt)
            else:
                ns = href
            a.replace_with(ns)
    return unicode(soup)

def rm_link_underlines(html):
    soup = BeautifulSoup(html)
    for u in soup.find_all('u'):
        if u.string and ('http:' in u.string):
            u.replace_with_children()
    return unicode(soup)



# ----------------------------------------------------------------------



def parse_headstyle_googledoc(html):
    """Parse Google Docs HTML with CSS in <head><style>.
    """
    spans_tags = map_spans_to_tags(html)
    # transform in various ways
    html = remove_empty_tags(html)
    html,title = convert_headers(html, spans_tags)
    if not title:
        t = os.path.basename(fname)
        ext = os.path.splitext(t)
        title = t.replace(ext[-1], '')
    html = convert_headword_links(html)
    html = convert_spans_tags(html, spans_tags)
    html,references = find_references(html)
    html = replace_references(html, references)
    #html = remove_whitespace(html)
    html = convert_paragraphs(html)
    html = remove_tags(html, rmthese=['span',])
    html = convert_tags_to_wikitext(html)
    return html,title


def parse_inlinestyle_googledoc(html):
    soup = BeautifulSoup(html)
    html = unicode(soup.body)
    html = rm_empty_span(html)
    html,title = convert_inline_headers(html)
    html = convert_headword_links(html)
    html = convert_pspan(html)
    html,references = find_references(html)
    html = replace_references(html, references)
    html = remove_empty_tags(html)
    html = convert_external_links(html)
    html = rm_link_underlines(html)
    html = convert_paragraphs(html)
    html = convert_tags_to_wikitext(html)
    #title = 'NOT YET IMPLEMENTED'
    return html,title



SOURCE_FILES = [
    #'ABCList.doc.html',
    #'ACLU.doc.html',
    'AFSCAustin.doc.html',
    #'AllCenterConfHayashi.docx.html',
    #'BiddleFrancis.doc.html',
    ]
DONT_PARSE_THESE = ['index.html',]

def main():
    source_files = []
    fnames = os.listdir(SRC_DIR)
    fnames.sort()
    for f in fnames:
        if f not in DONT_PARSE_THESE:
            source_files.append(f)
    source_files.sort()
    #source_files = SOURCE_FILES
    print source_files
    print

    titles = []
    for fname in source_files:
        inname = '/'.join([SRC_DIR, fname])
        print 'IN : %s' % inname
        infile = codecs.open(inname, 'r', 'utf-8')
        raw = infile.read()
        infile.close()
        #rawsoup = BeautifulSoup(raw)
        #outname = '/'.join([DEST_DIR, '%s.%s' % (inname, EXTENSION)]).replace(' ', '-')
        #print 'OUT: %s' % outname
        #out = codecs.open(inname.replace('.doc', '.clean'), 'w', 'utf-8')
        #out.write(rawsoup.prettify())
        #out.close()
        #break
        
        # convert (again) to Unicode
        html = UnicodeDammit(raw, ["windows-1252"], smart_quotes_to="html").unicode_markup
        # convert Windoze chars
        html = demoronizer(html)

        #html,title = parse_headstyle_googledoc(html)
        html,title = parse_inlinestyle_googledoc(html)
        if not title:
            title = fname.replace('.doc','').replace('.docx','').replace('.html','')
        title = title.replace(u'“','').replace(u'”','').replace(u"’",'')
        titles.append(title)
        
        # templatize
        #soup = BeautifulSoup(html)
        #wikitext = unicode(soup.body)
        wikitext = html.strip()
        wikitext = bury_the_body(wikitext)
        page = TEMPLATE % (title, wikitext)
        
        # write to file
        outname = '/'.join([DEST_DIR, '%s.%s' % (title, EXTENSION)]).replace(' ', '-')
        print 'OUT: %s' % outname
        out = codecs.open(outname, 'w', 'utf-8')
        out.write(page)
        out.close()
        if os.path.exists(outname):
            print 'OK'
        print
    # list of articles for Main_Page
    alist = ['== Articles ==',]
    for t in titles:
        alist.append('* [[%s]]' % t)
    aout = open('/'.join([DEST_DIR,'articles.mwp']), 'w')
    articles = TEMPLATE % ('Articles', '\n'.join(alist))
    aout.write(articles)
    aout.close()
    

if __name__ == '__main__':
    main()
