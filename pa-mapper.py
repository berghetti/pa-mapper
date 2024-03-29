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

def valid_user(user):
    user = user.strip()

    # Unifi has NULL char end string, remove this
    user = user.rstrip('\x00')

    if user == 'anonymous' or user == '': return False

    return user

def get_unifi_users():
    unifi = Unifi(config=CONFIG_FILE)
    unifi.login()

    users = []
    for client in unifi.getClients():
        if client['is_wired'] == True or \
                '1x_identity' not in client or 'ip' not in client:
            continue

        user = client['1x_identity']
        user = valid_user(user)
        if user == False: continue

        ip = client['ip'].strip()
        if ip == '': continue

        users.append({'user': user, 'ip': ip})

    unifi.logout()

    return users

def get_omada_users():
    omada = Omada(config=CONFIG_FILE)
    omada.login()

    users = []
    for client in omada.getSiteClients():
        if client['wireless'] == False or \
                'ip' not in client or 'dot1xIdentity' not in client:
            continue

        user = client['dot1xIdentity']
        user = valid_user(user)
        if user == False: continue

        ip = client['ip'].strip()
        if ip == '': continue

        users.append({'user': user, 'ip': ip})

    omada.logout()

    return users

def do_user_mapping(pa):
    while True:
        users = []
        users += get_omada_users()
        users += get_unifi_users()

        for user in users:
            pa.add_entry(user['user'], user['ip'])

        # send mapps to pa
        if len(users) > 0:
            if pa.mapp() == False:
                logging.error('Error map')

            logging.info(f'Updated {len(users)} users')

        time.sleep(update_interval)

def setup():
    global CONFIG_FILE, update_interval
    CONFIG_FILE = sys.argv[1]

    config = ConfigParser()
    config.read(CONFIG_FILE)
    update_interval = int(config['common']['update'])
    LOG_CODES = {'DEBUG': 10, 'INFO': 20, 'WARNING': 30, 'ERROR': 40}
    lvl = config['common']['log']
    debug = LOG_CODES[lvl]

    logging.basicConfig(filename='/var/log/pa_mapper.log', level=debug,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%d-%m-%Y %H:%M:%S')

def main():
    setup()

    logging.info('Starting pa-mapper')

    pa = Pa(config=CONFIG_FILE)
    if pa.login() == False:
        logging.error('Error PA Login')
        exit(1)

    do_user_mapping(pa)
    logging.info('Stoping pa-mapper')

if __name__ == '__main__':
    main()
