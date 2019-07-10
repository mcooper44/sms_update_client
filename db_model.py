import sqlite3

target_number = '+15195555555' # change this string to an actual number 


# file ID, app #
gift_table = [(123456,25), 
              (321654, 26), 
              (654987, 100), 
              (789456, 101), 
              (369852, 450)]

route_table = [(123456,99), 
              (321654, 99), 
              (654987, 100), 
              (789456, 100), 
              (369852, 200)]

person_table =  [(123456,'John', 'Doe',f'{target_number}'), 
              (321654, 'Jane', 'Doe',  f'{target_number}'), 
              (654987, 'John', 'Smith', f'{target_number}'), 
              (789456, 'Adam', 'Smith',f'{target_number}'), 
              (369852, 'Ada', 'Twist', f'{target_number}')]

test_values = {'gift_table': (gift_table,'(?,?)'),
               'route_table': (route_table,'(?,?)'),
               'person_table': (person_table,'(?,?,?,?)')}

gift_write = '''CREATE TABLE IF NOT EXISTS gift_table (file_id INT PRIMARY KEY, app_num
                INT)'''

route_write = '''CREATE TABLE IF NOT EXISTS route_table (file_id INT PRIMARY KEY, 
                route_num INT)'''

person_write = '''CREATE TABLE IF NOT EXISTS person_table (file_id INT PRIMARY KEY, 
                 f_name TEXT, l_name TEXT, phone_num TEXT)'''

setup_strings = [gift_write, route_write, person_write]

class Database():
    '''
    for interacting with databases
    path_name is the location and name of the databse to connect with
    or create

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

        except:
            print('could not establish connection to database')



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

    def lookup_string(self, string, tple):
        '''
        executes sql sring with values tple
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

if __name__ == '__main__':
    test_db = Database('sms_client_test.db')
    test_db.connect(first_time=True, strings=setup_strings)
    test_db.insert(test_values)
    test_db.close()