"""
source_catalog.py

A generic framework for managing literature database sources for the
Canary Database Project.

A SourceCatalog is a master in-memory implementation of the entire set
of sources, source versions, terms, and vocabulary references and should
be initialized from a database at application initialization.

A CatalogItem is a simple superclass for elements common to types found
within a SourceCatalog.  It provides a baseline of functions which any
item type should implement.

The main goal of the SourceCatalog is to enable the project to have generic
access to any record from any of the literature sources used, and to know
enough about parsing those records, and what their fields mean, to be
useful into the future.  SourceVersions attempt to capture point-in-time
snapshots of a single source because source terms change over time (roughly
annually at most), and should be usable to help meaningfully read a record
loaded at some point in the past where its source had a significantly
different set of terms than those defined at the later time of reading.

daniel.chudnov@yale.edu
"""

import dtuple
import time

from canary.utils import DTable


class SourceCatalog:

    def __init__ (self):
        self.sources = {}
        self.terms = {}
        self.vocabularies = {}

    def add_source (self, source):
        self.sources[source.uid] = source

    def get_source (self, id):
        try:
            uid = int(id)
            if self.sources.has_key(uid):
                return self.sources[uid]
            else:
                return None
        except:
            return None

    def get_source_by_name (self, name):
        '''
        Convenience function for grabbing sources.  Assume it should never be
        too slow as we'll likely never have more than a few dozen sources.
        '''
        for source_uid in self.sources.keys():
            source = self.sources[source_uid]
            if name.lower() == source.name.lower():
                return source
        return None

    def delete_source (self, cursor, id):
        try:
            uid = int(id)
            if self.sources.has_key(uid):
                source = self.sources[uid]
                for term_id in source.terms.keys():
                    source.delete_term(cursor, term_id)
                cursor.execute("""
                               DELETE FROM sources
                               WHERE uid = %s
                               """, id)
                # FIXME: should we bother here? probably, just to be thorough,
                # although ui should reload source_catalog after any change.
                del(self.sources[id])
        except:
            return

    def get_term (self, id):
        try:
            uid = int(id)
            if self.terms.has_key(uid):
                return self.terms[uid]
            else:
                return None
        except:
            return None

    def delete_term (self, cursor, id):
        try:
            uid = int(id)
            if self.terms.has_key(uid):
                term = self.terms[uid]
                source = self.get_source(term.source_uid)
                source.delete_term(cursor, uid)
        except:
            return

    def load_sources (self, cursor, load_terms=True):
        sources = {}
        # this two-step is redundant, but lets us use source's dynamic
        # field-name-setting load() function.
        cursor.execute('SELECT uid FROM sources')
        rows = cursor.fetchall()
        for row in rows:
            source = Source(uid=row[0])
            source.load(cursor, load_terms=load_terms)
            self.sources[source.uid] = source

        for source_id in self.sources.keys():
            source = self.sources[source_id]
            source.load(cursor, load_terms=load_terms)
            self.sources[source_id] = source
            # index the terms by id if they were loaded
            if load_terms:
                term_ids = source.terms.keys()
                for term_uid in term_ids:
                    #print 'adding term_uid %s to catalog %s' % (term_uid,
                    #                                            source.terms[term_uid])
                    self.terms[term_uid] = source.terms[term_uid]


class CatalogItem (DTable):

    def __init__ (self, uid=-1, name='', description='', date_modified=''):
        self.uid = uid
        self.name = name
        self.description = description
        #if date_modified == '':
        #    self.date_modified = '%s-%s-%s' % (yr, mo, day)


    """
    Subclasses should implement.
    """
    def load (self):
        pass

    """
    Subclasses should implement.
    """
    def save (self):
        pass



class Source (CatalogItem):

    def __init__ (self, uid=-1, name='', description='', date_modified=''):
        CatalogItem.__init__(self,
                             uid=uid,
                             name=name,
                             description=description,
                             date_modified=date_modified)
        self.terms = {}
        self.term_tokens = {}
        self.re_result_sep = ''
        self.re_term_token = ''
        self.version_uid = -1
        self.date_modified = None


    def load (self, cursor, load_terms=True):
        if self.uid == -1:
            return

        cursor.execute("""
                       SELECT *
                       FROM sources
                       WHERE uid = %s
                       """, self.uid)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        if rows and len(rows) > 0:
            row = dtuple.DatabaseTuple(desc, rows[0])
            for field in fields:
                self.set(field, row[field])

        if not load_terms:
            return

        cursor.execute("""
                       SELECT *
                       FROM terms
                       WHERE source_uid = %s
                       """, self.uid)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        for row in rows:
            row = dtuple.DatabaseTuple(desc, row)
            term = Term()
            for field in fields:
                term.set(field, row[field])
            #print 'adding term %s to source %s' % (term.uid, self.uid)
            self.terms[term.uid] = term
            self.term_tokens[term.token] = term.uid


    def save (self, cursor):
        if self.uid == -1:
            cursor.execute("""
                           INSERT INTO sources
                           (uid, name, description, date_modified,
                           re_result_sep, re_term_token)
                           VALUES (NULL, %s, %s, CURDATE(),
                           %s, %s)
                           """, (self.name, self.description,
                                 self.re_result_sep, self.re_term_token))
        else:
            cursor.execute("""
                           UPDATE sources
                           SET name = %s, description = %s, date_modified = CURDATE(),
                           re_result_sep = %s, re_term_token = %s
                           WHERE uid = %s
                           """, (self.name, self.description,
                                 self.re_result_sep, self.re_term_token,
                                 self.uid))
        # FIXME: should this be set from the SQL?
        self.date_modified = time.strftime(str('%Y-%m-%d'))


    def delete_term (self, cursor, id):
        if id > -1:
            cursor.execute("""
                           DELETE FROM terms
                           WHERE uid = %s
                           """, id)
            # FIXME: should we bother here? probably, just to be thorough,
            # although ui should reload source_catalog after any change.
            del(self.terms[id])


    def get_term_from_token (self, token):
        if self.term_tokens.has_key(token):
            term_uid = self.term_tokens[token]
            return self.terms[term_uid]
        else:
            return None



class Term (CatalogItem):

    def __init__ (self, uid=-1, name='', description='', date_modified=''):
        CatalogItem.__init__(self,
                             uid=uid,
                             name=name,
                             description=description,
                             date_modified=date_modified)
        self.token = ''
        self.vocabulary_uid = -1
        self.source_uid = -1
        self.is_multivalue = False
        self.re_multivalue_sep = ''
        self.mapped_term_uid = -1

    def load (self, cursor):
        if self.uid == -1:
            return

        cursor.execute("""
                       SELECT *
                       FROM terms
                       WHERE uid = %s
                       """, self.uid)
        rows = cursor.fetchall()
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        if rows and len(rows) > 0:
            row = dtuple.DatabaseTuple(desc, rows[0])
            for field in fields:
                self.set(field, row[field])


    def save (self, cursor):
        if self.uid == -1:
            cursor.execute("""
                           INSERT INTO terms
                           (uid, name, description, date_modified,
                           token, vocabulary_uid, source_uid, is_multivalue,
                           re_multivalue_sep, mapped_term_uid)
                           VALUES
                           (NULL, %s, %s, CURDATE(),
                           %s, %s, %s, %s,
                           %s, %s)
                           """, (self.name, self.description,
                                 self.token, self.vocabulary_uid, self.source_uid, self.is_multivalue,
                                 self.re_multivalue_sep, self.mapped_term_uid))
        else:
            cursor.execute("""
                           UPDATE terms
                           SET name=%s, description=%s, date_modified=CURDATE(),
                            token=%s, vocabulary_uid=%s, source_uid=%s,
                            is_multivalue=%s,
                            re_multivalue_sep=%s, mapped_term_uid=%s
                           WHERE uid=%s
                           """, (self.name, self.description,
                                 self.token, self.vocabulary_uid, self.source_uid,
                                 self.is_multivalue,
                                 self.re_multivalue_sep, self.mapped_term_uid,
                                 self.uid))
        self.date_modified = time.strftime(str('%Y-%m-%d'))

