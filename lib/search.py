# $Id$


import pyparsing as pyp
import PyLucene
from PyLucene import Field, Term, Document
from PyLucene import QueryParser, IndexSearcher, StandardAnalyzer, FSDirectory

from canary.concept import Concept
from canary.gazeteer import Feature
import canary.loader 
import canary.study
from canary.utils import render_capitalized


# All possible search fields, indexed by all valid forms.
SEARCH_FIELDS = {
    '1au':          'first-author',
    'ab':           'abstract',
    'abstract':     'abstract',
    'af':           'affiliation', 
    'affiliation':  'affiliation', 
    'all':          'all',
    'au':           'author',
    'author':       'author',
    'date':         'pubdate',
    'exp':          'exposures',
    'exposures':    'exposures',
    'gn':           'grantnum',
    'grantnum':     'grantnum',
    'has_exposures':        'has_exposures', 
    'has_exposure_linkage': 'has_exposure_linkage',
    'has_genomic':          'has_genomic',
    'has_interspecies':     'has_interspecies',
    'has_outcomes':         'has_outcomes',
    'has_outcome_linkage':  'has_outcome_linkage',
    'has_relationships':    'has_relationships',
    'is':           'issue', 
    'issn':         'issn',
    'issue':        'issue',
    'jn':           'journal',
    'journal':      'journal', 
    'keyword':      'keyword',
    'kw':           'keyword',
    'loc':          'location',
    'location':     'location',
    'mh':           'subject',
    'out':          'outcomes',
    'outcomes':     'outcomes',
    'pd':           'pubdate', 
    'page':         'pages',
    'pages':        'pages',
    'pg':           'pages', 
    'registrynum':  'registrynum',
    'rf':           'risk_factors',
    'risk_factors': 'risk_factors',
    'rn':           'registrynum',
    'sh':           'subject',
    'spec':         'species',
    'species':      'species',
    'subject':      'subject',
    'ti':           'title', 
    'title':        'title',
    'ui':           'unique-identifier',
    'uid':          'unique-identifier',
    'unique-identifier':    'unique-identifier',
    'vol':          'volume',
    'volume':       'volume',
    'word':         'keyword',
    }
    

def disassemble_user_query(s):
    """
    Pre-process user-specified search terms so they may be more easily 
    converted into lucene-friendly tokens.

    Input can be any arbitrary string received from the UI.

    Output is a single python list, where each element is either a 
    single string (eg. 'foo'), or a two-tuple where the first item is 
    the string to search for and the second is an abbreviated field 
    name (eg. ('foo', 'ti')).

    Note: eventually the query parser will be smart enough to support 
    concept matching. At present the parser step defers to lucene for 
    handling of overly-complex query strings, and hands off the output 
    list for re-joining for lucene (see below).

    Presently the PyParsing library (see documentation inside package) 
    is used for the parsing step. This step occurs by default in 
    SearchIndex.preprocess_query(). Preprocessing can be turned off by 
    specifying "preprocess=False" as a parameter to SearchIndex.search().

    It performs the following tasks:

    * converts any of {'and', 'or', 'not'} to {'AND', 'OR', 'NOT'} in-place
        o "foo and bar" becomes "foo AND bar"
        o "foo and or not bar" becomes " 

    * allows field specifications in the form "token [field]" or "token.field."
        o 'foo [ti]' becomes "('foo', 'ti')"
        o 'foo.ti.' becomes "('foo', 'ti')"
        o Note: fields are specified elsewhere 
    """
    LPAREN = pyp.Literal('(')
    RPAREN = pyp.Literal(')')
    LBRACK = pyp.Literal('[')
    RBRACK = pyp.Literal(']')
    SQUOTE = pyp.Literal("'")
    TILDE = pyp.Literal('~')
    DOT = pyp.Literal('.')
    AND = pyp.CaselessLiteral('AND')
    OR  = pyp.CaselessLiteral('OR')
    NOT = pyp.CaselessLiteral('NOT')
    BOOLEANS = AND | OR | NOT
    PLUS = pyp.Literal('+')
    MINUS = pyp.Literal('-')
    
    # Basic word tokens (allow "'" and ":" in token)
    WORD = ~BOOLEANS + pyp.Combine(pyp.Optional(PLUS | MINUS) + \
        pyp.Word(pyp.alphanums + pyp.alphas8bit + "'-:") + \
        pyp.Optional(TILDE))
    # Leave double-quoted strings as a single token
    wTokens = WORD | pyp.dblQuotedString
    
    # Fielded values in any of the forms specified above
    bracketed_field = pyp.Suppress(LBRACK) + WORD + pyp.Suppress(RBRACK)
    dotted_field = pyp.Suppress(DOT) + WORD + pyp.Suppress(DOT)
    bracketed_token = pyp.Group(wTokens + \
        pyp.Suppress(pyp.Optional(pyp.White())) + \
        bracketed_field)
    dotted_token = pyp.Group(wTokens + dotted_field)
    fielded_tokens = bracketed_token | dotted_token
    
    tokens = fielded_tokens | wTokens
    
    # Boolean phrase (may nest)
    bPhrase = pyp.Forward()
    bPhrase << (tokens + BOOLEANS + (tokens | bPhrase))
    
    # Parenthetical phrase (may nest)
    pPhrase = pyp.Forward()
    query_tokens = tokens ^ BOOLEANS ^ bPhrase ^ pPhrase
    pPhrase << LPAREN + pyp.OneOrMore(query_tokens) + RPAREN
    
    # Adding it all up
    query = pyp.ZeroOrMore(query_tokens)
    
    parse_results = query.parseString(s)
    return parse_results[:]


def reassemble_user_query (l):
    """
    Input of the query re-assembly step is the list output of the 
    parsing step. The list is joined using the following patterns:

    * fielded tokens are replaced with their full "lucene form"
        o ('foo', 'ti') becomes 'title:foo' 

    Output of the query re-assembly step is a single string intended,
    in turn, for parsing by lucene's QueryParser. 
    """
    out = []
    for t in l:
        # Re-arrange fielded tokens
        if t.__class__ == pyp.ParseResults:
            field = t[1].lower()
            if field in SEARCH_FIELDS.keys():
                t = '%s:%s' % (SEARCH_FIELDS[field], t[0])
            else:
                t = t[0]
        out.append(t)
    return ' '.join([str(x) for x in out])

class Search:

    FIELDS = [
        'author',
        'title',
        'canary id',
        'unique id',
        'keyword',
        ]
    
    def __init__ (self, field='keyword', token='', allow_curated=True, 
        allow_uncurated=False):
        self.field = field
        self.token = token.strip()
        self.allow_curated = allow_curated
        self.allow_uncurated = allow_uncurated
        
        
    def search (self, context, term_mapping={}):
        results = Results()
        if self.field == '' \
            or self.token == '':
            return results

        cursor = context.get_cursor()
        try:
            if self.field == 'canary id':
                token = int(self.token)
                record = QueuedRecord(context, token)
                results.add_result(record)
            elif self.field == 'keyword':
                select_clause = """
                    SELECT DISTINCT queued_record_metadata.queued_record_id
                    FROM queued_record_metadata, queued_records, studies
                    WHERE queued_record_metadata.queued_record_id = queued_records.uid
                    AND queued_records.study_id = studies.uid
                    """
                if self.allow_curated:
                    if self.allow_uncurated:
                        # Can be anything, no need to restrict
                        pass
                    else:
                        # Should be curated articles only
                        select_clause += ' AND queued_records.status = %s ' % \
                            canary.loader.QueuedRecord.STATUS_CURATED
                        select_clause += ' AND studies.article_type > %s ' % \
                            canary.study.Study.ARTICLE_TYPES['irrelevant']
                else:
                    # Should be uncurated articles only
                    select_clause += ' AND queued_records.status != %s' % \
                        canary.loader.QueuedRecord.STATUS_CURATED

                search_token = '%' + self.token.replace(' ', '% ') + '%'
                cursor.execute(select_clause + """
                    AND value LIKE %s
                    """, search_token
                    )
                rows = cursor.fetchall()
                for row in rows:
                    record = canary.loader.QueuedRecord(context, row[0])
                    results.add_result(record)

            else:
                search_token = self.token + '%'
                if self.field in self.FIELDS \
                    and term_mapping.has_key(self.field):
                    if self.field == 'title':
                        search_token = '%' + search_token
                    
                    select_clause = """
                        SELECT DISTINCT queued_record_metadata.queued_record_id
                        FROM queued_record_metadata, queued_records, studies
                        WHERE queued_record_metadata.queued_record_id = queued_records.uid
                        AND queued_records.study_id = studies.uid
                        AND ("""
                    select_clause += ' OR '.join(['(term_id = %s) ' % \
                        term.uid for term in term_mapping[self.field]])
                    select_clause += ')'
                        
                    if self.allow_curated:
                        if self.allow_uncurated:
                            # Can be anything, no need to restrict
                            pass
                        else:
                            # Should be curated articles only
                            select_clause += ' AND queued_records.status = %s' % \
                                canary.loader.QueuedRecord.STATUS_CURATED
                            select_clause += ' AND studies.article_type > %s ' % \
                                canary.study.Study.ARTICLE_TYPES['irrelevant']
                    else:
                        # Should be uncurated articles only
                        select_clause += ' AND queued_records.status != %s' % \
                            canary.loader.QueuedRecord.STATUS_CURATED
                    
                    cursor.execute(select_clause + ' AND value LIKE %s ', search_token)
                    rows = cursor.fetchall()
                    for row in rows:
                        record = canary.loader.QueuedRecord(context, row[0])
                        results.add_result(record)
        except:
            print 'Unable to perform search'
            import traceback
            print traceback.print_exc()
        
        context.close_cursor(cursor)
        return results


class Results:
    
    def __init__ (self):
        self.records = []
        
    def add_result (self, record):
        self.records.append(record)
        
    def get_results (self):
        return self.records
        
        
        
class PubmedSearch:
    """
    Query/download records from Pubmed, one function per EUtility:
        
        http://eutils.ncbi.nlm.nih.gov/entrez/query/static/eutils_help.html
    """

    def __init__ (self):
        self.efetch_url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=[[UI]]&mode=text&report=medline&tool=canarydb&email=sentinelstudies@yale.edu'
        self.esearch_url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=[[TERMS]]&tool=canarydb&email=sentinelstudies@yale.edu'
    

    def fetch (self, ui):
        """
        Fetch one or more records; ui can be a single ui, or a list of uis.
        
        Returns a single list of text lines to be parsed.
    http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=15148598&mode=text&report=medline
        """

        import types, urllib
        
        try:
            if isinstance(ui, types.ListType):
                url = self.efetch_url.replace('[[UI]]', 
                    (','.join([str(pmid) for pmid in ui])))
            else:
                url = self.efetch_url.replace('[[UI]]', str(ui))
            data = urllib.urlopen(url)
            return data.read().split('\n')
        except:
            return []

    def _get_text (self, p): 
        return ''.join([n.data for n in p.childNodes if n.nodeType==n.TEXT_NODE])

    def search (self, terms):
        """
        Search for a set of terms, returns a list of IDs to parse, which
        is then fed to self.fetch for data retrieval.
        """
        
        import types, urllib
        from xml.dom import pulldom
        
        id_list = []
        
        try:
            if isinstance(terms, types.ListType):
                url = self.esearch_url.replace('[[TERMS]]',
                    urllib.quote_plus((' '.join([str[term] for term in terms]))))
            else:
                url = self.esearch_url.replace('[[TERMS]]', 
                    urllib.quote_plus(str(terms)))
            xmls = urllib.urlopen(url).read()
            events = pulldom.parseString(xmls)
            for event, node in events:
                if event == 'START_ELEMENT' \
                    and node.tagName == 'Id':
                    events.expandNode(node)
                    id = self._get_text(node)
                    id_list.append(id)
        except:
            import traceback
            print traceback.print_exc()
            return []
            
        if len(id_list) > 0:
            return self.fetch(id_list)
        else:
            return []

            

class SearchIndex:
    
    def __init__ (self, context=None):
        self.context = context
        
        
    def index_record (self, record, writer=None):
        # field, value, store?, index?, token?
        try:
            if not writer:
                had_writer = False
                writer = self.context.get_search_index_writer(False)
            else:
                had_writer = True
            
            study = canary.study.Study(self.context, record.study_id)
            
            #print 'starting document'
            doc = PyLucene.Document()
            
            # First, we need to create a unique key so we can later delete
            # if necessary.  Will try simply uid for now.
            doc.add(PyLucene.Field('uid', str(record.uid),
                True, True, False))
            doc.add(PyLucene.Field('all', str(record.uid),
                True, True, False))
            
            # Second, save internal-use metadata.  These should probably
            # be x'd out at Query-time.
            doc.add(PyLucene.Field('record-status', str(record.status),
                False, True, False))
            doc.add(PyLucene.Field('article-type', str(study.article_type),
                False, True, False))
            
            
            source_catalog = self.context.get_source_catalog()
            complete_term_map = source_catalog.get_complete_mapping()
            mapped_metadata = record.get_mapped_metadata(complete_term_map)
            
            # First index all the non-multiple metadata fields
            for field in ('abstract', 'affiliation', 'issn', 
                'journal', 'pubdate', 'issue', 'pages', 'title', 
                'volume'):
                val = mapped_metadata.get(field, None)
                if val:
                    doc.add(PyLucene.Field(field, val,
                        False, True, True))
                    doc.add(PyLucene.Field('all', val,
                        False, True, True))
            
            # If a page range is given, index the first page, assuming
            # the delimiter is '-'
            pages = mapped_metadata.get('pages', None)
            if pages \
                and '-' in pages:
                first_page = pages[0:pages.index('-')]
                doc.add(PyLucene.Field('pages', first_page,
                    False, True, True))
                doc.add(PyLucene.Field('all', first_page,
                    False, True, True))
            
            
            # 'unique_identifier' must be specially treated because 
            # of the '_'
            val = mapped_metadata.get('unique_identifier', None)
            if val:
                doc.add(PyLucene.Field('unique-identifier', val,
                    False, True, True))
                doc.add(PyLucene.Field('all', val,
                    False, True, True))
            
            # Next, index all the possibly-multiple metadata fields
            # Give these (especially for author and subject) a little
            # boost, less than for canary UMLS concepts
            for field in ('author', 'grantnum', 'keyword', 'registrynum', 
                'subject'):
                vals = mapped_metadata.get(field, None)
                for val in vals:
                    doc.add(PyLucene.Field(field, val,
                        False, True, True))
                    f = PyLucene.Field('all', val,
                        False, True, True)
                    f.setBoost(1.3)
                    doc.add(f)
            
            # If at least one author name is available, index the first
            # author to support first-author searching.  Also, boost it
            # slightly higher than the other authors.
            authors = mapped_metadata.get('author', None)
            if authors:
                doc.add(PyLucene.Field('first-author', authors[0],
                    False, True, True))
                f = PyLucene.Field('all', authors[0],
                    False, True, True)
                f.setBoost(1.5)
                doc.add(f)

            
            # All the booleans
            for bool in ('has_outcomes', 'has_exposures', 
                'has_relationships', 'has_interspecies', 
                'has_exposure_linkage', 'has_outcome_linkage', 
                'has_genomic'):
                val = getattr(study, bool)
                # NOTE: I think lucene dislikes '_' in field names ??
                boolstr = bool.replace('_', '-')
                doc.add(PyLucene.Field(boolstr, str(int(val)),
                    False, True, False))
                # NOTE: no need to add this to 'all'.  I think.
            
            # Now, all the UMLS concepts.  Simpler approach to
            # lucene "synonym injection", but it works!  Give it
            # slightly bigger boost than keywords/subjects
            for ctype in ('exposures', 'outcomes', 'risk_factors',
                'species'):
                # NOTE: I think lucene dislikes '_' in field names ??
                ctype.replace('_', '-')
                for val in getattr(study, ctype):
                    concept = Concept(self.context, val.concept_id)
                    for syn in concept.synonyms:
                        doc.add(PyLucene.Field(ctype, unicode(syn, 'latin-1'),
                            False, True, True))
                        f = PyLucene.Field('all', unicode(syn, 'latin-1'),
                            False, True, True)
                        f.setBoost(2.0)
                        doc.add(f)

            # And, the locations
            gazeteer = self.context.get_gazeteer()
            locs = []
            for location in study.locations:
                feature = Feature(self.context, uid=location.feature_id)
                feature.load(self.context)
                if gazeteer.fips_codes.has_key((feature.country_code, feature.adm1)):
                    region_name = gazeteer.fips_codes[(feature.country_code, feature.adm1)]
                else:
                    region_name = ''
                full_name = '%s (%s, %s, %s)' % (feature.name, 
                    gazeteer.feature_codes[feature.feature_type],
                    render_capitalized(region_name), 
                    render_capitalized(gazeteer.country_codes[feature.country_code]))
                doc.add(PyLucene.Field('location', unicode(full_name, 'latin-1'),
                    False, True, True))
                doc.add(PyLucene.Field('all', unicode(full_name, 'latin-1'),
                    False, True, True))
                
            writer.addDocument(doc)
            if not had_writer:
                writer.close()
        except:
            import traceback
            print traceback.print_exc()
        

    def unindex_record (self, record):
        """
        Unindex documents matching this entry's uid.  *Should* 
        only be one, but could be many, if somehow the same entry 
        got indexed multiple times.
        """
        reader = self.context.get_search_index_reader()
        term = Term('uid', str(record.uid))
        reader.deleteDocuments(term)
        reader.close()


    def search (self, query_string='', require_visible=True,
        allow_curated=True):
            
        hits = []
        query_string = str(query_string)
        print 'QS:', query_string
        disassembled_query = disassemble_user_query(query_string)
        print 'DQ:', disassembled_query
        reassembled_query = '+(%s)' % reassemble_user_query(disassembled_query)
        print 'RQ:', reassembled_query
        
        if not allow_curated:
            reassembled_query += \
                ' -record-status:%s' % canary.loader.QueuedRecord.STATUS_CURATED
    
        if require_visible:
            reassembled_query += ' +article-type:[%s TO %s]' % \
                (canary.study.Study.ARTICLE_TYPES['traditional'], 
                canary.study.Study.ARTICLE_TYPES['curated'])
            reassembled_query += ' +record-status:%s' % \
                canary.loader.QueuedRecord.STATUS_CURATED
                
            
        print 'FQ:', reassembled_query
        
        try:
            searcher = PyLucene.IndexSearcher(PyLucene.FSDirectory.getDirectory(
                self.context.config.search_index_dir, False))
            analyzer = StandardAnalyzer()
            query_parser = QueryParser('all', analyzer)
            query_parser.setOperator(QueryParser.DEFAULT_OPERATOR_AND)
            query = query_parser.parseQuery(reassembled_query)
            print 'Query:', query
            hits = searcher.search(query)
            return hits, searcher
        except:
            import traceback
            print traceback.print_exc()
            return hits, searcher

        
    
