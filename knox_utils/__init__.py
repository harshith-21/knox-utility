import os
import configparser
import time

CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config.ini'))

# Handles reading and updating config.ini
class KnoxConfig:
    def __init__(self, config_path=CONFIG_PATH):
        self.config_path = config_path
        self.config = configparser.ConfigParser()
        self.config.read(self.config_path)
        if 'ambari' not in self.config:
            self.config['ambari'] = {}

    def get(self, key, fallback=None):
        return self.config['ambari'].get(key, fallback)

    def set(self, key, value):
        self.config['ambari'][key] = str(value)
        self.save()

    def save(self):
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)

    def update_from_dict(self, d):
        for k, v in d.items():
            self.config['ambari'][k] = str(v)
        self.save()

    def as_dict(self):
        return dict(self.config['ambari'])

# Usage:
# from knox_utils import KnoxConfig
# config = KnoxConfig()
# config.get('username')
# config.update_from_dict({'protocol': 'https'})
