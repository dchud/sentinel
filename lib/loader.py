import email
import re
import time
import traceback
import types

import dtuple

from quixote import enable_ptl
enable_ptl()

from canary.source_catalog import Source, Term, SourceCatalog
from canary.utils import DTable


class Queue:

    def __init__ (self):
        self.batches = []
        
    def get_batch (self, batch_id):
        for batch in self.batches:
            if batch.uid == batch_id:
                return batch
        return None
        
    def get_batch_by_name (self, name):
        for batch in self.batches:
            if batch.name == name:
                return batch
        return None

    def load (self, cursor):
        cursor.execute("""
            SELECT *
            FROM queued_batches
            ORDER BY uid, date_added
            """)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        for row in rows:
            row = dtuple.DatabaseTuple(desc, row)
            batch = Batch()
            for field in fields:
                batch.set(field, row[field])
            self.batches.append(batch)


class QueuedRecord (DTable):

    STATUS_UNCLAIMED = 0
    STATUS_CLAIMED = 1
    STATUS_CURATED = 2

    def __init__ (self, uid=-1):
        self.uid = uid
        self.queued_batch_id = -1
        self.user_id = ''
        self.status = self.STATUS_UNCLAIMED
        self.study_id = -1
        self.metadata = {}
        self.title = ''
        self.source = ''
        self.unique_identifier = ''

    def __str__ (self):
        out = []
        out.append('<QueuedRecord uid=%s queued_batch_id=%s' % (self.uid, self.queued_batch_id))
        out.append('\tstatus=%s study_id=%s' % (self.get_status(text=True), self.study_id))
        return '\n'.join(out)


    def add_metadata (self, source_id, term, value, extra=''):
        """
        Add a metadata value for a given source metadata field,
        appending to a list or setting the single value depending
        on whether the term allows multiple values.
        """
        md_key = (source_id, term.uid)
        if term.is_multivalue:
            if self.metadata.has_key(md_key):
                if not value in self.metadata[md_key]:
                    self.metadata[md_key].append(value)
            else:
                self.metadata[md_key] = [value]
        else:
            self.metadata[md_key] = value
            
    
    def get_metadata (self, source_id, term):
        """
        Get the metadata value, of the list of values, for a given sources
        metadata field.
        """
        md_key = (source_id, term.uid)
        if self.metadata.has_key(md_key):
            return self.metadata[md_key]
        else:
            # FIXME: temporary fix, better API would be better
            if not term.is_multivalue:
                return ''
            else:
                return []
            
            
    def get_mapped_metadata (self, term_map={}):
        """
        For every field in this record that is mapped from a specific source,
        return a map to its metadata values.
        
        If an md value comes back == '' or [], it probably doesn't exist for that 
        record and term.  We don't want to clobber things like titles from 
        one source when other source-titles aren't present, so don't overwrite
        values unless value is blank.
        """
        mapped_metadata = {}
        term_info_set = [(mapped_name, term) for mapped_name, term in term_map.items()]
        for mapped_name, terms in term_info_set:
            if isinstance(terms, types.ListType):
                for term in terms:
                    md = self.get_metadata(term.source_id, term)
                    if not md == '' \
                        or md == []:
                        mapped_metadata[mapped_name] = md
            else:
                # terms is really a single item
                term = terms
                md = self.get_metadata(term.source_id, term)
                if not md == '' \
                    or md == []:
                    mapped_metadata[mapped_name] = md
            # Note: only if a mapped-term value hasn't been set at all
            # FIXME: this feels hackish...
            if not mapped_metadata.has_key(mapped_name):
                mapped_metadata[mapped_name] = ''
        return mapped_metadata
        

    def load (self, cursor, load_metadata=True, source=None):
        """
        Load a batch's queued record.
        
        Note that if a source is not specified, every term will be
        looked-up again from the DB (rather than read from memory).
        """
        # To be safe, specify full table.field names because names overlap
        cursor.execute("""
            SELECT queued_records.uid, queued_records.queued_batch_id,
            queued_records.status, queued_records.user_id, 
            queued_records.user_id, queued_records.study_id,
            queued_records.title, queued_records.source,
            queued_records.unique_identifier,
            queued_batches.source_id
            FROM queued_records, queued_batches
            WHERE queued_records.uid = %s
            AND queued_batches.uid = queued_records.queued_batch_id
            """, int(self.uid))
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        row = cursor.fetchone()
        row = dtuple.DatabaseTuple(desc, row)
        # remove source_id from fields, it's not a proper attribute on self
        fields.remove('source_id')
        # but save it for later!
        source_id = row['source_id']
        for field in fields:
            self.set(field, row[field])
            
        if not source:
            source_catalog = SourceCatalog()
            source_catalog.load_sources(cursor)
        if load_metadata:
            cursor.execute("""
                SELECT *
                FROM queued_record_metadata
                WHERE queued_record_id = %s
                AND source_id = %s
                """, (self.uid, source_id))
            fields = [d[0] for d in cursor.description]
            desc = dtuple.TupleDescriptor([[f] for f in fields])
            rows = cursor.fetchall()
            for row in rows:
                row = dtuple.DatabaseTuple(desc, row)
                if source:
                    term = source.terms[row['term_id']]
                else:
                    term = source_catalog.get_term(row['term_id'])
                self.add_metadata(source_id, term, row['value'], row['extra'])
    


    def save (self, cursor):
        
        if self.uid == -1:
            #print 'inserting new record:', self
            cursor.execute("""
                INSERT INTO queued_records
                (uid, 
                queued_batch_id, status, user_id, study_id,
                title, source, unique_identifier)
                VALUES (NULL, 
                %s, %s, %s, %s,
                %s, %s, %s)
                """, (self.queued_batch_id, self.status, self.user_id, self.study_id,
                self.title, self.source, self.unique_identifier)
                )
            self.uid = self.get_new_uid(cursor)

        else:
            cursor.execute("""
                UPDATE queued_records
                SET queued_batch_id = %s, status = %s, user_id = %s, study_id = %s,
                title = %s, source = %s, unique_identifier = %s
                WHERE uid = %s
                """, (self.queued_batch_id, self.status, self.user_id, self.study_id,
                self.title, self.source, self.unique_identifier,
                self.uid)
                )
        # FIXME: should this be set from the SQL?
        self.date_modified = time.strftime(str('%Y-%m-%d'))
        
        cursor.execute("""
            DELETE FROM queued_record_metadata
            WHERE queued_record_id = %s
            """, self.uid)
        for key, val in self.metadata.items():
            # FIXME: extra?
            source_id, term_id = key
            if isinstance(val, types.ListType):
                for value in val:
                    self.save_metadata_value(cursor, source_id, term_id, value)
            else:
                self.save_metadata_value(cursor, source_id, term_id, val)
 
 
    def save_metadata_value (self, cursor, source_id, term_id, value, extra=None):
        # FIXME: extra?
        cursor.execute("""
            INSERT INTO queued_record_metadata
            (uid, queued_record_id, source_id,
            term_id, value, extra)
            VALUES (NULL, %s, %s,
            %s, %s, NULL)
            """, (self.uid, source_id, 
            term_id, value)
            )


    def get_status (self, text=False):
        try:
            status = int(self.status)
        except:
            print 'error w/cast'
        if not text:
            return status
        else:
            if status == self.STATUS_UNCLAIMED:
                return 'unclaimed'
            elif status == self.STATUS_CLAIMED:
                return 'claimed'
            elif status == self.STATUS_CURATED:
                return 'curated'
            else:
                return ''



class Batch (DTable):

    # FIXME: init shouldn't need a damn cursor, write a load() function
    def __init__ (self, uid=-1, file_name='', source_id=-1):
        self.uid = uid
        self.file_name = file_name
        self.source_id = source_id
        self.num_records = 0
        self.name = ''
        self.date_added = ''
        self.queued_records = {}
        self.loaded_records = []


    def add_records (self, records):
        for record in records:
            self.loaded_records.append(record)
            self.num_records += 1
            
    
    def get_statistics (self, cursor):
        """
        Return the state of a Batch based on the number of unclaimed,
        claimed, and finished QueuedRecords it contains.
        """
        stats = {}
        for name, status in [
            ('unclaimed', QueuedRecord.STATUS_UNCLAIMED),
            ('claimed', QueuedRecord.STATUS_CLAIMED),
            ('curated', QueuedRecord.STATUS_CURATED),
            ]:
            cursor.execute("""
                SELECT count(*) as unclaimed_count
                FROM queued_records
                WHERE queued_batch_id = %s
                AND status = %s
                """, (self.uid, status)
                )
            stats[name] = cursor.fetchone()[0]
        stats['total'] = stats['unclaimed'] + stats['claimed'] + stats['curated']
        stats['all'] = stats['total']
        stats['unfinished'] = stats['unclaimed'] + stats['claimed']
        return stats


    def load (self, cursor, show='unfinished', start=0, size=25, load_metadata=True):
        """
        Load a batch and its queued records.
        """
        if self.uid == -1:
            return
            
        cursor.execute("""
            SELECT * 
            FROM queued_batches
            WHERE uid = %s
            """, self.uid)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        for row in rows:
            row = dtuple.DatabaseTuple(desc, row)
            for field in fields:
                self.set(field, row[field])
        
        if show == 'unfinished':
            show_clause = ' AND status < %s ' % QueuedRecord().STATUS_CURATED
        elif show == 'unclaimed':
            show_clause = ' AND status = %s ' % QueuedRecord().STATUS_UNCLAIMED
        elif show == 'all':
            show_clause = ' AND 1 '
            
        cursor.execute("""
            SELECT *
            FROM queued_records
            WHERE queued_batch_id = %s
            """ + show_clause + """
            ORDER BY uid
            LIMIT %s, %s
            """, (int(self.uid), start, size))
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        for row in rows:
            row = dtuple.DatabaseTuple(desc, row)
            record = QueuedRecord()
            for field in fields:
                #print 'record: setting %s to %s' % (field, row[field])
                record.set(field, row[field])
            record.load(cursor, load_metadata)
            #print 'load: adding rec', record.uid
            self.queued_records[record.uid] = record
        self.num_records = len(self.queued_records)
        #print 'loaded %s queued_records for batch %s' % (self.num_records, self.uid)


    def save (self, cursor):
        
        if self.uid == -1:
            cursor.execute("""
                INSERT INTO queued_batches
                (uid, file_name, source_id, num_records, name, 
                date_added)
                VALUES
                (NULL, %s, %s, %s, %s, 
                CURDATE())
                """, (self.file_name, self.source_id, self.num_records, self.name)
                )
            cursor.execute("""
                SELECT LAST_INSERT_ID() AS new_uid
                """)
            row = cursor.fetchone()
            self.uid = row[0]
            self.date_added = time.strftime(str('%Y-%m-%d'))

        else:
            cursor.execute("""
                UPDATE queued_batches
                SET file_name = %s, num_records = %s, name = %s, source_id = %s
                WHERE uid = %s
                """, (self.file_name, self.num_records, self.name, self.source_id,
                self.uid)
                )
        
        for record in self.loaded_records:
            record.queued_batch_id = self.uid
            record.save(cursor)



class Parser:

    def __init__ (self, source=None):
        self.re_result_sep = re.compile(source.re_result_sep)
        self.re_term_token = re.compile(source.re_term_token)
        self.source = source


    def parse (self, file_name='', mapped_terms={}, is_email=True, data=[]):
        lines = data
        if lines == [] \
            and not file_name =='':
            try:
                file = open(file_name)
                if is_email:
                    data = email.message_from_file(file)
                    lines = data.get_payload().split('\n')
                else:
                    lines = file.read().split('\n')
                file.close()
            except:
                print 'unable to load file, or msg'
                return []
        
        records = []
        value = ''
        current_token = current_value = ''
        current_record = QueuedRecord()
        for line in lines:
            try:
                if self.re_result_sep.match(line):
                    # Matches record separator, so is either first record or new record
                    if len(current_record.metadata) > 0:
                        # Must be new record, but don't miss last token/value for current_record
                        self._add_metadata(current_token, current_value, current_record)
                        mapped_metadata = current_record.get_mapped_metadata(mapped_terms)
                        current_record.title = mapped_metadata['title']
                        current_record.source = mapped_metadata['source']
                        current_record.unique_identifier = mapped_metadata['unique_identifier']
                        records.append(current_record)
                        current_token = current_value = ''
                        current_record = QueuedRecord()
                else:
                    # More info for current_record
                    match = self.re_term_token.match(line)
                    if match:
                        # Line contains token, i.e. is start of value
                        # Note: match.group(0) == line  (damn that snake!)
                        token = match.group(1)
                        value = match.group(2)
                        self._add_metadata(current_token, current_value, current_record)
                        current_token = token
                        current_value = value
                    else:
                        # Line does not contain token, i.e. is value cont'd or blank
                        if not line.strip() == '':
                            # Line isn't blank, so it continues a value
                            current_value = current_value + ' ' + line.strip()
                        else:
                            # blank line
                            pass
            except:
                print 'failed on line: "%s"' % line
                continue
            
        # Note: we don't catch the last record in the loop above,
        # so do it 'manually' here
        if not current_record == None \
            and not current_record.metadata == {}:
            self._add_metadata(current_token, current_value, current_record)
            mapped_metadata = current_record.get_mapped_metadata(mapped_terms)
            current_record.title = mapped_metadata['title']
            current_record.source = mapped_metadata['source']
            current_record.unique_identifier = mapped_metadata['unique_identifier']
            records.append(current_record)
        return records


    def _add_metadata (self, token, value, record):
        term = self.source.get_term_from_token(token)
        if term:
            if term.is_multivalue \
                and not term.re_multivalue_sep == '':
                values = value.split(term.re_multivalue_sep)
                for val in values:
                    record.add_metadata(self.source.uid, term, val.strip())
            else:
                record.add_metadata(self.source.uid, term, value)
                    

if __name__ == '__main__':

    source = Source()
    source.re_result_sep = '^<.*>'
    source.re_term_token = '^([A-Z][A-Z]+) +-[ ](.*)'

    parser = Parser(source)
    records = parser.parse('/home/dlc33/projects/sentinel/record_parser/test-data/ovid-medline-12.txt')
    print len(records), 'records:'
    print records
    
    

