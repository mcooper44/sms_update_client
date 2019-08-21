import sqlite3

target_number = '+15195555555' # change this string to an actual number 

class Database():
    '''
    for interacting with databases
    path_name is the location and name of the databse to connect with
    or create

    connect() method establishes a database and/or connection to one
    

    '''
    def __init__(self, path_name):
        self.path_name = path_name
        self.conn = None
        self.cur = None


    def connect(self, first_time=False, strings=None):
        '''
        establishes connection to database stored in the .path_name attribute
        if the first_time flag is set
        it will attempt to create tables with strings contained in a list or
        tuple held in the 'strings' parameter
        '''
        
        try:
            self.conn = sqlite3.connect(self.path_name)
            self.cur = self.conn.cursor()
            print(f'Database.connect: database connection open to {self.path_name}')

            if first_time == True and any(strings):
                for string in strings:
                    self.cur.execute(string)
                    print(f'executing: {string}')
                    self.conn.commit()
            elif first_time == True and not any(strings):
                print('no strings provided to provision tables')

        except Exception as e:
            print('could not establish connection to database')
            print(e)



    def insert(self, data_struct, echo=False):
        '''
        takes a dictionary 'data_struct' of 
        'table name': ([(values_to_write,)], # list of tuple(s)
                       '(?, [...])') # string tuple with a ? for each 
                                     # to insert

        and iterates through the data structure inserting values
        into the tables used as keys in dictionary
        '''
        for table_name in data_struct.keys():
            # lookup the values to insert i.e [(1,2,3),(4,5,6)]
            # and a tuple representing the number of columns
            # i.e. '(?, ?, ?)'
            lst_of_tples, flds = data_struct.get(table_name, (None,None))
            wr_str = f'INSERT OR IGNORE INTO {table_name} VALUES {flds}'
            if all((lst_of_tples,flds)):
                # iterate through val which should be a list of tuples
                for tple_to_insert in lst_of_tples:
                    if echo: print(f'writing {tple_to_insert} into {table_name}')
                    self.cur.execute(wr_str, tple_to_insert)
                    self.conn.commit()

    def lookup(self, target, table, row, paramater):
        '''
        SELECT {file_id} FROM {route_table} WHERE {route_num}{ BETWEEN 50 AND 130}
        SELECT {*} FROM {person_table} WHERE {file_id}{=123456}
        
        http://www.sqlitetutorial.net/sqlite-between/    
        '''
        ex_string = f'SELECT {target} FROM {table} WHERE {row}{parameter}'
        self.cur.execute(ex_string)
        rows = self.cur.fetchall()
        return rows

    def update(self, string, tple):
        '''
        executes sql string with values tple
        to update a table
        '''
        if all((string,tple)):
            try:
                self.cur.execute(string, tple)
                return True
            except Exception as error:
                return error
        else:
            print('input for SQL update operation is none')
            return False

    def lookup_string(self, string, tple):
        '''
        executes sql string with values tple
        if tple != None asuming it a fetchone scenario
        if tple = None, assuming it is a fetchall scenario
        '''
        rows = None
        if tple:
            try:
                self.cur.execute(string, tple) 
                rows = self.cur.fetchone()
            except:
                print(f'could not lookup {tple} with {string}')
        else:
            self.cur.execute(string)
            rows = self.cur.fetchall()
        
        if not rows: print('WARNING: NO DATABASE RESULT')

        return rows

    def close(self):
        '''
        closes the db connection

        '''
        name = self.path_name
        try:
            self.conn.close()
            print(f'connection to {name} closed')
        except:
            print('could not close connection')

class database_manager:
    '''
    Interface for the Database class
    contains methods for making specific calls to the database

    dbm = database_manager({'client_db': 'sms_client_test.db', 
                                'sa': 'sa_2019_appointments.db'})
    dbm.initialize_connections() # instantiate db objects

    '''


    def __init__(self, data_bases):
        self.db_path_dict = data_bases # dict of {db_name: path_string}
        self.db_struct = {}

    def initialize_connections(self):
        for db_name in self.db_path_dict.keys():
            path_string = self.db_path_dict.get(db_name, None)
            self.db_struct[db_name] = Database(path_string)
            self.db_struct[db_name].connect()

    def close_all(self):
        '''
        iterates through the databases being managed and closes them
        '''
        for db_name in self.db_struct.keys():
            self.db_struct[db_name].close()

    def insert_to(self, db_name, d_struct):
        '''
        insert data structre d_struct to database db_name
        param d_struct is a dictionary as per doc string described
        on insert method of the database class

        'table name': ([(values_to_write,)], # list of tuple(s)
                       '(?, [...])') # string tuple with a ? for each 
                                     # value to insert

        '''
        self.db_struct[db_name].insert(d_struct)

    def return_app_num(self, database, file_id):
        ls = 'SELECT app_num FROM gift_table WHERE file_id=?'
        return self.db_struct[database].lookup_string(ls, file_id)

    def return_app_range(self, database, low, high):
        '''
        return a range of gift appointments between the low and high values
        used to lookup file_id's that have upcoming gift appointments
        returns 2 tuples of file_id, app_num
        '''
        ls = f'''SELECT gift_table.file_id, app_num, phone_num
                 FROM gift_table 
                 INNER JOIN person_table ON gift_table.file_id =
                 person_table.file_id WHERE 
                 app_num <= {high} AND app_num >= {low} AND message_sent = 0
                 AND person_table.phone_num IS NOT NULL'''
        return self.db_struct[database].lookup_string(ls, None)
    
    def return_route_range(self, database, low, high):
        '''
        return a range of file_id's that have route numbers between parameter
        low and high - used to find households that have an upcoming delivery
        returns 2 tuples of file_id, route_num
        '''
        ls = f'''SELECT route_table.file_id, route_num, phone_num FROM 
                 route_table 
                 INNER JOIN person_table
                 ON person_table.file_id = route_table.file_id
                 WHERE route_table.route_num >= {low} AND 
                 route_num <= {high} AND route_table.message_sent = 0
                 AND person_table.phone_num IS NOT NULL'''
        return self.db_struct[database].lookup_string(ls, None)

    def return_route_num(self, database, file_id):
        ls = 'SELECT route_num FROM route_table WHERE file_id=?'
        return self.db_struct[database].lookup_string(ls, (file_id,))

    def return_file_ids(self, database):
        '''
        returns tuples of (file_id, cell_num)
        from the person_table of the client_database
        for all the Households that have a valid NOT NULL cell_num value
        typical usage would be dbm.return_file_ids('client_database.db')
        or in testing scenarios .return_file_ids('sms_client_test.db')

        '''
        ls = '''SELECT file_id, cell_num FROM person_table 
                WHERE cell_num IS NOT NULL'''
        return self.db_struct[database].lookup_string(ls, None)
    
    def return_app_date(self, database, app_num, echo=False):
        '''
        returns the day and time as a tuple from the database when
        supplied a app_num
        '''
        ls = 'SELECT day, time from Appointments where ID=?'
        day_time =  self.db_struct[database].lookup_string(ls, (app_num,))
        if echo: print(f'found {day_time}')
        return day_time

    def return_gift_sent(self, database, app_number):
        '''
        looks in database in the 'gift_table' to see if 'message_sent' where
        'app_num' = parameter app_number
        '''
        ls = 'SELECT message_sent FROM gift_table WHERE app_num=?'
        return self.db_struct[database].lookup_string(ls, (app_number,))

    def set_gift_sent(self, database, file_id):
        '''
        set the message_sent value in the gift_table at param file_id
        '''
        ls = 'UPDATE gift_table SET message_sent=1 WHERE file_id=?'
        try:
            self.db_struct[database].update(ls, (file_id,))
            return True
        except Exception as error:
            print(error)
            return False
        
    def set_route_sent(self, database, file_id):
        '''
        set the message_sent value in the route table at param file_id
        '''
        try:
            self.db_struct[database].update(ls, (file_id,))
            return True
        except Exception as error:
            print(error)
            return False

