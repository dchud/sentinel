# $Id$

import logging

import dtuple


class ValueGroup:
    """
    A single group of discrete values from the EAV model.
    """

    def __init__ (self, group_name, description, value_group_id=-1,
        allow_multiple=0):
        self.value_group_id = value_group_id
        self.group_name = group_name
        self.description = description
        self.allow_multiple = allow_multiple
        self.values = {}

    def __repr__ (self):
        s = []
        s.append("<ValueGroup ")
        s.append("\tvalue_group_id=%d" % self.value_group_id)
        s.append("\tgroup_name=%s" % self.group_name)
        s.append("\tdescription=%s" % self.description)
        s.append("\allow_multiple=%s" % self.allow_multiple)
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
        
    def delete_value (self, context, value):
        if self.has_value(value.value_id):
            del(self.values[value.serial_number])
            value.delete(context)
            
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
        
    def is_multiple (self):
        return self.allow_multiple

    def save (self, context, update_values=True):
        cursor = context.get_cursor()
        try:
            if self.value_group_id == -1:
                cursor.execute("""
                    INSERT INTO dv_group
                    (dv_group_id, group_name, description, allow_multiple)
                    VALUES (NULL, %s, %s, %s)
                    """, (self.group_name, self.description, int(self.allow_multiple)))
            else:
                cursor.execute("""
                    UPDATE dv_group
                    SET group_name = %s,
                    description = %s,
                    allow_multiple = %s,
                    WHERE dv_group_id = %s
                    """, (self.group_name, self.description, self.value_group_id, int(self.allow_multiple)))
            
            if update_values:
                cursor.execute("""
                    DELETE FROM dv_values
                    WHERE dv_group_id = %s
                    """, self.value_group_id)
                for value_id in self.values:
                    value = self.values[value_id]
                    value.save(context)
                    
        except:
            # FIXME: log something here.  how to handle?  define Error.
            pass
            
        context.close_cursor(cursor)
        

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
        self.logger = logging.getLogger(str(self.__class__))

    def __repr__ (self):
        s = []
        s.append("<Value ")
        s.append("\tvalue_id=%d" % self.value_id)
        s.append("\tvalue_group_id=%d" % self.value_group_id)
        s.append("\tserial_number=%d" % self.serial_number)
        s.append("\tdescription=%s" % self.description)
        s.append(" />")
        return "\n".join(s)

    def save (self, context):
        cursor = context.get_cursor()
        try:
            if self.value_id == -1:
                cursor.execute("""
                    INSERT INTO dv_values
                    (dv_id, dv_group_id, serial_number, description)
                    VALUES (NULL, %s, %s, %s)
                    """, (self.value_group_id, self.serial_number, self.description))
            else:
                cursor.execute("""
                    UPDATE dv_values
                    SET dv_group_id = %s, serial_number = %s, description = %s
                    WHERE dv_id = %s
                    """, (self.value_group_id, self.serial_number, self.description,
                        self.value_id))
        except:
            # FIXME: define Errors.
            pass
        context.close_cursor(cursor)
        
            
    def delete (self, context):
        cursor = context.get_cursor()
        try:
            cursor.execute("""
                DELETE FROM dv_values
                WHERE dv_id = %s
                """, self.value_id)
        except:
            # FIXME: define Errors
            pass
        context.close_cursor(cursor)


class DBModel:
    """
    Provides access and maintenance functions for EAV-style discrete value
    groups, of which there is only a simple two-table setup in the sentinel
    db as of early July 2003.
    """

    def __init__ (self):
        self.value_groups = {}

    def load (self, context, debug=0):
        cursor = context.get_cursor()
        
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
                group.add_value(value)

            self.add_group(group)
        context.close_cursor(cursor)
        

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
        
        
    def delete_group (self, context, group_id):
        cursor = context.get_cursor
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

        context.close_cursor(cursor)
        
        
    def get_value_description (self, group_id, serial_number):
        try:
            group = self.value_groups[group_id]
            value = group.values[serial_number]
            return value.description
        except:
            return ''


    def model_size (self):
        return len(self.value_groups)
