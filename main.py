import yaml
from twilio.rest import Client


class configuration:
    def __init__(self, config_file):
        self.config = config_file
        self.secret = None
        self.auth = None
        
        if self.config:
            try:
                print(f'trying to open {self.config}')
                f = self.config
                with open(f, 'r') as ymlfile:
                    yfile = yaml.load(ymlfile)
                    self.secret = yfile['sid']
                    self.auth = yfile['token']
            except:
                print('failed to open config file')

    def return_creds(self):
        return self.secret, self.auth

if __name__ == '__main__':
    config_file = configuration('setup.yml')
    sid, token  = config_file.return_creds()
    client = Client(sid, token)
    print('good to go')
