# $Id$

import dtuple

from canary.utils import DTable



class Feature (DTable):

    def __init__ (self, uid=-1):
        self.uid = uid
        self.data_source = ''
        self.latitude = 0.0
        self.longitude = 0.0
        self.dms_latitude = 0
        self.dms_longitude = 0
        self.feature_type = ''
        self.country_code = ''
        self.adm1 = 0
        self.adm2 = ''
        self.name = ''
        
    def load (self, cursor):
        cursor.execute("""
            SELECT *
            FROM gazeteer
            WHERE uid = %s
            """, self.uid)
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        row = cursor.fetchone()
        if row:
            row = dtuple.DatabaseTuple(desc, row)
            for field in fields:
                self.set(field, row[field])
    


class Gazeteer:
    """
    Represents the gazeteer in general, including simple lookup values.
    """
    
    def __init__ (self):
        self.country_codes = {}
        self.feature_codes = {}
        self.fips_codes = {}
        
    def load (self, cursor):
        
        cursor.execute("""
            SELECT code, name
            FROM gazeteer_countries
            """)
        rows = cursor.fetchall()
        for row in rows:
            self.country_codes[row[0]] = row[1]
            
        cursor.execute("""
            SELECT designation, name
            FROM gazeteer_features
            """)
        rows = cursor.fetchall()
        for row in rows:
            self.feature_codes[row[0]] = row[1]
                
        cursor.execute("""
            SELECT country_code, fips_code, name
            FROM gazeteer_fips_codes
            """)
        rows = cursor.fetchall()
        for row in rows:
            self.fips_codes[(row[0], row[1])] = row[2]
            
            
    def search (self, cursor, feature_name, params={}):
        
        results = []
        search_token = feature_name.strip() + '%'
        
        cursor.execute("""
            SELECT * 
            FROM gazeteer
            WHERE MATCH (name) AGAINST (%s)
            LIMIT 100
            """, feature_name)
        
        while 1:
            row = cursor.fetchone()
            if row == None: break
            feature = Feature()
            fields = [d[0] for d in cursor.description]
            desc = dtuple.TupleDescriptor([[f] for f in fields])
            row = dtuple.DatabaseTuple(desc, row)
            for field in fields:
                feature.set(field, row[field])
            results.append(feature)
        
        # Try to bump up coarse "relevance" of exact matches
        results_ranked = results
        for result in results_ranked:
            if result.name.lower() == feature_name.lower():
                results_ranked.remove(result)
                results_ranked.insert(0, result)
        
        return results_ranked
