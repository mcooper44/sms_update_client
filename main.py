#!/usr/bin/python3.6

'''
classes and methods for loading twilio configuration and credentials 
and processing client data.
calling this file will send sms messages to clients according to the
parameters supplied on the command line

'''
import yaml
from twilio.rest import Client

from db_model import Database
 

class configuration:
    def __init__(self, config_file):
        self.config = config_file 
        # production creds
        self.secret = None
        self.auth = None
        # testing creds
        self.test_secret = None 
        self.test_auth = None
        self.test_number = None # twilio supplied testing number
        self.live_test_number = None # an actual number to test with
        # number that twilio will sms from
        self.phone_number = None # phone number purchased from twilio
        
        if self.config:
            try:
                print(f'trying to open {self.config}')
                f = self.config
                with open(f, 'r') as ymlfile:
                    yfile = yaml.load(ymlfile)
                    self.secret = yfile['sid']
                    self.auth = yfile['token']
                    self.test_secret = yfile['test_sid']
                    self.test_auth = yfile['test_token']
                    self.phone_number = yfile['phone_number']
                    self.test_number = yfile['test_number']
                    self.live_test_number = yfile['test_target']

            except:
                print('failed to open config file')

    def return_creds(self, cred_type='test'):
        '''
        returns secret, auth attributes, from_phone number
        cred_type flag == test to return test creds
        otherwise returns the actual credentials
        '''
        if cred_type == 'test':
            return self.test_secret, self.test_auth, self.phone_number
        else:
            return self.secret, self.auth, self.phone_number

    def print_creds(self):
        print(f'secret {self.secret} auth {self.auth} phone {self.phone_number}')
        print(f'test secret {self.test_secret} test_auth {self.test_auth}')

class twilio_client:
    '''
    controls the twilio client and provides a method to send sms messages
    to recipients
    '''
    def __init__(self, sid, token, from_number):
        self.sid = sid
        self.token = token
        self.client = None
        self.from_number = from_number

        if all((self.sid, self.token)):
            try:
                self.client = Client(self.sid, self.token)
            except:
                print('failed to initialize twilio client')
                print(f'sid={self.sid} token={self.token}')

    def send_sms(self, to_num, sms_string, from_num=None, l_echo=True):
        '''
        sends a text message from the from_num to the to_num
        sms_string
        '''
        
        message = self.client.messages.create(to=to_num,
                                              from_=from_num,
                                              body=sms_string)
        if l_echo: print(f'to:{to_num} from:{from_num} body:{sms_string}')

class database_manager:
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

        '''
        self.db_struct[db_name].insert(d_struct)

    def return_app_num(self, database, file_id):
        ls = 'SELECT app_num FROM gift_table WHERE file_id=?'
        return self.db_struct[database].lookup_string(ls, file_id)

    def return_route_num(self, database, file_id):
        ls = 'SELECT route_num FROM route_table WHERE file_id=?'
        return self.db_struct[database].lookup_string(ls, (file_id,))

    def return_file_ids(self, database):
        '''
        returns tuples of (file_id, f_name, l_name, phone_num)
        from the person_table of the client_database
        
        '''
        ls = 'SELECT file_id, f_name, l_name FROM person_table'
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
        
def ld_client(echo=False):
    '''
    load the configuration file and twilio client
    and return them in that order
    '''
    # this is a basic test of the functionality
    c_f = configuration('setup.yml')
    if echo: c_f.print_creds()
    sid, token, f_num  = c_f.return_creds(cred_type='production')
    client = twilio_client(sid, token, f_num)
    print('good to go')
    return cf, client

def test_twilio():
    cf, client = ld_client()
    to_phone = c_f.live_test_number
    from_phone = c_f.phone_number
    if client: client.send_sms(to_phone, 'hello from the Internet',from_phone)

def test_database():
    
    try:
        dbm = database_manager({'client_db': 'sms_client_test.db', 
                                'sa': 'sa_2019_appointments.db'})
        dbm.initialize_connections() # instantiate db objects
    
        hh = dbm.return_file_ids('client_db')
        app_nums = [12, 55, 100, 250]
        app_dates = []
        print('testing client database')
        for x in hh:
            print(x)
        print('testing appointment database')
        for n in app_nums:
                
            info = dbm.return_app_date('sa', n)
            app_dates.append(info)
        for x,y in zip(app_nums, app_dates):
            print(f'{x}: {y}')
        dbm.close_all()
        print('databases closed')
    except Exception as e:
        print(f'what! it didnt work because of {e}')

if __name__ == '__main__':
   #test_twilio() 
   test_database()
