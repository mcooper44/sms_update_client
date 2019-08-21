#!/usr/bin/python3.6

'''
classes and methods for loading twilio configuration and credentials 
and processing client data.
calling this file will send sms messages to clients according to the
parameters supplied on the command line

'''
import yaml
from twilio.rest import Client

import argparse
from datetime import datetime
from collections import namedtuple
from collections import defaultdict

from db_model import Database
from db_model import database_manager 

# used in the recipient class
recip_hh = namedtuple('recip_hh', 
                      'file_id, phone_num, gift_app, gift_date, route_num')

class configuration:
    '''
    Load the data in the configuration file into an object
    and make the data points in the file accessble via
    class attributes and methods

    '''

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
        self.delivery_target = None # average number of HH we can deliver to
        self.gift_dates = None # dict {4: [1,286], ...}
        self.delivery_dates = None # list [12, 13, ... 20]


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
                    self.delivery_target = yfile['daily_delivery_target']
                    self.gift_dates = yfile['gift_dates']
                    self.delivery_dates = yfile['delivery_dates']

            except:
                print('failed to open config file')

    def return_creds(self, cred_type='test'):
        '''
        for twilio:
        returns secret, auth attributes, from_phone number
        cred_type flag == test to return test creds
        otherwise returns the actual credentials
        '''
        if cred_type == 'test':
            return self.test_secret, self.test_auth, self.phone_number
        else:
            return self.secret, self.auth, self.phone_number

    def print_creds(self):
        '''
        for verification/testing print twilio creds

        '''
        print(f'secret {self.secret} auth {self.auth} phone {self.phone_number}')
        print(f'test secret {self.test_secret} test_auth {self.test_auth}')
    
    def return_gift_dates(self):
        '''
        returns the dictionary keyed with numbers for the day in Dec that SA
        is distributing gifts and containing the ranges of appointment numbers
        that occur on that date i.e. 4: [1, 286]
        '''
        return self.gift_dates 

    def return_delivery_data(self):
        '''
        returns a tuple of the daily delivery target (which is an approximation
        of how many we can do per day) and the delivery dates in a list
        (70, [12, 13, 14, 16 ...]
        '''
        return self.delivery_target, self.delivery_dates


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
        sends a text message sms_string from the from_num to the to_num
        
        '''
        
        message = self.client.messages.create(to=to_num,
                                              from_=from_num,
                                              body=sms_string)
        if l_echo: print(f'to:{to_num} from:{from_num} body:{sms_string}')

class recipient:
    '''
    recipient models a household and its gift appointment information
    and/or it's route number

    it contains the basic information and a __str__ method to expose
    this information in a formatted string ready to send via sms

    it is instantiated blank in a default dict by the contact_manger
    class and the set methods are used to add data via database
    lookups.

    '''
    def __init__(self, file_id=None, phone_num=None, gift_app=None,
                 gift_date=None, route_num=None):
        self.file_id = file_id
        self.phone_num = phone_num # cell phone number to send a sms message to
        self.gift_app = gift_app # appointment number
        self.gift_date = gift_date # string of date and time
        self.route_num = route_num # route number assigned to the Household
        self.status = False
        self.current_route = None

    def get_recipient_data(self):
        '''
        returns a named tuple of recipient attributes
        file_id, phone_num, gift_date, route_num
        if the object has not been properly initialized it will return False
        '''
        if self.status:
            return recip_hh(self.file_id, self.phone_num, self.gift_app, 
                                self.gift_date, self.route_num)
        else:
            return False
    
    def set_gift_data(self, app_num, app_date):
        '''
        sets the gift appointment number and time and date.
        it formats the app_date parameter for insertion
        into the final message string with an _at_ between the
        date and time
        '''
        self.gift_app = app_num
        adt_str = app_date.split(' ')
        fnl_str = f'{adt_str[0]} {adt_str[1]} at {adt_str[2]}'
        self.gift_date = fnl_str
    
    def set_route_data(self, route_num, cr):
        '''
        sets the route_num and current_route attributes
        current_route is the route number that is used
        to calculate the range of routes that can expect
        a delivery in the next 24 hour range.  route_num is
        the route number assigned to the recipient
        '''
        self.route_num = route_num
        self.current_route = cr

    def set_contact_data(self, fid, phone):
        '''
        updates the file_id and phone_num attributes
        if these attributes are not set, the sms message
        code will fail
        '''
        self.file_id = fid
        self.phone_num = phone

    def check_status(self):
        '''
        This method provides some introspection on the object
        if it has not been initialized with a fild id and phone
        number it will return False
        If it has that data but no route number or gift appointment
        some sort of error has occured and it will raise
        a ValueError
        '''
        if all((self.file_id, self.phone_num)):
            if any((self.route_num, self.gift_app)):
                self.status = True
                return self.status
            else:
                raise ValueError('invalid recipient initialized with no data')
        else:
            return False 

    def __str__(self):
        mess_head = '''Hello, this is an automated message from the Christmas \
Hamper Program. '''
        hdq_mess = f'''You are in hamper delivery route number {self.route_num} \
We are currently working on delivery \
route number {self.current_route}.'''
        gift_mess = f''' have a gift appointment on {self.gift_date} \
Please remember that you have gift appointment number \
{self.gift_app}.  It will be helpful to the volunteers \
at the Salvation Army to know this number.'''
        del_tail = ''' You should expect your food hamper delivery to arrive \
in 24 hours.  If you are expecting not to be home, \
please call 519-742-5860.'''
        gift_tail = '''If you will not be able to make your gift appointment \
please call 519-742-5860.'''

        if all((self.gift_date, self.route_num)):
            also = 'also '
            return f'{mess_head} {hdq_mess} {del_tail} You also{gift_mess} {gift_tail}'
        elif self.route_num:
            return f'{mess_head} {hdq_mess} {del_tail}'
        elif self.gift_date:
            return f'{mess_head} You {gift_mess} {gift_tail}'
        else:
            return None

class contact_manager:
    '''
    this class provides a way to extract recipient data from the 
    database and instantiate and set attributes of recipient class objects

    it takes a database manager class, configuration file to view 
    recipient data and configuration parameters
    :param: target is the day that events are happening - essentially gift
    appointments
    :param: route_floor is the last route that was delivered or the route
    that we are actively targetting in the queue.  this will be used
    to caclulate the range of routes containing recipients that we will 
    send an sms update to.
    
    this class holds on to the recipients and exposes their __str__ 
    methods via the __iter__ method to that once the recipient objects have
    the correct data set in them (gift appointments, route numbers and 
    contact phone number) we can easly cycle through and send
    all the sms update strings via twilio
    
    order of operations
    .set_gift_status()
    .set_route_status()
    
    then using another function or class iterate through this class
    via the __iter__ method
    '''
    
    
    def __init__(self, db_manager, config_class, target, route_floor):
        self.dbm = db_manager # instantiated database_manager class
        self.conf = config_class
        self.target_date = target # the day that things are happening e.g 4 for
                                  # dec 4 - must be int
        self.route_floor = route_floor # current route we are operating on
        self.day = datetime.now().day
        self.contacts = defaultdict(recipient) # dictionary of HH's to contact
                           # key = hhid value = recpient class 

    def set_gift_status(self, dbase='client_db', sabase='sa', echo=False, ovrd=False):
        '''
        determines gift range with help from initialization parameter
        target_date (which is the day we want to remind people for)
        prior to the delivery of actual boxes it will likely be the case that
        we will need to contact people about gift appointments
        as a result there are two methods to extract data. this one for gifts
        and .set_route_status() for hampers.
        param dbase = database name that is the key to the dictionary
        in the database manager 

        :param: dbase is the database label that the db_manager uses to 
        retrieve recipient data.  It has three tables 'gift_table'
        'person_table' and 'route_table'
        :param: sabase is the label for the salvation army appointments
        with ID, day, time where ID=appointment ID, etc
        :param: echo is used to print the file ids of the households that 
        are in the queue to contact.  primarily used for testing.
        :param: ovrd is a toggle for using the target date (False)
        or instead ignoring the target date (True) when running tests with
        the test database setup.

        '''
        # find the low and high number in the range of appointments
        # for the target date we want to remind people about i.e Dec 4
        # maps appointments 1 to 286 
        lw, hi = self.conf.return_gift_dates()[self.target_date]
        # use those two numbers to pull the appointments in that range
        # from the client database
        fids = []

        if not ovrd: # if we are not testing 
            # check to make sure the date passed in is actually valid
            if int(self.target_date) not in self.conf.gift_dates.keys():
                raise ValueError('target date is not a valid date')

        for fid, app_num, pn in self.dbm.return_app_range(dbase, lw, hi):
            # we have the file id and app numbers
            # now lookup what day and time the app num maps to

            dy, tm = self.dbm.return_app_date(sabase, app_num)
            # add the data to the contacts data structure
            # keyed to file id
            self.contacts[fid].set_gift_data(app_num, f'{dy} {tm}')
            fids.append(fid)
            if not self.contacts[fid].check_status():
                self.contacts[fid].set_contact_data(fid, pn)

        print(f'{len(fids)} SA gift apps set by set_gift_status() method')
        if echo: print(fids)
            
    def set_route_status(self, dbase='client_db', echo=False,ovrd=False):
        '''
        iterates through recipients in the delivery queue
        that have route numbers in the active range and queries via a 
        query to the client database.  This method is used 
        when we are at the delivery phase of operations
        :param: dbase contains the label for the db_manager and allows
        access to the 'person_table' and 'route_table' to pull out
        route number (and phone number if not already extracted
        by the set_gift_status() method
        for :params: echo and ovrd see the set_gift_status() method

        '''
        # first make sure that the date we are targetting is a delivery date
        av_shipped, del_dates = self.conf.return_delivery_data()
        lw = int(input(f'confirm current route is {self.route_floor}'))
        hi = lw + int(av_shipped)
        fids = []
        
        if not ovrd: # if we are not testing...
            if int(self.target_date) not in del_dates:
                raise ValueError('target date is not a valid date')

        for fid, rn, pn in self.dbm.return_route_range(dbase, lw, hi):
            self.contacts[fid].set_route_data(rn,self.route_floor)
            
            fids.append(fid)

            if not self.contacts[fid].check_status():
                self.contacts[fid].set_contact_data(fid, pn)
        
        print(f'{len(fids)} routes set by set_route_status() method')
        if echo: print(fids)

    def __iter__(self):
        '''
        exposes the recipient classes __str__() method  held in the contacts 
        attribute keyed to the file id of the recipient

        once the set_X_status methods are used, this method will allow
        another function or class to make use of the sms string
        that should be sent to each household
        '''

        for k in self.contacts:
            household = self.contacts[k]
            if household.check_status():
                yield household.__str__()
            else:
                yield None

### TEST FUNCTIONS ###

def ld_client(echo=False):
    '''
    load the configuration file and twilio client
    and return them in that order
    '''
    # this is a basic test of the functionality
    print('attempting to load configuration data')
    c_f = configuration('setup.yml')
    if echo: c_f.print_creds()
    sid, token, f_num  = c_f.return_creds(cred_type='production')
    client = twilio_client(sid, token, f_num)
    print('configuration loaded: good to go')
    return c_f, client

def test_twilio():
    '''
    basic sanity test for the twilio client and its basic function
    send a short string to the live_test_number to make sure
    that we can actually send sms messages
    '''
    cf, client = ld_client()
    to_phone = c_f.live_test_number
    from_phone = c_f.phone_number
    if client: client.send_sms(to_phone, 'hello from the Internet',from_phone)

def test_database():
    '''
    make sure that the methods of the database_manager class
    work and that the structure of the databases are correct and 
    the test values they contain match expectations
    '''
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

def trial_run():
    '''
    this testing function will use the testing database and values
    to simulate a trial run of the contact manager
    and twilio client
    '''
    cf, client = ld_client()
    to_phone = cf.live_test_number
    dbm = database_manager({'client_db': 'sms_client_test.db', 
                             'sa': 'sa_2019_appointments.db'})
    dbm.initialize_connections()
    con_manager = contact_manager(dbm, cf, 4, 90)

    con_manager.set_route_status(echo=True,ovrd=True)
    con_manager.set_gift_status(echo=True,ovrd=True)
    
    for hh in con_manager:
        if hh:
            print(hh)
        else:
            print('missing value')
    
    dbm.close_all()


### COMMAND LINE FUNCTIONS ###

#def parse_food(food, limit=0):
#    f = food
#    if food == 'None' or 'none': f = False
#    if int(food) == 0: f = False
#    if int(food) < limit: f = False
#    if int(food) > limit: f = int(food)
#    return f

#def send_it(args):
#    '''
#    usage is as follows:
#    file.py delivery [start of delivery range] --toys [start of appointment
#    range]
#
#    if only doing gift update use delivery 0
#    if only doing delivery routes omit --toys 
#
#    e.g.
#    file.py delivery 100 --toys=45
#    file.py delivery 100
#    file.py delivery 0 --toys=500
#
#    '''
#
#    lim =int(args.limit)
#    food = parse_food(args.food, lim)
#    
#    if all((food, args.toys)):
#        print(f'hello! you are in route number {args.food} and you have toy app: {args.toys} have a great day!')
#    elif food and not args.toys:
#        print(f'hello! you are in route number {food}')
#    elif args.toys and not food:
#        print(f'hello! you have appointment number {args.toys}')
#    elif not args.toys and not food:
#        print('nothing to say!')


#parser = argparse.ArgumentParser()
#parser.add_argument('--version', action='version',version='1.0.0')
#subparsers = parser.add_subparsers()

#food_parser = subparsers.add_parser('delivery')
#food_parser.add_argument('food',  help= 'start of route # range to send an sms')
#food_parser.add_argument('--toys', default=None, help='start of gift range')
#food_parser.add_argument('--limit', default=0, help='last route number range pinged')
#food_parser.set_defaults(func=send_it)


if __name__ == '__main__':
#   args = parser.parse_args()
#   args.func(args)
    trial_run()    






