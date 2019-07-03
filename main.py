#!/usr/bin/python3.6

import yaml
from twilio.rest import Client

class configuration:
    def __init__(self, config_file):
        self.config = config_file 
        # production creds
        self.secret = None
        self.auth = None
        # testing creds
        self.test_secret = None 
        self.test_auth = None
        # number that twilio will sms from
        self.phone_number = None 
        self.test_number = None

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
            except:
                print('failed to open config file')

    def return_creds(self, cred_type='test'):
        '''
        returns secret, auth attributes
        cred_type flag == test to return test creds
        otherwise returns the actual credentials
        '''
        if cred_type == 'test':
            return self.test_secret, self.test_auth
        else:
            return self.secret, self.auth

    def print_creds(self):
        print(f'secret {self.secret} auth {self.auth} phone {self.phone_number}')
        print(f'test secret {self.test_secret} test_auth {self.test_auth}')

if __name__ == '__main__':
    config_file = configuration('setup.yml')
    config_file.print_creds()
    sid, token  = config_file.return_creds(cred_type='production')
    client = Client(sid, token)
    print('good to go')
    message = client.messages.create(
            to="+15194983069", 
            from_=config_file.phone_number,
            body="Hello from Python!")
