import dtuple

class ValueGroup:
    """
    A single group of discrete values from the EAV model.
    """

    def __init__ (self,
                  value_group_id,
                  group_name,
                  description):
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

    def add_value (self,
                   value):
        if value.__class__.__name__ == 'Value':
            #self.values[value.value_id] = value
            self.values[value.serial_number] = value

    def group_size (self):
        return len(self.values)


class Value:
    """
    A single potential value, one of many within a single group,
    from the EAV model.
    """
    def __init__ (self,
                  value_id,
                  value_group_id,
                  serial_number,
                  description):
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



class DBModel:
    """
    Provides access and maintenance functions for EAV-style discrete value
    groups, of which there is only a simple two-table setup in the sentinel
    db as of early July 2003.
    """

    def __init__ (self):
        self.value_groups = {}

    def add_group (self, group):
        if not group.__class__.__name__ == "ValueGroup":
            return

        self.value_groups[group.value_group_id] = group

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
            group = ValueGroup(int(row['dv_group_id']),
                               row['group_name'],
                               row['description'])


            cursor.execute("""
                SELECT * FROM dv_values
                WHERE dv_group_id = %s
                """ % group.value_group_id)

            value_rows = cursor.fetchall()
            for value_row in value_rows:
                # FIXME: dtuplify
                value = Value(int(value_row[0]),
                              int(value_row[1]),
                              int(value_row[2]),
                              value_row[3])
                if debug:
                    print "adding value:"
                    print value
                group.add_value(value)

            if debug:
                print "adding group:"
                print group
            self.add_group(group)


    def get_group (self, group_id):
        if self.value_groups.has_key(group_id):
            return self.value_groups[group_id]

    def get_value_description (self, group_id, serial_number):
        try:
            group = self.value_groups[group_id]
            value = group.values[serial_number]
            return value.description
        except:
            return ''

    def model_size (self):
        return len(self.value_groups)



if __name__ == '__main__':
    import MySQLdb
    con = MySQLdb.connect(host='localhost',
                          user='dlc33',
                          passwd='floogy',
                          db='sentinel')
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
