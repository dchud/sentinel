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
        
        rows = cursor.fetchall()
        for row in rows:
            row = dtuple.DatabaseTuple(desc, row)
            self.term = row['preferred_name']
            self.sources.append((row['umls_source_id'], row['umls_source_code']))
            self.concept_source_id = row['umls_source_id']
            self.concept_source_code = row['umls_source_code']
            
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




class Category (DTable):
    
    concept_types = [
        'exposure', 
        'outcome', 
        'species', 
        'location',
        ]
        
    def __init__ (self, uid=-1, name=''):
        self.uid = uid
        self.name = name
        self.types = []
        self.groups = []
        self.concepts = []
        
    def add_type (self, type):
        if type in self.concept_types \
            and not type in self.types:
            self.types.append(type)
            
    def clear_types (self):
        self.types = []
    
    def set_types (self, types):
        self.clear_types()
        if types.__class__ == ''.__class__:
            type_dict = dict(zip([t[0:1] for t in self.concept_types],
                self.concept_types))
            for type in types:
                concept_type = type_dict.get(type, None)
                if concept_type:
                    self.add_type(concept_type)
                    
        elif types.__class__ == [].__class__:
            for type in types:
                if type in self.concept_types:
                    self.add_type(type)
        
    def get_types (self, shorthand=False):
        if shorthand:
            sh = ''.join([type[0:1] for type in self.types])
            return sh
        else:
            return self.types

    def add_group (self, group):
        if group.__class__ == ''.__class__:
            group = CategoryGroup(name=group, category_id=self.uid)
            
        if not group.name in [g.name for g in self.groups]:
            self.groups.append(group)
            
    def clear_groups (self):
        self.groups = []
        
    def set_groups (self, groups):
        self.clear_groups()
        for group in groups:
            self.add_group(group)
        
    def get_groups (self):
        return self.groups

    def add_concept (self, concept):
        if not concept.concept_id in [c.concept_id for c in self.concepts] \
            and not concept.uid in [c.uid for c in self.concepts]:
            self.concepts.append(concept)
            
    def remove_concept (self, cursor, concept):
        print 'Category.remove_concept()'
        for c in self.concepts:
            if concept.uid == c.uid:
                self.concepts.remove(c)
        print '...executing DELETE on uid = %s' % concept.uid
        try:
            cursor.execute("""
                DELETE FROM category_concepts
                WHERE uid = %s
                """, concept.uid)
        except:
            import traceback
            print traceback.print_exc()

    def update_concept (self, concept):
        self.remove(concept)
        self.add_concept(concept)
    
    def get_concepts (self):
        return self.concepts

    def load (self, cursor, load_concepts=False):
        if self.uid == -1:
            return

        cursor.execute("""
            SELECT * 
            FROM categories
            WHERE uid = %s
            """, self.uid)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        row = cursor.fetchone()
        row = dtuple.DatabaseTuple(desc, row)
        self.name = row['name']
        self.set_types(row['concept_types'])
        
        cursor.execute("""
            SELECT * 
            FROM category_groups
            WHERE category_id = %s
            """, self.uid)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        for row in rows:
            row = dtuple.DatabaseTuple(desc, row)
            group = CategoryGroup(uid=row['uid'], category_id=self.uid, 
                name=row['name'])
            self.add_group(group)
        
        if load_concepts:
            cursor.execute("""
                SELECT *
                FROM category_concepts
                WHERE category_id = %s
                """, self.uid)
            fields = [d[0] for d in cursor.description]
            desc = dtuple.TupleDescriptor([[f] for f in fields])
            rows = cursor.fetchall()
            for row in rows:
                row = dtuple.DatabaseTuple(desc, row)
                cat_concept = CategoryConcept(uid=row['uid'], 
                    category_id=self.uid, 
                    concept_id=row['concept_id'])
                cat_concept.is_broad = row['is_broad']
                cat_concept.is_default = row['is_default']
                cat_concept.load(cursor)
                self.add_concept(cat_concept)
                
        
        
    def save (self, cursor):
        if self.uid == -1:
            cursor.execute("""
                INSERT INTO categories
                (uid, name, concept_types)
                VALUES
                (NULL, %s, %s)
                """, (self.name, self.get_types(shorthand=True)))
            cursor.execute("""
                SELECT LAST_INSERT_ID() AS new_uid
                """)
            row = cursor.fetchone()
            self.uid = row[0]
            
            for group in self.groups:
                group.category_id = self.uid
                group.save(cursor)
        
        else:
            cursor.execute("""
                UPDATE categories
                SET name = %s, concept_types = %s
                WHERE uid = %s
                """, (self.name, self.get_types(shorthand=True), self.uid))
                


def load_categories (cursor):
    categories = []
    cursor.execute("""
        SELECT uid
        FROM categories
        ORDER BY name
        """)
    rows = cursor.fetchall()
    for row in rows:
        category = Category(uid=row[0])
        category.load(cursor)
        categories.append(category)
    
    return categories


class CategoryGroup (DTable):
    
    def __init__ (self, uid=-1, category_id=-1, name=''):
        self.uid = uid
        self.category_id = category_id
        self.name = name
        
    def save (self, cursor):
        if self.uid == -1:
            cursor.execute("""
                INSERT INTO category_groups
                (uid, category_id, name)
                VALUES
                (NULL, %s, %s)
                """, (self.category_id, self.name))
        else:
            cursor.execute("""
                UPDATE category_groups
                SET name = %s
                WHERE uid = %s
                """, (self.name, self.uid))


class CategoryConcept (DTable):
    
    def __init__ (self, uid=-1, category_id=-1, concept_id=-1, term=''):
        self.uid = uid
        self.category_id = category_id
        self.concept_id = concept_id
        self.is_broad = False
        self.is_default = False
        self.term = term
        self.groups = []
        self.concept = None
        
    def load (self, cursor):
        if self.uid == -1:
            if not self.concept_id == -1 \
                and not self.category_id == -1:
                cursor.execute("""
                    SELECT * 
                    FROM category_concepts
                    WHERE category_id = %s
                    AND concept_id = %s
                    """, (self.category_id, self.concept_id))
                fields = [d[0] for d in cursor.description]
                desc = dtuple.TupleDescriptor([[f] for f in fields])
                row = cursor.fetchone()
                if row:
                    row = dtuple.DatabaseTuple(desc, row)
                    self.uid = row['uid']
                    self.is_broad = row['is_broad']
                    self.is_default = row['is_default']
                else:
                    print 'no matched rows'
                    return
            else:
                print 'not enough info'
                return
        else:
            cursor.execute("""
                SELECT * 
                FROM category_concepts
                WHERE uid = %s
                """, self.uid)
            fields = [d[0] for d in cursor.description]
            desc = dtuple.TupleDescriptor([[f] for f in fields])
            row = cursor.fetchone()
            if row:
                row = dtuple.DatabaseTuple(desc, row)
                self.concept_id = row['concept_id']
                self.is_broad = row['is_broad']
                self.is_default = row['is_default']
        
        cursor.execute("""
            SELECT * 
            FROM category_concept_groups
            WHERE category_concept_id = %s
            """, self.uid)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        for row in rows:
            row = dtuple.DatabaseTuple(desc, row)
            self.groups.append(row['category_group_id'])
        
        self.concept = Concept(uid=self.concept_id)
        self.concept.load(cursor)
        
    def save (self, cursor):
        if self.uid == -1:
            print 'execute'
            cursor.execute("""
                INSERT INTO category_concepts
                (uid, category_id, concept_id, 
                is_default, is_broad)
                VALUES
                (NULL, %s, %s, 
                %s, %s)
                """, (self.category_id, self.concept_id, 
                self.is_default, self.is_broad))
            print 'get last insert id'
            cursor.execute("""
                SELECT LAST_INSERT_ID() AS new_uid
                """)
            print 'executed both'
            row = cursor.fetchone()
            print 'setting uid'
            self.uid = row[0]
        else:
            print 'updating'
            cursor.execute("""
                UPDATE category_concepts
                SET is_default = %s,
                is_broad = %s
                WHERE uid = %s
                """, (self.is_default, self.is_broad, self.uid))
            print 'updated'
