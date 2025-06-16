import requests
from .params import AMBARI_BASE_URL, USERNAME, PASSWORD, CLUSTER_NAME
import urllib3


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

