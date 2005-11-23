# $Id$

import re
import urllib

import dtuple

import canary.context
from canary.utils import DTable


class Journal (canary.context.Cacheable, DTable):
    """
    A simple structure containing exactly one row of the NLM MEDLINE
    journal list, stored locally in the db as "medline_journals".
    
    http://www.ncbi.nlm.nih.gov/entrez/citmatch_help.html#JournalLists
    """
    
    CACHE_KEY = 'journal'
    ALT_CACHE_KEY = 'issn'

    def __init__ (self, context=None, uid=-1):
        try:
            if self.journal_title:
                return
        except AttributeError:
            pass
            
        self.uid = uid
        self.journal_title = ''
        self.abbreviation = ''
        self.issn = ''
        self.eissn = ''
        self.iso_abbr = ''
        self.nlm_id = ''
    
    def no_dash (self):
        """Return the ISSN without the dash."""
        return self.issn[0:4] + self.issn[5:]
           
    def load_from_issn (self, context, issn):
        if not issn:
            return
        
        if context.config.use_cache:
            j = context.cache_get('%s:%s' % (self.ALT_CACHE_KEY, issn))
            if j \
                and j.journal_title:
                for att in ('uid', 'journal_title', 'abbreviation',
                    'issn', 'eissn', 'iso_abbr', 'nlm_id'):
                    self.set(att, getattr(j, att))
                return
        
        cursor = context.get_cursor()
        cursor.execute("""
            SELECT uid, journal_title, abbreviation, nlm_id
            FROM medline_journals
            WHERE issn = %s
            """, issn)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        if rows:
            row = rows[0]
            row = dtuple.DatabaseTuple(desc, row)
            for k, v in row.items():
                self.set(k, v)
            self.issn = issn
            
            if context.config.use_cache:
                context.cache_set('%s:%s' % (self.CACHE_KEY, self.uid), self)
                context.cache_set('%s:%s' % (self.ALT_CACHE_KEY, self.issn), self)
    
    def load (self, context):
        if self.uid == -1:
            return
        
        # Is it already loaded?  Convenience check for client calls
        # don't need to verify loads from the cache.
        if context.config.use_cache:
            try:
                if self.journal_title:
                    # Already loaded
                    return
            except AttributeError:
                # Note already loaded, so continue
                pass

        cursor = context.get_cursor()
        cursor.execute("""
            SELECT journal_title, abbreviation, issn, nlm_id
            FROM medline_journals
            WHERE uid = %s
            """, self.uid)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        
        rows = cursor.fetchall()
        for row in rows:
            row = dtuple.DatabaseTuple(desc, row)
            for k, v in row.items():
                self.set(k, v) 
                
        if context.config.use_cache:
            context.cache_set('%s:%s' % (self.ALT_CACHE_KEY, self.issn), self)


xslt = """<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">

    <xsl:output method='html'/>

    <xsl:template match='/'>

        <xsl:apply-templates select='//MedlineCitation'/>

    </xsl:template>


    <xsl:template match='MedlineCitation'>

        <xsl:apply-templates select='PMID'/>

        <xsl:apply-templates select='Article/Journal/JournalIssue'/>

        <xsl:apply-templates select='MedlineJournalInfo/MedlineTA'/>

        <xsl:apply-templates select='Article/ArticleTitle'/>

        <xsl:apply-templates select='Article/Pagination/MedlinePgn'/>

        <xsl:apply-templates select='Article/Abstract/AbstractText'/>

        <xsl:apply-templates select='Article/Affiliation'/>

        <xsl:apply-templates select='Article/AuthorList/Author'/>

    </xsl:template>


    <xsl:template match='PMID'>

        <xsl:value-of select='.'/>

    </xsl:template>

</xsl:stylesheet>
"""


class Pubmed:

    def __init__ (self):
        self.tool = 'ycmi_canary_database'
        self.email = 'daniel.chudnov@yale.edu'

        self.count = 0
        self.query_key = 0
        self.web_env = ''

        self.results = ''

        self.re_query_key = re.compile(r'<QueryKey>(.*)</QueryKey>')
        self.re_web_env = re.compile(r'<WebEnv>(.*)</WebEnv>')
        self.re_count = re.compile(r'<Count>(.*)</Count>')
        self.re_body_tags = re.compile('</?(Html|Body)>')
        self.re_title_data = re.compile('<Title>.*</Title>\\n')

    def url_tool_info (self):
        return '&tool=%s&email=%s' % (self.tool, self.email)

    """
Simple esearch following definition at:

  http://eutils.ncbi.nlm.nih.gov/entrez/query/static/esearch_help.html

Note:  currently handles no options such as date range.
    """
    def esearch (self, query, use_history=True):
        url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed'

        if use_history:
            url = url + '&usehistory=y'
        else:
            url = url + '&usehistory=n'

        url = url + '&term=' + urllib.quote_plus(query)
        url = url + self.url_tool_info()
        data = urllib.urlopen(url).read()

        self.count = self.re_count.search(data).groups()[0]

        if use_history:
            self.query_key = self.re_query_key.search(data).groups()[0]
            self.web_env = self.re_web_env.search(data).groups()[0]

        return (self.count, self.query_key, self.web_env)



    """
Simple elink following definition at:

  http://eutils.ncbi.nlm.nih.gov/entrez/query/static/elink_help.html

Note: currently only handles cmd=neighbor with no options.
    """
    def elink (self, pmid, use_history=True):
        pass



    """
Simple efetch following definition at:

  http://eutils.ncbi.nlm.nih.gov/entrez/query/static/efetch_help.html

Returns the query result data in the specified format.

Note that retmode='html' will have surrounding <html> and <body> tags;
strip_body_tags, if true, will remove these, leaving a <pre> formatted
result layout.
    """
    def efetch (self, query_key, webenv,
                retstart=0, retmax=10,
                retmode='text', rettype='citation',
                strip_body_tags=True):


        url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed'

        url = url + '&WebEnv=%s' % (webenv)
        url = url + '&query_key=%s' % (query_key)
        url = url + '&retstart=%s' % (retstart)
        url = url + '&retmax=%s' % (retmax)
        url = url + '&retmode=%s' % (retmode)
        url = url + '&rettype=%s' % (rettype)

        url = url + self.url_tool_info()

        data = urllib.urlopen(url).read()

        if strip_body_tags:
            data = self.re_body_tags.sub('', data)
            data = self.re_title_data.sub('', data)

        self.results = data

