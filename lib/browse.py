# browse.py

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



def records_by_journal (nlm_journal_code, cursor):
    results = []
    cursor.execute("""
        SELECT authors, title, source, pubmed_id
        FROM sentinel_studies
        WHERE nlm_journal_code = %s
        """, nlm_journal_code)
    while 1:
        row = cursor.fetchone()
        if row == None: break
        results.append((row[0], row[1], row[2], row[3]))
    return results


def records_by_journal_index (cursor):

    cursor.execute("""
        SELECT source, nlm_journal_code, COUNT(*)
        FROM sentinel_studies
        GROUP BY nlm_journal_code
        ORDER BY source
        """)
    results = []
    while 1:
        row = cursor.fetchone()
        if row == None: break
        results.append((row[0], row[1], row[2]))
    return results



def records_by_study_type (s_type, cursor):
    results = []
    cursor.execute("""
        SELECT reference_id
        FROM reference_methodology
        WHERE methodology = %s
        """, s_type)
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


def records_by_study_type_index (cursor):

    cursor.execute("""
        SELECT methodology, COUNT(methodology) as mcount
        FROM reference_methodology
        GROUP BY methodology
        """)
    results = []
    while 1:
        row = cursor.fetchone()
        if row == None: break
        results.append((row[0], row[1]))

    return results



def records_by_year (year, cursor):
    results = []
    cursor.execute("""
        SELECT authors, title, source, pubmed_id
        FROM sentinel_studies
        WHERE year_published = %s
        """, year)
    while 1:
        row = cursor.fetchone()
        if row == None: break
        results.append((row[0], row[1], row[2], row[3]))
    return results


def records_by_year_index (cursor):

    cursor.execute("""
        SELECT year_published, COUNT(year_published) AS yearcount
        FROM sentinel_studies
        GROUP BY year_published
        ORDER BY year_published DESC
        """)
    results = []
    while 1:
        row = cursor.fetchone()
        if row == None: break
        results.append((row[0], row[1]))
    return results
