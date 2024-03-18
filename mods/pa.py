import requests
import re
import logging
from configparser import ConfigParser

class Pa:
    def __init__(self, config='config.cfg'):
        self.config = ConfigParser()
        self.config.read(config)
        self.verify = self.config['common'].getboolean('verify', True)
        self.warnings = self.config['common'].getboolean('warnings', True)
        self.ip = self.config['pa'].get('ip')
        self.timeout = self.config['pa'].get('timeout', 5)

        self.logged = False
        self.key = None
        self.entries = ''

        self.log = logging.getLogger(__name__)

        # hide warnings about insecure SSL requests
        if self.verify == False and self.warnings == False:
            requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)


    def login(self):
        username = self.config['pa'].get('username')
        password = self.config['pa'].get('password')
        url=f'https://{self.ip}/api/?type=keygen&user={username}&password={password}'

        try:
            r = requests.get(url, verify=self.verify, timeout=5)
        except Exception as e:
            self.log.error(e)
            return False

        if (r.status_code != 200):
            self.log.error('PA login error')
            return False

        match = re.search(r'<key>(.*?)</key>', r.text)
        if match:
            self.key = match.group(1)
        else:
            self.log.error("Error pa login.")
            return False

        return True

    def _create_entry(self, user, ip):
        return f'<entry name="{user}" ip="{ip}" timeout="{self.timeout}"></entry>'

    def _clear_entries(self):
        self.entries = ''

    def add_entry(self, user, ip):
        self.entries += self._create_entry(user, ip)

    def get_entries(self):
        return self.entries

    def mapp(self):
        if self.key == None:
            self.log.error('No pa key')
            return False

        url = f'https://{self.ip}/api/?type=user-id&key={self.key}'

        command = f'<uid-message><version>1.0</version><type>update</type><payload><login>{self.entries}</login></payload></uid-message>'

        data = {'cmd': command}
        r = requests.post(url, data=data, verify=self.verify)

        if (r.status_code != 200):
            self.log.error(f'Error to mapp users in PA\n{r.text}')
            return False

        self._clear_entries()
        return True

# test
def main():
    pa = Pa()
    pa.login()

if __name__ == '__main__':
    main()
