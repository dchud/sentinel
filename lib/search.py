
from canary.loader import QueuedRecord


class Search:

    # FIXME: what are you thinking, make it dynamic!!!!
    FIELDS = {
        'author': (10, 22),
        'title': (10, 79),
        'unique id': (10, 62)
        }
        
    def __init__ (self, field='', token='', allow_curated=False):
        self.field = field
        self.token = token
        self.allow_curated = allow_curated
        
        
    def search (self, cursor):
        
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
                if self.field in self.FIELDS.keys():
                    source_id, term_id = self.FIELDS[self.field]
                    cursor.execute("""
                        SELECT queued_record_id
                        FROM queued_record_metadata
                        WHERE source_id = %s
                        AND term_id = %s
                        AND value LIKE %s
                        """, (source_id, term_id, search_token)
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
