# browse.py


from canary.loader import QueuedRecord

def records_by_heading (term, cursor):
    results = []
    # GROUP BY reference_id because some terms repeat w/diff qualifiers
    cursor.execute("""
        SELECT reference_id
        FROM reference_mesh
        WHERE term = %s
        GROUP BY reference_id
        """, term)
    id_rows = cursor.fetchall()
    for id_row in id_rows:
        cursor.execute("""
            SELECT authors, title, source, pubmed_id
            FROM sentinel_studies
            WHERE reference_id = %s
            """, id_row[0])
        while 1:
            row = cursor.fetchone()
            if row == None: break
            results.append((row[0], row[1], row[2], row[3]))
    return results


def records_by_heading_index (cursor):

    cursor.execute("""
        SELECT term, COUNT(term) as termcount, COUNT(DISTINCT reference_id) AS idcount
        FROM reference_mesh
        GROUP BY term
        HAVING COUNT(term) > 4
        ORDER BY idcount DESC, term
        """)
    results = []
    while 1:
        row = cursor.fetchone()
        if row == None: break
        results.append((row[0], row[1], row[2]))
    return results


# NOTE: queued_record.status is hard-coded to 2
def records_by_journal (cursor, issn, term_map={}):
    journal_title = ''
    queued_records = []
    issn_terms = term_map['issn']
    issn_clause = ' OR '.join(['queued_record_metadata.term_id=%s' % term.uid for term in issn_terms])
    
    cursor.execute("""
        SELECT journal_title
        FROM medline_journals
        WHERE issn = %s
        """, issn)
    try:
        rows = cursor.fetchall()
        if len(rows) != 1:
            raise Exception('Journal not found')
        
        journal_title = rows[0][0]
        
        select_clause = """
            SELECT queued_records.uid
            FROM queued_records, queued_record_metadata, studies
            WHERE queued_record_metadata.queued_record_id = queued_records.uid
            AND queued_records.uid = studies.record_id
            AND queued_records.status = 2
            AND studies.article_type >= 2
            AND (%s)
            """ % issn_clause
        #print 'sql:', select_clause
        cursor.execute(select_clause + """
            AND queued_record_metadata.value = %s
            """, issn
            )
        while 1:
            row = cursor.fetchone()
            if row == None: break
            queued_record = QueuedRecord(row[0])
            queued_records.append(queued_record)
        for queued_record in queued_records:
            queued_record.load(cursor)
    except:
        import traceback
        print traceback.print_exc()
    return journal_title, queued_records


def records_by_journal_index (cursor, term_map={}):
    results = []
    issn_terms = term_map['issn']
    issn_clause = ' OR '.join(['term_id=%s' % term.uid for term in issn_terms])
    select_clause = """
        SELECT COUNT(*) AS the_count, value, journal_title, abbreviation
        FROM queued_record_metadata, queued_records, medline_journals, studies
        WHERE queued_record_metadata.queued_record_id = queued_records.uid
        AND queued_record_metadata.value = medline_journals.issn
        AND queued_records.uid = studies.record_id
        AND queued_records.status = 2
        AND studies.article_type >= 2
        AND (%s)
        GROUP BY value
        ORDER BY journal_title
        """ % issn_clause
    cursor.execute(select_clause)
    while 1:
        row = cursor.fetchone()
        if row == None: break
        results.append((row[0], row[1], row[2], row[3]))
    return results




def records_by_methodology (cursor, methodology_id):
    queued_records = []
    
    try:
        cursor.execute("""
            SELECT queued_records.uid
            FROM queued_records, studies, methodologies
            WHERE queued_records.uid = studies.record_id
            AND studies.uid = methodologies.study_id
            AND queued_records.status = 2
            AND studies.article_type >= 2
            AND methodologies.study_type_id = %s        
            """, methodology_id
            )
        while 1:
            row = cursor.fetchone()
            if row == None: break
            queued_record = QueuedRecord(row[0])
            queued_records.append(queued_record)
        for queued_record in queued_records:
            queued_record.load(cursor)
    except:
        import traceback
        print traceback.print_exc()
    return queued_records


def records_by_methodology_index (cursor):

    cursor.execute("""
        SELECT study_type_id, COUNT(study_type_id) as the_count
        FROM methodologies, studies, queued_records
        WHERE methodologies.study_id = studies.uid
        AND studies.record_id = queued_records.uid
        AND queued_records.status = 2
        AND studies.article_type >= 2
        GROUP BY study_type_id
        """)
    results = []
    while 1:
        row = cursor.fetchone()
        if row == None: break
        results.append((row[0], row[1]))

    return results



def records_by_year (cursor, year, term_map={}):
    queued_records = []
    year_terms = term_map['pubdate']
    year_clause = ' OR '.join(['queued_record_metadata.term_id=%s' % term.uid for term in year_terms])
    
    try:
        select_clause = """
            SELECT queued_records.uid
            FROM queued_records, queued_record_metadata, studies
            WHERE queued_records.uid = queued_record_metadata.queued_record_id
            AND queued_records.uid = studies.record_id
            AND queued_records.status = 2
            AND studies.article_type >= 2
            AND (%s)
            """ % year_clause
        #print 'sql:', select_clause
        cursor.execute(select_clause + """
            AND SUBSTRING(queued_record_metadata.value, 1, 4) LIKE %s
            """, str(year) + '%'
            )
        while 1:
            row = cursor.fetchone()
            if row == None: break
            queued_record = QueuedRecord(row[0])
            queued_records.append(queued_record)
        for queued_record in queued_records:
            queued_record.load(cursor)
    except:
        import traceback
        print traceback.print_exc()
    return queued_records


def records_by_year_index (cursor, term_map={}):

    results = []
    year_terms = term_map['pubdate']
    year_clause = ' OR '.join(['term_id=%s' % term.uid for term in year_terms])
    
    select_clause = """
        SELECT COUNT(*) AS the_count, SUBSTRING(value, 1, 4) AS the_year
        FROM queued_record_metadata, queued_records, studies
        WHERE queued_record_metadata.queued_record_id = queued_records.uid
        AND queued_records.uid = studies.record_id
        AND queued_records.status = 2
        AND studies.article_type >= 2
        AND (%s)
        GROUP BY SUBSTRING(value, 1, 4)
        ORDER BY value DESC
        """ % year_clause
    cursor.execute(select_clause)
    while 1:
        row = cursor.fetchone()
        if row == None: break
        results.append((row[0], row[1]))
    return results
