
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
        # NOTE: should this be consistent with the concept search screens?
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
        self.efetch_url = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=[[UI]]&mode=text&report=medline'

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
