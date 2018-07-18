from neomodel import config
from beacon_controller import utils

db_config = utils.load_config(silent=False)['client']['database']

username = db_config['username']
password = db_config['password']
address = db_config['address']

if 'bolt://' in address:
    address = address.replace('bolt://', '')
elif 'http://' in address or 'https://' in address:
    raise Exception('Only bolt protocol is allowed')

config.DATABASE_URL = 'bolt://{}:{}@{}'.format(username, password, address)
