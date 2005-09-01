# $Id$

import canary.context
from canary.loader import QueuedRecord


def records_by_heading (context, term):
    results = []
    # GROUP BY reference_id because some terms repeat w/diff qualifiers
    cursor = context.get_cursor()
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
        rows = cursor.fetchall()
        for row in rows:
            results.append((row[0], row[1], row[2], row[3]))
    context.close_cursor(cursor)
    return results


def records_by_heading_index (context):

    cursor = context.get_cursor()
    cursor.execute("""
        SELECT term, COUNT(term) as termcount, COUNT(DISTINCT reference_id) AS idcount
        FROM reference_mesh
        GROUP BY term
        HAVING COUNT(term) > 4
        ORDER BY idcount DESC, term
        """)
    results = []
    rows = cursor.fetchall()
    for row in rows:
        if row == None: break
        results.append((row[0], row[1], row[2]))
    context.close_cursor(cursor)
    return results


# NOTE: queued_record.status is hard-coded to 2
def records_by_journal (context, issn, term_map={}):
    journal_title = ''
    queued_records = []
    issn_terms = term_map['issn']
    issn_clause = ' OR '.join(['queued_record_metadata.term_id=%s' % term.uid for term in issn_terms])
    
    cursor = context.get_cursor()
    cursor.execute("""
        SELECT journal_title
        FROM medline_journals
        WHERE issn = %s
        """, issn)
    try:
        rows = cursor.fetchall()
        if len(rows) != 1:
            raise Exception('Journal %s not found' % issn)
        
        journal_title = rows[0][0]
        
        select_clause = """
            SELECT queued_records.uid
            FROM queued_records, queued_record_metadata, studies
            WHERE queued_record_metadata.queued_record_id = queued_records.uid
            AND queued_records.uid = studies.record_id
            AND queued_records.status = 2
            AND studies.article_type >= 2
            AND studies.article_type < 8
            AND (%s)
            """ % issn_clause
        cursor.execute(select_clause + """
            AND queued_record_metadata.value = %s
            """, issn
            )
        rows = cursor.fetchall()
        for row in rows:
            queued_record = QueuedRecord(context, row[0])
            queued_records.append(queued_record)
    except Exception, e:
        context.logger.error('Records by journal: %s', e)
    
    context.close_cursor(cursor)
    return journal_title, queued_records


def records_by_journal_index (context,term_map={}):
    cursor = context.get_cursor()
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
        AND studies.article_type < 8
        AND (%s)
        GROUP BY value
        ORDER BY journal_title
        """ % issn_clause
    cursor.execute(select_clause)
    rows = cursor.fetchall()
    for row in rows:
        results.append((row[0], row[1], row[2], row[3]))
    context.close_cursor(cursor)
    return results




def records_by_methodology (context, methodology_id):
    queued_records = []
    
    cursor = context.get_cursor()
    try:
        cursor.execute("""
            SELECT queued_records.uid
            FROM queued_records, studies, methodologies
            WHERE queued_records.uid = studies.record_id
            AND studies.uid = methodologies.study_id
            AND queued_records.status = 2
            AND studies.article_type >= 2
            AND studies.article_type < 8
            AND methodologies.study_type_id = %s        
            """, methodology_id
            )
        rows = cursor.fetchall()
        for row in rows:
            queued_record = QueuedRecord(context, row[0])
            queued_records.append(queued_record)
    except Exception, e:
        context.logger.error('Records by methodology: %s', e)
        
    context.close_cursor(cursor)
    return queued_records


def records_by_methodology_index (context):
    cursor = context.get_cursor()
    cursor.execute("""
        SELECT study_type_id, COUNT(study_type_id) as the_count
        FROM methodologies, studies, queued_records
        WHERE methodologies.study_id = studies.uid
        AND studies.record_id = queued_records.uid
        AND queued_records.status = 2
        AND studies.article_type >= 2
        AND studies.article_type < 8
        GROUP BY study_type_id
        """)
    results = []
    rows = cursor.fetchall()
    for row in rows:
        results.append((row[0], row[1]))

    context.close_cursor(cursor)
    return results



def records_by_year (context, year, term_map={}):
    cursor = context.get_cursor()
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
            AND studies.article_type < 8
            AND (%s)
            """ % year_clause
        cursor.execute(select_clause + """
            AND SUBSTRING(queued_record_metadata.value, 1, 4) LIKE %s
            """, str(year) + '%'
            )
        rows = cursor.fetchall()
        for row in rows:
            queued_record = QueuedRecord(context, row[0])
            queued_records.append(queued_record)
    except Exception, e:
        context.logger.error('Records by year: %s', e)
        
    context.close_cursor(cursor)
    return queued_records


def records_by_year_index (context, term_map={}):
    cursor = context.get_cursor()
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
        AND studies.article_type < 8
        AND (%s)
        GROUP BY SUBSTRING(value, 1, 4)
        ORDER BY value DESC
        """ % year_clause
    cursor.execute(select_clause)
    rows = cursor.fetchall()
    for row in rows:
        results.append((row[0], row[1]))
    context.close_cursor(cursor)
    return results


def records_by_author (context, author):
    cursor = context.get_cursor()
    queued_records = []
    source_catalog = context.get_source_catalog()
    complete_mapping = source_catalog.get_complete_mapping()
    term_list = complete_mapping['author']
    term_clause = ' OR '.join(['queued_record_metadata.term_id=%s' % term.uid for term in term_list])
    
    try:
        select_clause = """
            SELECT queued_records.uid
            FROM queued_records, queued_record_metadata, studies
            WHERE queued_records.uid = queued_record_metadata.queued_record_id
            AND queued_records.uid = studies.record_id
            AND queued_records.status = 2
            AND studies.article_type >= 2
            AND studies.article_type < 8
            AND (%s)
            """ % term_clause
        cursor.execute(select_clause + """
            AND value LIKE %s
            """, str(author) + '%'
            )
        rows = cursor.fetchall()
        for row in rows:
            queued_record = QueuedRecord(context, row[0])
            queued_records.append(queued_record)
    except Exception, e:
        context.logger.error('Records by author: %s', e)
        
    context.close_cursor(cursor)
    return queued_records


def records_by_author_index (context):
    cursor = context.get_cursor()
    results = []
    source_catalog = context.get_source_catalog()
    complete_mapping = source_catalog.get_complete_mapping()
    term_list = complete_mapping['author']
    term_clause = ' OR '.join(['term_id=%s' % term.uid for term in term_list])
    
    select_clause = """
        SELECT COUNT(*) AS the_count, value
        FROM queued_record_metadata, queued_records, studies
        WHERE queued_record_metadata.queued_record_id = queued_records.uid
        AND queued_records.uid = studies.record_id
        AND queued_records.status = 2
        AND studies.article_type >= 2
        AND studies.article_type < 8
        AND (%s)
        GROUP BY value
        ORDER BY value
        """ % term_clause
    cursor.execute(select_clause)
    rows = cursor.fetchall()
    results.extend([(r[0], r[1]) for r in rows])
    context.close_cursor(cursor)
    return results





concept_tables = {
    'exposure': 'exposures',
    'outcome':  'outcomes',
    'species':  'species',
    'risk_factor':  'risk_factors',
    }


def records_by_concept (context, concept, concept_id):
    cursor = context.get_cursor()
    queued_records = []
    table_name = concept_tables[concept]
    try:
        select_clause = """
            SELECT queued_records.uid
            FROM queued_records, studies, %s
            WHERE %s.study_id = studies.uid
            AND studies.record_id = queued_records.uid
            AND %s.concept_id = %s
            AND queued_records.status = 2
            AND studies.article_type >= 2
            AND studies.article_type < 8
            """ % (table_name, 
                table_name,
                table_name, concept_id)
        cursor.execute(select_clause)
        rows = cursor.fetchall()
        for row in rows:
            queued_record = QueuedRecord(context, row[0])
            queued_records.append(queued_record)
    except Exception, e:
        context.logger.error('Records by concept: %s', e)
        
    context.close_cursor(cursor)
    return queued_records
    

def records_by_concept_index (context, concept):
    cursor = context.get_cursor()
    results = []
    table_name = concept_tables[concept]
    
    select_clause = """
        SELECT COUNT(concept_id) AS the_count, concept_id, term
        FROM %s, studies, queued_records
        WHERE %s.study_id = studies.uid
        AND studies.record_id = queued_records.uid
        AND queued_records.uid = studies.record_id
        AND queued_records.status = 2
        AND studies.article_type >= 2
        AND studies.article_type < 8
        GROUP BY concept_id
        ORDER BY term
        """ % (table_name, table_name)
    cursor.execute(select_clause)
    rows = cursor.fetchall()
    results.extend([(r[0], r[1], r[2]) for r in rows])
    context.close_cursor(cursor)
    return results
