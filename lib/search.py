# $Id$

import PyLucene
from PyLucene import Field, Term, Document
from PyLucene import QueryParser, IndexSearcher, StandardAnalyzer, FSDirectory

from canary.concept import Concept
import canary.context
from canary.gazeteer import Feature
from canary.loader import QueuedRecord
from canary.study import Study
from canary.utils import render_capitalized


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
        
        
    def search (self, term_mapping={}):
        results = Results()
        if self.field == '' \
            or self.token == '':
            return results

        context = canary.context.Context()
        cursor = context.get_cursor()
        try:
            if self.field == 'canary id':
                token = int(self.token)
                record = QueuedRecord(token)
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
                        select_clause += ' AND queued_records.status = %s ' % QueuedRecord.STATUS_CURATED
                        select_clause += ' AND studies.article_type > %s ' % Study.ARTICLE_TYPES['irrelevant']
                else:
                    # Should be uncurated articles only
                    select_clause += ' AND queued_records.status != %s' % QueuedRecord.STATUS_CURATED

                search_token = '%' + self.token.replace(' ', '% ') + '%'
                cursor.execute(select_clause + """
                    AND value LIKE %s
                    """, search_token
                    )
                rows = cursor.fetchall()
                for row in rows:
                    record = QueuedRecord(row[0])
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
                            select_clause += ' AND queued_records.status = %s' % QueuedRecord.STATUS_CURATED
                            select_clause += ' AND studies.article_type > %s ' % Study.ARTICLE_TYPES['irrelevant']
                    else:
                        # Should be uncurated articles only
                        select_clause += ' AND queued_records.status != %s' % QueuedRecord.STATUS_CURATED
                    
                    cursor.execute(select_clause + ' AND value LIKE %s ', search_token)
                    rows = cursor.fetchall()
                    for row in rows:
                        record = QueuedRecord(row[0])
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
            return []
            
        if len(id_list) > 0:
            return self.fetch(id_list)
        else:
            return []

            

class SearchIndex:
    
    def __init__ (self, context=None):
        self.context = canary.context.Context()
        
        
    def index_record (self, record, writer=None):
        # field, value, store?, index?, token?
        try:
            if not writer:
                had_writer = False
                writer = self.context.get_search_index_writer(False)
            else:
                had_writer = True
            
            study = Study(record.study_id)
            
            print 'starting document'
            doc = PyLucene.Document()
            
            # First, we need to create a unique key so we can later delete
            # if necessary.  Will try simply uid for now.
            doc.add(PyLucene.Field('uid', str(record.uid),
                True, True, False))
            doc.add(PyLucene.Field('all', str(record.uid),
                True, True, False))
            
            source_catalog = self.context.get_source_catalog()
            complete_term_map = source_catalog.get_complete_mapping()
            mapped_metadata = record.get_mapped_metadata(complete_term_map)
            
            # First index all the non-multiple metadata fields
            for field in ('abstract', 'affiliation', 'grantnum', 'issn', 
                'journal', 'pubdate', 'issue', 'pages', 'title', 
                'unique_identifier', 'volume'):
                val = mapped_metadata.get(field, None)
                if val:
                    doc.add(PyLucene.Field(field, val,
                        False, True, True))
                    doc.add(PyLucene.Field('all', val,
                        False, True, True))
            
            # Next, index all the possibly-multiple metadata fields
            # Give these (especially for author and subject) a little
            # boost, less than for canary UMLS concepts
            for field in ('author', 'keyword', 'registrynum', 'subject'):
                vals = mapped_metadata.get(field, None)
                for val in vals:
                    doc.add(PyLucene.Field(field, val,
                        False, True, True))
                    f = PyLucene.Field('all', val,
                        False, True, True)
                    f.setBoost(1.1)
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
                for val in getattr(study, ctype):
                    concept = Concept(val.concept_id)
                    for syn in concept.synonyms:
                        doc.add(PyLucene.Field(ctype, syn,
                            False, True, True))
                        f = PyLucene.Field('all', syn,
                            False, True, True)
                        f.setBoost(1.2)
                        doc.add(f)

            # And, the locations
            gazeteer = self.context.get_gazeteer()
            locs = []
            for location in study.locations:
                feature = Feature(uid=location.feature_id)
                feature.load()
                if gazeteer.fips_codes.has_key((feature.country_code, feature.adm1)):
                    region_name = gazeteer.fips_codes[(feature.country_code, feature.adm1)]
                else:
                    region_name = ''
                full_name = '%s (%s, %s, %s)' % (feature.name, 
                    gazeteer.feature_codes[feature.feature_type],
                    render_capitalized(region_name), 
                    render_capitalized(gazeteer.country_codes[feature.country_code]))
                doc.add(PyLucene.Field('location', full_name,
                    False, True, True))
                doc.add(PyLucene.Field('all', full_name,
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
        term = Term('uid', record.uid)
        reader.deleteDocuments(term)
        reader.close()


    def search (self, query_string=''):
        hits = []
        query_string = str(query_string)
        try:
            searcher = PyLucene.IndexSearcher(PyLucene.FSDirectory.getDirectory(
                self.context.config.search_index_dir, False))
            analyzer = StandardAnalyzer()
            query = QueryParser.parse(query_string, 'all', analyzer)
            print 'Query:', query
            hits = searcher.search(query)
            return hits, searcher
        except:
            import traceback
            print traceback.print_exc()
            return hits, searcher

        
    
