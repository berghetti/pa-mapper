
#!/usr/bin/env python3

import sys
import time
import logging
from configparser import ConfigParser

from mods.unifi import Unifi
from mods.omada import Omada
from mods.pa import Pa

CONFIG_FILE = None
update_interval = 15
omada_enable = False
unifi_enable = False

unifi = None
omada = None

def valid_user(user):
    user = user.strip()
    user = user.rstrip('\x00')  # Remove null char
    if user == 'anonymous' or user == '':
        return False
    return user

def get_unifi_users():
    users = []
    for client in unifi.getClients():
        if client['is_wired'] or '1x_identity' not in client or 'ip' not in client:
            continue

        user = valid_user(client['1x_identity'])
        if not user:
            continue

        ip = client['ip'].strip()
        if ip == '':
            continue

        users.append({'user': user, 'ip': ip})

    return users

def get_omada_users():
    users = []
    for client in omada.getSiteClients():
        if not client['wireless'] or 'ip' not in client or 'dot1xIdentity' not in client:
            continue

        user = valid_user(client['dot1xIdentity'])
        if not user:
            continue

        ip = client['ip'].strip()
        if ip == '':
            continue

        users.append({'user': user, 'ip': ip})

    return users

def do_user_mapping(pa):
    while True:
        users = []
        if omada_enable:
            users += get_omada_users()
        if unifi_enable:
            users += get_unifi_users()

        for user in users:
            pa.add_entry(user['user'], user['ip'])

        if users:
            if not pa.mapp():
                logging.error('Error map')
            logging.info(f'Updated {len(users)} users')

        time.sleep(update_interval)

def setup():
    global CONFIG_FILE, update_interval, omada_enable, unifi_enable, unifi, omada
    CONFIG_FILE = sys.argv[1]

    config = ConfigParser()
    config.read(CONFIG_FILE)

    update_interval = int(config['common'].get('update', 15))
    LOG_CODES = {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40}
    lvl = config['common'].get('log', 'INFO')
    debug = LOG_CODES.get(lvl.upper(), 20)

    omada_enable = config.getboolean('omada', 'enable', fallback=False)
    unifi_enable = config.getboolean('unifi', 'enable', fallback=False)

    logging.basicConfig(filename='/var/log/pa_mapper.log', level=debug,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%d-%m-%Y %H:%M:%S')

    if omada_enable:
        omada = Omada(config=CONFIG_FILE)
        if not omada.login():
            logging.error('Omada login failed')
            omada_enable = False
        else:
            logging.info('Omada login successful')
    else:
            logging.info('Omada disabled')

    if unifi_enable:
        unifi = Unifi(config=CONFIG_FILE)
        if not unifi.login():
            logging.error('Unifi login failed')
            unifi_enable = False
        else:
            logging.info('Unifi login successful')
    else:
            logging.info('Unifi disabled')


def main():
    setup()

    logging.info('Starting pa-mapper')

    pa = Pa(config=CONFIG_FILE)
    if not pa.login():
        logging.error('Error PA Login')
        exit(1)

    try:
        do_user_mapping(pa)
    finally:
        if omada_enable and omada:
            omada.logout()
        if unifi_enable and unifi:
            unifi.logout()
        logging.info('Stopping pa-mapper')

if __name__ == '__main__':
    main()
