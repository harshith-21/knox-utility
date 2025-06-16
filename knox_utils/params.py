import os
import configparser

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))

config = configparser.ConfigParser()
config.read(CONFIG_PATH)

# All possible variables needed for the app
AMBARI_PROPERTIES_PATH = '/etc/ambari-server/conf/ambari.properties'
USERNAME = config.get('ambari', 'username', fallback='admin')
PASSWORD = config.get('ambari', 'password', fallback='admin')
CLUSTER_NAME = config.get('ambari', 'cluster_name', fallback='mycluster')
PROTOCOL = config.get('ambari', 'protocol', fallback='http')
PORT = config.get('ambari', 'port', fallback='8080')
AMBARI_HOST = config.get('ambari', 'host', fallback='localhost')
AMBARI_BASE_URL = f"{PROTOCOL}://{AMBARI_HOST}:{PORT}"

# Add more variables as needed for future features
