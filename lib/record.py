# $Id$

import dtuple
import re


_q_exports = []

class SubjectHeading:

    def __repr__ (self):
        return """<SubjectHeading term=%s, is_focus=%s, qualifier=%s>""" % (self.term,
            self.is_focus, self.qualifier)

    def __init__ (self, text=''):
        if not text == '':
            self.parse_text(text)
        else:
            self.text = text
            self.term = ''
            self.qualifier = ''
            self.is_focus = False


    def parse_text (self, text):
        """
        Parse an incoming MeSH string in one of the forms:

        'Growth Substances'
        'Growth Substances*'
        'Growth Substances/genetics'
        'Growth Substances/genetics*'
        'Growth Substances/*genetics'
        'Growth Substances/ge [Genetics]'  (From Ovid Medline)
        
        ...into its component parts.
        """

        text = text.strip()
        self.text = text

        # '*' indicates it's a focus heading[/qualifier]
        if '*' in text:
            self.is_focus = 1
            text = text.replace('*', '')
        else:
            self.is_focus = 0

        # '/' indicates there's an qualifier attached to the term
        slash_index = text.find('/')
        if slash_index > 0:
            self.term = text[0:slash_index]
            self.qualifier = text[(slash_index + 1):]
            if self.qualifier[-1] == ']':
                self.qualifier = self.qualifier[(self.qualifier.index('[') + 1) :
                    (self.qualifier.index(']'))].lower()
        else:
            self.term = text
            self.qualifier = ''



class Record:

    def __init__ (self):
        self.data = {}
        self.mesh = []
        self.outcomes = []
        self.methodologies = []
        self.exposures = []
        self.species = []

    def set (self, field, value):
        if value == None:
            setattr(self, str(field), str(''))
        else:
            setattr(self, str(field), str(value))
        #self.data[field] = value

    def get (self, field):
        return getattr(self, str(field))
        #if self.data.has_key(field):
        #    return self.data[field]
        #else:
        #    return ''

    def get_boolean (self, field):
        value = getattr(self, str(field))
        if value == '0':
            return "No"
        else:
            return "Yes"

    def load_by_pmid (self, pubmed_id, cursor):
        cursor.execute("""
            SELECT *
            FROM sentinel_studies
            WHERE pubmed_id = %s
            """, pubmed_id)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        row = cursor.fetchone()
        if row:
            row = dtuple.DatabaseTuple(desc, row)
            for field in fields:
                self.set(field, row[field])

            cursor.execute("""
                SELECT mesh_heading
                FROM reference_mesh
                WHERE reference_id = %s
                """, self.reference_id)
            while 1:
                row = cursor.fetchone()
                if row == None:
                    break
                sh = SubjectHeading(row[0])
                self.mesh.append(sh)

            cursor.execute("""
                SELECT human_disease, nature_of_relevance
                FROM reference_disease
                WHERE reference_id = %s
                """, self.reference_id)
            while 1:
                row = cursor.fetchone()
                if row == None:
                    break
                self.outcomes.append((row[0], row[1]))

            cursor.execute("""
                SELECT methodology
                FROM reference_methodology
                WHERE reference_id = %s
                """, self.reference_id)
            while 1:
                row = cursor.fetchone()
                if row == None:
                    break
                self.methodologies.append(row[0])

            cursor.execute("""
                SELECT exposure_agent
                FROM reference_exposure
                WHERE reference_id = %s
                """, self.reference_id)
            while 1:
                row = cursor.fetchone()
                if row == None:
                    break
                self.exposures.append(row[0])

            cursor.execute("""
                SELECT species_name
                FROM reference_species
                WHERE reference_id = %s
                """, self.reference_id)
            while 1:
                row = cursor.fetchone()
                if row == None:
                    break
                self.species.append(row[0])

