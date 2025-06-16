import os
import configparser
import time
from knox_utils.params import AMBARI_PROPERTIES_PATH, CONFIG_PATH

def update_config_if_needed():
    """
    If Ambari properties file is newer than config.ini, update protocol/port in config.ini.
    """
    if not os.path.exists(AMBARI_PROPERTIES_PATH) or not os.path.exists(CONFIG_PATH):
        return
    props_mtime = os.path.getmtime(AMBARI_PROPERTIES_PATH)
    config_mtime = os.path.getmtime(CONFIG_PATH)
    if props_mtime > config_mtime:
        protocol = 'http'
        port = 8080
        with open(AMBARI_PROPERTIES_PATH) as f:
            for line in f:
                if line.startswith('client.api.ssl.port'):
                    port = int(line.split('=')[1].strip())
                elif line.startswith('api.ssl'):
                    if line.split('=')[1].strip().lower() == 'true':
                        protocol = 'https'
        config = configparser.ConfigParser()
        config.read(CONFIG_PATH)
        if 'ambari' not in config:
            config['ambari'] = {}
        config['ambari']['protocol'] = protocol
        config['ambari']['port'] = str(port)
        with open(CONFIG_PATH, 'w') as configfile:
            config.write(configfile)
