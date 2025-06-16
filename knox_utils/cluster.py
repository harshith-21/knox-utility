import requests
from .params import AMBARI_BASE_URL, USERNAME, PASSWORD, CLUSTER_NAME
import urllib3
import json
import time


def get_ambari_cluster_name():
    """
    Fetches the cluster name from Ambari via API call.
    Returns the cluster name as a string, or None if not found.
    """
    try:
        url = f"{AMBARI_BASE_URL}/api/v1/clusters"
        response = requests.get(url, auth=(USERNAME, PASSWORD), timeout=10)
        if response.status_code == 200:
            data = response.json()
            items = data.get('items', [])
            if items and 'Clusters' in items[0] and 'cluster_name' in items[0]['Clusters']:
                return items[0]['Clusters']['cluster_name']
        return None
    except Exception:
        return None

def is_knox_installed():
    url = f"{AMBARI_BASE_URL}/api/v1/clusters/{CLUSTER_NAME}/services/KNOX"
    if AMBARI_BASE_URL.startswith('https'):
        try:
            response = requests.get(url, auth=(USERNAME, PASSWORD), timeout=10)
        except requests.exceptions.SSLError:
            print("[WARN] SSL verification failed. Retrying with SSL verification disabled.")
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.get(url, auth=(USERNAME, PASSWORD), timeout=10, verify=False)
    else:
        response = requests.get(url, auth=(USERNAME, PASSWORD), timeout=10)
    try:
        data = response.json()
    except Exception:
        data = {}
    # Check for 404 or error message in response
    if response.status_code == 404 or (
        isinstance(data, dict) and data.get('status') == 404 and 'Service not found' in data.get('message', '')):
        return False
    # Check for ServiceInfo in response (Knox present)
    if response.status_code == 200 and 'ServiceInfo' in data:
        return True
    # Fallback: treat as not installed if not clear
    return False

def configure_knox():
    """
    Adds/updates proxyuser.knox.* properties in core-site (Hadoop) via Ambari API using configs.py logic.
    Sets proxyuser.knox.groups=* and proxyuser.knox.hosts=*
    """
    from .params import AMBARI_HOST, USERNAME, PASSWORD, PROTOCOL, PORT, CLUSTER_NAME
    from . import configs
    print("[INFO] Configuring Knox proxyuser in Hadoop core-site via Ambari API using configs.py...")
    try:
        accessor = configs.api_accessor(
            host=AMBARI_HOST,
            login=USERNAME,
            password=PASSWORD,
            protocol=PROTOCOL,
            port=PORT,
            unsafe=True
        )
        version_note = "Set proxyuser.knox.* for Knox gateway"
        def update_proxyuser_knox(cluster, config_type, accessor):
            try:
                properties, attributes = configs.get_current_config(cluster, config_type, accessor)
            except Exception as e:
                print(f"[ERROR] Failed to fetch current core-site config: {e}")
                raise
            properties['hadoop.proxyuser.knox.groups'] = '*'
            properties['hadoop.proxyuser.knox.hosts'] = '*'
            return properties, attributes
        try:
            configs.update_config(
                cluster=CLUSTER_NAME,
                config_type='core-site',
                config_updater=update_proxyuser_knox,
                accessor=accessor,
                version_note=version_note
            )
            print("[SUCCESS] Knox proxyuser properties updated in core-site using configs.py.")
        except Exception as e:
            print(f"[ERROR] Failed to update core-site config: {e}")
    except Exception as e:
        print(f"[ERROR] Unexpected error in configure_knox: {e}")

