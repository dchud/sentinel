import dtuple
import types

from canary.utils import DTable


class Concept (DTable):
    # FIXME: Resolve conflict between Exp/Out/Spec as "concepts" and this
    # 'Concept'; namely that Concept.uid == Exp/Out/Spec.concept_id.
    # Can wait until refactoring.
    
    def __init__ (self, uid=-1):
        self.uid = uid
        self.study_id = -1
        self.concept_source_id = -1
        self.concept_source_code = ''
        self.term = ''
        self.sources = []
        self.synonyms = []
        
    
    def load (self, cursor, load_synonyms=False):
        if self.uid == -1:
            return
        
        print 'select'
        cursor.execute("""
            SELECT umls_concepts.preferred_name, 
                umls_concepts_sources.umls_source_id, 
                umls_concepts_sources.umls_source_code
            FROM umls_concepts, umls_concepts_sources
            WHERE umls_concepts_sources.umls_concept_id = umls_concepts.umls_concept_id
            AND umls_concepts.umls_concept_id = %s
            """, self.uid)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        
        print 'fetch'
        rows = cursor.fetchall()
        for row in rows:
            row = dtuple.DatabaseTuple(desc, row)
            self.term = row['preferred_name']
            self.sources.append((row['umls_source_id'], row['umls_source_code']))
            self.concept_source_id = row['umls_source_id']
            self.concept_source_code = row['umls_source_code']
            
        print 'synonyms'
        if load_synonyms:
            # NOTE: Is there any value in using umls_term_id?  It's ignored here.
            cursor.execute("""
                SELECT term
                FROM umls_terms
                WHERE umls_concept_id = %s
                """, self.uid)
            fields = [d[0] for d in cursor.description]
            desc = dtuple.TupleDescriptor([[f] for f in fields])
            rows = cursor.fetchall()
            for row in rows:
                row = dtuple.DatabaseTuple(desc, row)
                synonym = row['term']
                if not synonym in self.synonyms:
                    self.synonyms.append(synonym)
                    
    
    def save (self, cursor, update_all=False):
        # NOTE: For now, do not allow creation of arbitrary concepts
        if self.uid == -1:
            return
        
        # NOTE: For now, only allow update of preferred_name
        cursor.execute("""
            UPDATE umls_concepts
            SET preferred_name = %s
            WHERE umls_concept_id = %s
            """, (self.term, self.uid))
            
    
    def add_synonym (self, cursor, term):
        
        # If a synonym does not yet exist, add it here, starting at id 20,000,000
        # (5,000,000+ and 10,000,000+ are already in use from ITIS faux-merge)
        
        if not term in self.synonyms:
            cursor.execute("""
                SELECT MAX(umls_term_id) AS max_id
                FROM umls_terms
                """)
            row = cursor.fetchone()
            current_max = row[0]
            if current_max < 20000000:
                new_max = 20000001
            else:
                new_max = current_max + 1
                
            cursor.execute("""
                INSERT INTO umls_terms
                (umls_term_id, term, umls_concept_id)
                VALUES (%s, %s, %s)
                """, (new_max, term, self.uid))
            
            

def find_concepts (cursor, search_term):
    
    concepts = {}
    
    if isinstance(search_term, types.IntType):
        cursor.execute("""
            SELECT umls_terms.umls_concept_id, term, preferred_name, umls_source_id 
            FROM umls_terms, umls_concepts, umls_concepts_sources 
            WHERE umls_concepts.umls_concept_id = %s
            AND umls_concepts.umls_concept_id = umls_terms.umls_concept_id 
            AND umls_concepts_sources.umls_concept_id = umls_concepts.umls_concept_id
            GROUP BY umls_concepts.umls_concept_id
            ORDER BY term, preferred_name
            """, search_term)
            
    else:
        # Assumes search_term is text
        if search_term \
            and len(search_term) > 0:
            query_term = search_term.strip().replace(' ', '% ') + '%'
            cursor.execute("""
                SELECT umls_terms.umls_concept_id, term, preferred_name, umls_source_id 
                FROM umls_terms, umls_concepts, umls_concepts_sources 
                WHERE term LIKE %s
                AND umls_concepts.umls_concept_id = umls_terms.umls_concept_id 
                AND umls_concepts_sources.umls_concept_id = umls_concepts.umls_concept_id
                GROUP BY umls_concepts.umls_concept_id
                ORDER BY term, preferred_name
                """, query_term)
    
    fields = [d[0] for d in cursor.description]
    desc = dtuple.TupleDescriptor([[f] for f in fields])
    rows = cursor.fetchall()
    for row in rows:
        row = dtuple.DatabaseTuple(desc, row)
        if not concepts.has_key((row['umls_concept_id'], row['umls_source_id'])):
            concept = Concept(uid=row['umls_concept_id'])
            concept.concept_source_id = row['umls_source_id']
            concept.term = row['preferred_name']
            concept.synonyms.append(row['term'])
            concepts[(concept.uid, concept.concept_source_id)] = concept
        else:
            concept = concepts[(row['umls_concept_id'], row['umls_source_id'])]
            if not row['term'] in concept.synonyms:
                concept.synonyms.append(row['term'])
            concepts[(concept.uid, concept.concept_source_id)] = concept
        
    if not isinstance(search_term, types.IntType):
        # Try to bump up coarse "relevance" of exact matches
        concepts_ranked = concepts.values()
        for concept in concepts_ranked:
            if concept.term.lower() == search_term.lower()\
                or search_term.lower() in [syn.lower() for syn in concept.synonyms]:
                concepts_ranked.remove(concept)
                concepts_ranked.insert(0, concept)
        return concepts_ranked
    
    return concepts.values()
