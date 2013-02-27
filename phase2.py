"""
Geoff Froh
1:50 PM (21 hours ago)

Just reviving this thread. I think the list is nearly ready for import -- definitely in the next day or so. 
The current list is at:

https://docs.google.com/a/densho.us/spreadsheet/ccc?key=0AtoUiX7vEzdfdHRxWW9DY0xtbWVsbUJUZjhGMnR0OFE&usp=sharing

The final list is in the EXPORT tab; you can ignore all the columns, except for:
- "Final Title" : headword title (i.e., title of the new page). Not necessary to repeat in page body.
- "Body" : unformatted text to dump in article main body.
- "Primary Source PD" : boolean flag. E.g., "{{ ps-photodoc }}"
- "Primary Source VH" : boolean flag. E.g., "{{ ps-video }}"
- "Category 1" : category from standard Encyclopedia taxonomy. E.g., "[[ Category:Value ]]"
- "Category 2" : category from standard Encyclopedia taxonomy. E.g., "[[ Category:Value ]]"
- "Default Sort" : the default sort key, if applicable. E.g., "{{ DEFAULTSORT:Value }}"

The structure of the new page should follow what we discussed earlier:

    {{ Status1 }}                                       <-- All entries have this template
    {{ ps-photodoc }}                                   <-- if "Primary Source PD" contains "TRUE"
    {{ ps-video }}                                      <-- if "Primary Source VH" contains "TRUE"
    
    some notes that were in the Body column of the row.
    
    [[Category:People]]                                 <-- contents of "Category 1", "Category 2"
    [[Category:Phase2]]                                 <-- All entries
    [[Category:Import2]]                                <-- All entries
    {{ DEFAULTSORT:LastName,FirstName }}                <-- if "Default Sort" is not null

The only difference between what I wrote in my earlier message is that we're going to ignore the author column. I looked through the data and there are almost none and they often don't match the format anyways so they'll have to be done by hand later anyways.
"""


import csv
import os
import re


ALLOWED_CHARS = ['-', '_', ',', '.', '(', ')', '"', ]
def sanitize_filename( f ):
    f = f.replace(' ', '_')
    f = ''.join(x for x in f if x.isalnum() or x in ALLOWED_CHARS)
    f = f.replace('__', '_')
    return f

def read_csv( srcfile, debug ):
    """Reads contents of spreadsheet into list of dicts."""
    articles = []
    with open(srcfile, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        for n,row in enumerate(reader):
            if n:
                if debug:
                    print( '{} ----------------------------------------'.format(n) )
                # ps-photodoc, ps-video, Category1, Category2, Sort, Title, Body
                templates = ['Status1',]
                if row[0]: templates.append('ps-photodoc')
                if row[1]: templates.append('ps-video')
                categories = []
                if row[2]: categories.append(row[2])
                if row[3]: categories.append(row[3])
                categories.append('Phase2')
                categories.append('Import2')
                sort = None
                if row[4]: sort = row[4]
                a = { 'title':row[5], 'sort':sort, 'body':row[6], 'templates':templates, 'categories':categories, }
                a['filename'] = sanitize_filename(a['title'])
                if debug:
                    print(a['title'])
                articles.append(a)
    return articles

def format_pages( articles, destdir, debug=False ):
    """Write article dicts out to .mwp files.

    Uses template format that upload_pages.py can read:
        {{-start-}}
        '''Your Title Here'''
        {{ templates }}
        
        [[Category:Status 1]]
        {{-stop-}}
    """
    for a in articles:
        # page
        lines = []
        lines.append('{{-start-}}')
        lines.append("'''{}'''".format(a['title']))
        for t in a['templates']:
            lines.append( '{{{{ {} }}}}'.format(t) )
        lines.append('')
        if a['body']:
            lines.append( a['body'] )
            lines.append('')
        for c in a['categories']:
            lines.append( '[[ {} ]]'.format(c) )
        if a['sort']:
            lines.append( '{{{{ DEFAULTSORT:{} }}}}'.format(a['sort']) )
        lines.append('{{-stop-}}')
        txt = '\n'.join(lines).strip()
        if debug:
            print( txt )
            print('\n')
        filename = os.path.join(destdir, '{}.mwp'.format(a['filename']))
        if debug:
            print(filename)
        with open(filename, 'w') as newfile:
            newfile.write(txt)


def main():
    DEBUG = True
    #DEBUG = False
    SRCFILE='/home/gjost/encyc/201302-phase2/phase-II-articles-20130226.csv'
    PAGESDIR='/home/gjost/encyc/201302-phase2/pages'
    
    articles = read_csv(SRCFILE, DEBUG)
    format_pages(articles, PAGESDIR, DEBUG)


if __name__ == '__main__':
    main()
