import dtuple

class ValueGroup:
    """
    A single group of discrete values from the EAV model.
    """

    def __init__ (self,
                  group_name,
                  description,
                  value_group_id=-1):
        self.value_group_id = value_group_id
        self.group_name = group_name
        self.description = description
        self.values = {}

    def __repr__ (self):
        s = []
        s.append("<ValueGroup ")
        s.append("\tvalue_group_id=%d" % self.value_group_id)
        s.append("\tgroup_name=%s" % self.group_name)
        s.append("\tdescription=%s" % self.description)
        s.append("/>")
        return "\n".join(s)

    def add_value (self, value):
        if value.__class__.__name__ == 'Value':
            #self.values[value.value_id] = value
            self.values[value.serial_number] = value

    def has_value (self, value_id):
        for serial_number, value in self.values.items():
            if value.value_id == value_id:
                return True
        return False
        
    def delete_value (self, cursor, value):
        if self.has_value(value.value_id):
            del(self.values[value.serial_number])
            value.delete(cursor)
            
    def get_value (self, value_id):
        for serial_number, value in self.values.items():
            if value.value_id == value_id:
                return value
        
    def get_values (self):
        values = [(value.serial_number, value) for id, value in self.values.items()]
        values.sort()
        return values
        
    def group_size (self):
        return len(self.values)

    def save (self, cursor, update_values=True):
        try:
            if self.value_group_id == -1:
                cursor.execute("""
                    INSERT INTO dv_group
                    (dv_group_id, group_name, description)
                    VALUES (NULL, %s, %s)
                    """, (self.group_name, self.description))
            else:
                cursor.execute("""
                    UPDATE dv_group
                    SET group_name = %s,
                    description = %s
                    WHERE dv_group_id = %s
                    """, (self.group_name, self.description, self.value_group_id))
            
            if update_values:
                cursor.execute("""
                    DELETE FROM dv_values
                    WHERE dv_group_id = %s
                    """, self.value_group_id)
                for value_id in self.values:
                    value = self.values[value_id]
                    value.save(cursor)
                    
        except:
            # FIXME: log something here.  how to handle?  define Error.
            pass
            

class Value:
    """
    A single potential value, one of many within a single group,
    from the EAV model.
    """
    def __init__ (self,
                  value_group_id,
                  serial_number,
                  description,
                  value_id=-1):
        self.value_id = value_id
        self.value_group_id = value_group_id
        self.serial_number = serial_number
        self.description = description

    def __repr__ (self):
        s = []
        s.append("<Value ")
        s.append("\tvalue_id=%d" % self.value_id)
        s.append("\tvalue_group_id=%d" % self.value_group_id)
        s.append("\tserial_number=%d" % self.serial_number)
        s.append("\tdescription=%s" % self.description)
        s.append(" />")
        return "\n".join(s)

    def save (self, cursor):
        try:
            if self.value_id == -1:
                print 'inserting value'
                cursor.execute("""
                    INSERT INTO dv_values
                    (dv_id, dv_group_id, serial_number, description)
                    VALUES (NULL, %s, %s, %s)
                    """, (self.value_group_id, self.serial_number, self.description))
            else:
                print 'updating value'
                cursor.execute("""
                    UPDATE dv_values
                    SET dv_group_id = %s, serial_number = %s, description = %s
                    WHERE dv_id = %s
                    """, (self.value_group_id, self.serial_number, self.description,
                        self.value_id))
        except:
            # FIXME: define Errors.
            pass
            
    def delete (self, cursor):
        try:
            cursor.execute("""
                DELETE FROM dv_values
                WHERE dv_id = %s
                """, self.value_id)
            print 'deleted value'
        except:
            # FIXME: define Errors
            print 'failed: deleting value'
            pass


class DBModel:
    """
    Provides access and maintenance functions for EAV-style discrete value
    groups, of which there is only a simple two-table setup in the sentinel
    db as of early July 2003.
    """

    def __init__ (self):
        self.value_groups = {}

    def load_from_db (self, cursor, debug=0):
        if cursor == None:
            return

        # load all value groups
        cursor.execute('SELECT * FROM dv_group')
        fields = [d[0] for d in cursor.description]
        desc = dtuple.TupleDescriptor([[f] for f in fields])
        rows = cursor.fetchall()
        for row in rows:
            if row == None: break

            # FIXME: dtuplify
            row = dtuple.DatabaseTuple(desc, row)
            group = ValueGroup(row['group_name'],
                row['description'],
                int(row['dv_group_id']))


            cursor.execute("""
                SELECT * FROM dv_values
                WHERE dv_group_id = %s
                """, group.value_group_id)
            val_fields = [d[0] for d in cursor.description]
            val_desc = dtuple.TupleDescriptor([[f] for f in val_fields])
            val_rows = cursor.fetchall()
            for val_row in val_rows:
                val_row = dtuple.DatabaseTuple(val_desc, val_row)
                value = Value(int(val_row['dv_group_id']),
                    int(val_row['serial_number']),
                    val_row['description'],
                    int(val_row['dv_id']))
                    
                if debug:
                    print "adding value:"
                    print value
                group.add_value(value)

            if debug:
                print "adding group:"
                print group
            self.add_group(group)


    def get_value (self, value_id):
        for group_id, group in self.value_groups.items():
            if group.has_value(value_id):
                return group.get_value(value_id)
            
    def add_group (self, group):
        if not group.__class__.__name__ == "ValueGroup":
            return
        self.value_groups[group.value_group_id] = group

    def get_group (self, group_id):
        if self.value_groups.has_key(group_id):
            return self.value_groups[group_id]
            
    def get_groups (self):
        group_ids = self.value_groups.keys()
        group_ids.sort()
        groups = []
        for id in group_ids:
            groups.append(self.value_groups[id])
        return groups
        
    def has_group (self, group_name):
        for group in self.get_groups():
            if group.group_name == group_name:
                return True
        return False
        
    def delete_group (self, cursor, group_id):
        print 'delete group', group_id
        try:
            group_id = int(group_id)
            
            # FIXME:  add existing value error checking
            cursor.execute("""
                DELETE FROM dv_values
                WHERE dv_group_id = %s
                """, group_id)
                
            cursor.execute("""
                DELETE FROM dv_group
                WHERE dv_group_id = %s
                """, group_id)
                
        except:
            # FIXME: errors.
            pass
       
    def get_value_description (self, group_id, serial_number):
        try:
            group = self.value_groups[group_id]
            value = group.values[serial_number]
            return value.description
        except:
            return ''

    def model_size (self):
        return len(self.value_groups)



# FIXME: a better test plan than embedding connection details here!
if __name__ == '__main__':
    import MySQLdb
    con = MySQLdb.connect(host='localhost',
                          user='dlc33',
                          passwd='floogy',
                          db='canary-dev')
    c = con.cursor()
    print 'connected, loading:'
    dbmodel = DBModel()
    dbmodel.load_from_db(c, debug=0)
    c.close()
    con.close()
    print 'done.'
    for group_id in dbmodel.value_groups.keys():
        group = dbmodel.get_group(group_id)
        print group
        for value_id in group.values.keys():
            value = group.values[value_id]
            print value

    group = dbmodel.get_group(14)
    for id in group.values.keys():
        value = group.values[id]
        print value.serial_number, value.description

    print dbmodel.get_value_description(3, 0)
    print dbmodel.get_value_description(4, 2)
    print dbmodel.get_value_description(12, 1)
