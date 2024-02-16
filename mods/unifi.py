
import requests
import logging
from configparser import ConfigParser

class Unifi:
    def __init__(self, config='config.cfg'):
        self.config = ConfigParser()
        self.config.read(config)
        self.verify = self.config['common'].getboolean('verify', True)
        self.warnings = self.config['common'].getboolean('warnings', True)
        self.baseurl = self.config['unifi'].get('baseurl')
        self.site = self.config['unifi'].get('site', 'default')

        self.logged = False
        self.session = None
        
        self.log = logging.getLogger(__name__)

        # hide warnings about insecure SSL requests
        if self.verify == False and self.warnings == False:
            requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

    def _build_url(self, path):
        return self.baseurl + '/api' + path

    def _build_url_endpoint(self, path):
        if not self.logged:
            self.log.error('Not logged in unifi')
            return
        
        return self.baseurl + '/api/s/' + self.site + path

    def _get(self, path, data=None):
        r = self.session.get(self._build_url_endpoint(path), json=data, headers=self.session.headers, verify=self.verify)
        if (r.status_code != 200):
            self.log.error(f'Error to get {path}')

        return r.json()['data']

    def login(self):
        username = self.config['unifi'].get('username')
        password = self.config['unifi'].get('password')
        data = {'username': username, 'password': password}

        self.session = requests.Session()
        r = self.session.post(self._build_url('/login'), json=data, verify=self.verify)
        if r.status_code != 200:
            self.log.error('Error login unifi')
            return

        self.logged = True

    def logout(self):
        self.session.post(self._build_url('/logout'), verify=self.verify)
        self.logged = False

    def getClients(self):
        return self._get('/stat/sta')

# example
def main():
    unifi = Unifi()
    unifi.login()
 
    for client in unifi.getClients():
        print(client)
    
    unifi.logout()

if __name__ == '__main__':
    main()

