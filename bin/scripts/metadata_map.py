#!/usr/bin/env python2.4

from canary.context import Context

context = Context()
cursor = context.get_cursor()

cursor.execute(\
    """
    SELECT sources.name, T1.name, T1.token, T2.name, T2.token 
    FROM terms T1
    LEFT JOIN terms T2 ON T1.mapped_term_id = T2.uid
    INNER JOIN sources ON T1.source_id = sources.uid
    WHERE T1.source_id != 12
    ORDER BY sources.name, T1.name
    """)

last_source = ""
for row in cursor.fetchall():

    if last_source == "" or last_source != row[0]:
        print "\n%s" % row[0]
        print "-" * len(row[0])

    source = row[1] + " [" + row[2] + "]"
    mapped = "None"
    if row[3] and row[4]:
        mapped = row[3] + " [" + row[4] + "]"

    print "%-40s %-30s" % (source, mapped)
    last_source = row[0]

