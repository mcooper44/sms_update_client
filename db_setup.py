from db_model import Database
from datetime import datetime
from db_model import database_manager

             

r_now = str(datetime.now())

sms_table = [('555-555-5555', 'hello', r_now),
             ('555-555-5555', 'is it me you are looking for', r_now)] 
test_sms = {'sms_message':(sms_table, '(?,?,?)')}


target_number = '+15195555555' # change this string to an actual number 


# file ID, app #
gift_table = [(123456, 25, 0), 
              (321654, 26, 0), 
              (654987, 100, 0), 
              (7894500, 120, 0), 
              (369852, 300, 0)]

route_table = [(321654, 99, 0), 
              (654987, 100, 0), 
              (789456, 120, 0), 
              (369852, 200, 0),
              (146374, 5, 0)]

person_table =  [(123456,'John', 'Doe',f'{target_number}'), 
              (321654, 'Jane', 'Doe',  f'{target_number}'), 
              (654987, 'John', 'Smith', f'{target_number}'), 
              (789456, 'Adam', 'Smith',f'{target_number}'), 
              (369852, 'Ada', 'Twist', f'{target_number}'),
              (7894500, 'Iggy', 'Peck', f'{target_number}'),
              (146374, 'Rosie', 'Revere', f'{target_number}')]

test_values = {'gift_table': (gift_table,'(?,?,?)'),
               'route_table': (route_table,'(?,?,?)'),
               'person_table': (person_table,'(?,?,?,?)')}

gift_write = '''CREATE TABLE IF NOT EXISTS gift_table (file_id INT PRIMARY KEY, app_num
                INT, message_sent INT)'''

route_write = '''CREATE TABLE IF NOT EXISTS route_table (file_id INT PRIMARY KEY, 
                route_num INT, message_sent INT)'''

person_write = '''CREATE TABLE IF NOT EXISTS person_table (file_id INT PRIMARY KEY, 
                 f_name TEXT, l_name TEXT, phone_num TEXT)'''

sms_write = '''CREATE TABLE IF NOT EXISTS sms_message (sms_from TEXT, sms_body TEXT, sms_when DATE)'''

setup_strings = [gift_write, route_write, person_write]






def write_sms_db():
    '''
    instantiates a sms database
    '''
    sms_db = Database('sms_response.db')
    sms_db.connect(first_time=True, strings=[sms_write])
    sms_db.insert(test_sms)
    sms_db.close()

def write_to_db(package):
    '''
    opens a connection to the sms database 
    and writes a test value to it
    '''
    dbc = database_manager({'sms': 'sms_response.db'})
    dbc.initialize_connections()
    name, structure = package
    dbc.insert_to(name, structure)
    dbc.close_all()

def log_sms():
    '''
    test insert of a message to the sms database
    '''
    message = 'hello mr.'
    from_number = '519-555-5555'
    now = r_now
    sms_response = ('sms', 
                    {'sms_message':
                     ([(from_number, message, now)],
                      '(?,?,?)')
                    }
                   )
    write_to_db(sms_response)


if __name__ == '__main__':

    # connect to and initialize a test client database
    test_db = Database('sms_client_test.db')
    test_db.connect(first_time=True, strings=setup_strings)
    test_db.insert(test_values)
    test_db.close()

    # setup a sms database
    write_sms_db()
