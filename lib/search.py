
from canary.loader import QueuedRecord


class Search:

    FIELDS = [
        'author',
        'title',
        'record id',
        'unique id',
        ]
    
    def __init__ (self, field='', token='', allow_curated=False):
        self.field = field
        self.token = token
        self.allow_curated = allow_curated
        
        
    def search (self, cursor, term_mapping={}):
        results = Results()
        if self.field == '' \
            or self.token == '':
            return results

        try:
            if self.field == 'record id':
                token = int(self.token)
                record = QueuedRecord(token)
                record.load(cursor)
                results.add_result(record)
            else:
                search_token = self.token + '%'
                if self.field in self.FIELDS \
                    and term_mapping.has_key(self.field):
                    if self.field == 'title':
                        search_token = '%' + search_token
                    
                    select_clause = """
                        SELECT queued_record_id
                        FROM queued_record_metadata
                        WHERE ("""
                    select_clause += ' OR '.join(['(source_id = %s AND term_id = %s) ' % \
                        (term.source_id, term.uid) for term in term_mapping[self.field]])
                    
                    cursor.execute(select_clause + """)
                        AND value LIKE %s
                        """, (search_token)
                        )
                    rows = cursor.fetchall()
                    for row in rows:
                        record = QueuedRecord(row[0])
                        record.load(cursor)
                        if self.allow_curated:
                            results.add_result(record)
                        elif not record.status == record.STATUS_CURATED:
                            results.add_result(record)
        except:
            print 'Unable to perform search'
        
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
            print 'url:', url
            xmls = urllib.urlopen(url).read()
            events = pulldom.parseString(xmls)
            for event, node in events:
                if event == 'START_ELEMENT' \
                    and node.tagName == 'Id':
                    print 'found Id'
                    events.expandNode(node)
                    id = self._get_text(node)
                    print 'adding id:', id
                    id_list.append(id)
        except:
            return []
            
        if len(id_list) > 0:
            return self.fetch(id_list)
        else:
            return []

            
