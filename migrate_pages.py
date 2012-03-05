# -*- encoding: utf-8 -*-

import codecs
import re
import sys

from bs4 import BeautifulSoup, UnicodeDammit
from bs4.dammit import EntitySubstitution


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
    styletag = soup('style')[0].contents[0]
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
            new_tag = soup.new_tag('h2')
            new_tag.string = s.string
            s.parent.replace_with(new_tag)
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
    return html, references


def replace_references(html, references, debug=False):
    """Move footnotes from bottom to within text, in MediaWiki <ref> format.

    Google Docs:
        <sup><a href="\#ftnt11" name="ftnt_ref11">[11]</a></sup>
    MediaWiki:
        <ref name="ftnt_ref11">Dorothy Ochiai Hazama and Jane Okamoto Komeiji, \
        Okage Same De: The Japanese in Hawai\xe2\x80\x98i 1885-1985 \
        (Honolulu: Bess Press, 1986), 130.</ref>
    
    NOTE: The href and name in the in-text note and the ones in the footnote
    at the bottom are flipped! (i.e. the name in the footnote is the href of the
    <sup><a> in the text.)
    """
    soup = BeautifulSoup(html)
    for name in references.keys():
        ref = references[name]
        href = '#%s' % name
        name = ref['href']
        a = soup.find('a', attrs={'name':name, 'href':href}).parent
        if debug:
            print name
            print href
            print ref['note']
            print '<a href="%s" name="%s">' % (href, name)
            print a
        new_tag = soup.new_tag('ref')
        new_tag.string = ref['note']
        a.replace_with(new_tag)
    return unicode(soup)

def substitute_html_entities(html):
    return EntitySubstitution.substitute_html(html)


DEBUG = False
fname = 'EmergencyServiceCommitteeNakamura.docx.html'
#fname = 'KooskiaWegars.doc.html'
#fname = 'SoneMonicaMatsumoto.docx.html'

f = codecs.open(fname, 'r', 'utf-8')
raw = f.read()
html = UnicodeDammit(raw, ["windows-1252"], smart_quotes_to="html").unicode_markup
html = demoronizer(html)

spans_tags = map_spans_to_tags(html)

html = remove_empty_tags(html)
html,title = convert_headers(html, spans_tags)
html = convert_headword_links(html)
html = convert_spans_tags(html, spans_tags)
html,references = find_references(html)
html = replace_references(html, references)
html = remove_whitespace(html)
html = remove_tags(html, rmthese=['span',])
html = convert_paragraphs(html)


print html
#soup = BeautifulSoup(html)
#print(soup.prettify(formatter=substitute_html_entities))

