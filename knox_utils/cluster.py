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

def set_knox_proxy_users():
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
        print(f"[ERROR] Unexpected error in set_knox_proxy_users: {e}")

def set_knox_whitelist():
    """
    Configures Knox gateway.dispatch.whitelist property in Advanced gateway-site configuration
    based on hostname patterns discovered from cluster hosts via Ambari API.
    
    Fetches all cluster hostnames, analyzes them for common domain patterns,
    and generates appropriate whitelist regex if a consistent pattern is found.
    """
    from .params import AMBARI_HOST, USERNAME, PASSWORD, PROTOCOL, PORT, CLUSTER_NAME, AMBARI_BASE_URL
    from . import configs
    import requests
    import urllib3
    
    print("[INFO] Configuring Knox whitelist based on cluster hostname patterns...")
    
    # Create accessor for API calls
    try:
        accessor = configs.api_accessor(
            host=AMBARI_HOST,
            login=USERNAME,
            password=PASSWORD,
            protocol=PROTOCOL,
            port=PORT,
            unsafe=True
        )
    except Exception as e:
        print(f"[ERROR] Failed to create API accessor: {e}")
        raise
    
    # Fetch all cluster hostnames via Ambari API
    try:
        print("[INFO] Fetching cluster hostnames from Ambari API...")
        hosts_url = f"{AMBARI_BASE_URL}/api/v1/clusters/{CLUSTER_NAME}/hosts"
        
        if AMBARI_BASE_URL.startswith('https'):
            try:
                response = requests.get(hosts_url, auth=(USERNAME, PASSWORD), timeout=10)
            except requests.exceptions.SSLError:
                print("[WARN] SSL verification failed. Retrying with SSL verification disabled.")
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
                response = requests.get(hosts_url, auth=(USERNAME, PASSWORD), timeout=10, verify=False)
        else:
            response = requests.get(hosts_url, auth=(USERNAME, PASSWORD), timeout=10)
        
        if response.status_code != 200:
            error_msg = f"[ERROR] Failed to fetch cluster hosts. Status: {response.status_code}"
            print(error_msg)
            raise ValueError(error_msg)
        
        hosts_data = response.json()
        hostnames = []
        
        for item in hosts_data.get('items', []):
            hostname = item.get('Hosts', {}).get('host_name')
            if hostname:
                hostnames.append(hostname)
        
        if not hostnames:
            error_msg = "[ERROR] No hostnames found in cluster"
            print(error_msg)
            raise ValueError(error_msg)
        
        print(f"[INFO] Found {len(hostnames)} cluster hostnames: {hostnames}")
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch cluster hostnames: {e}")
        raise
    
    # Analyze hostnames for common domain pattern
    print("[INFO] Analyzing hostnames for common domain patterns...")
    
    # Extract domain suffixes (last 2 parts when split by '.')
    domain_suffixes = []
    valid_hostnames = []
    
    for hostname in hostnames:
        parts = hostname.split('.')
        if len(parts) >= 3:  # Must have at least 3 parts for FQDN
            domain_suffix = '.'.join(parts[-2:])  # Get last 2 parts
            domain_suffixes.append(domain_suffix)
            valid_hostnames.append(hostname)
            print(f"[DEBUG] {hostname} → domain suffix: {domain_suffix}")
        else:
            print(f"[WARN] Skipping hostname with insufficient parts: {hostname} ({len(parts)} parts)")
    
    if not domain_suffixes:
        error_msg = "[ERROR] No valid FQDNs found in cluster hostnames. All hostnames must have at least 3 parts (hostname.domain.tld)"
        print(error_msg)
        raise ValueError(error_msg)
    
    # Check if all domain suffixes are the same
    unique_suffixes = set(domain_suffixes)
    
    if len(unique_suffixes) == 1:
        # All hostnames share the same domain suffix
        common_domain = list(unique_suffixes)[0]
        print(f"[SUCCESS] Found common domain pattern: {common_domain}")
        
        # Generate whitelist regex pattern
        escaped_domain = common_domain.replace(".", "\\.")
        whitelist_regex = f'^https?:\\/\\/(.+\\.{escaped_domain}):[0-9]+\\/?.*$'
        
        print(f"[INFO] Generated whitelist regex: {whitelist_regex}")
        
    elif len(unique_suffixes) > 1:
        # Multiple different domain suffixes found
        error_msg = f"[ERROR] Multiple domain suffixes found in cluster hostnames: {unique_suffixes}. Cannot generate consistent whitelist pattern."
        print(error_msg)
        print(f"[INFO] Hostnames analyzed: {valid_hostnames}")
        raise ValueError(error_msg)
    
    else:
        # This shouldn't happen, but just in case
        error_msg = "[ERROR] Unexpected error in domain suffix analysis"
        print(error_msg)
        raise ValueError(error_msg)
    
    try:
        accessor = configs.api_accessor(
            host=AMBARI_HOST,
            login=USERNAME,
            password=PASSWORD,
            protocol=PROTOCOL,
            port=PORT,
            unsafe=True
        )
        
        version_note = "Set Knox gateway.dispatch.whitelist for hostname pattern"
        
        def update_knox_whitelist(cluster, config_type, accessor):
            try:
                properties, attributes = configs.get_current_config(cluster, config_type, accessor)
            except Exception as e:
                print(f"[ERROR] Failed to fetch current gateway-site config: {e}")
                raise
            
            # Set the whitelist property
            properties['gateway.dispatch.whitelist'] = whitelist_regex
            print(f"[INFO] Setting gateway.dispatch.whitelist = {whitelist_regex}")
            
            return properties, attributes
        
        try:
            configs.update_config(
                cluster=CLUSTER_NAME,
                config_type='gateway-site',
                config_updater=update_knox_whitelist,
                accessor=accessor,
                version_note=version_note
            )
            print("[SUCCESS] Knox whitelist property updated in gateway-site configuration.")
        except Exception as e:
            print(f"[ERROR] Failed to update gateway-site config: {e}")
            raise
            
    except Exception as e:
        print(f"[ERROR] Unexpected error in set_knox_whitelist: {e}")
        raise

def flush_topology_to_local(topology_vars):
    """
    Renders the advanced topology Jinja template using topology_vars and writes the output to a local file.
    """
    from jinja2 import Environment, FileSystemLoader
    import os
    template_dir = os.path.join(os.path.dirname(__file__), '../templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('advaned_topology_template.j2')
    rendered = template.render(**topology_vars)
    output_path = os.path.join(os.path.dirname(__file__), '../rendered_topology.xml')
    with open(output_path, 'w') as f:
        f.write(rendered)
    print(f"[SUCCESS] Rendered topology written to {output_path}")

def configure_knox():
    """
    Calls set_knox_proxy_users, set_knox_whitelist and will call other Knox configuration functions as needed.
    """
    print("[INFO] Running Knox configuration steps...")
    set_knox_proxy_users()
    set_knox_whitelist()
    topology_vars = get_topology_vars()
    flush_topology_to_local(topology_vars)
    apply_topology_to_knox()
    # Future: call other Knox-related configuration functions here

def get_topology_vars():
    """
    Prepares to apply the advanced topology template by collecting all required variables.
    
    Variables needed from the Jinja template (excluding those inside {% raw %} tags):
    - ambariui_protocol
    - ambariui_host
    - ambariui_port
    - ambariws_protocol
    - ambariws_host
    - ambariws_port
    - ranger_protocol (if is_ranger_installed)
    - ranger_host (if is_ranger_installed)
    - ranger_port (if is_ranger_installed)
    - rangerui_protocol (if is_ranger_installed)
    - rangerui_host (if is_ranger_installed)
    - rangerui_port (if is_ranger_installed)
    - solr_protocol (if is_solr_installed)
    - solr_host (if is_solr_installed)
    - solr_port (if is_solr_installed)
    - hdfsui_protocol
    - hdfsui_host
    - hdfsui_port
    - is_namenode_ha
    - is_ranger_installed
    - is_solr_installed
    """
    from .params import AMBARI_HOST, AMBARI_BASE_URL, PORT
    ambariws_protocol = 'ws'  # as per user instruction
    ambariws_host = AMBARI_HOST
    ambariws_port = PORT
    # Placeholders for the rest, to be filled in next steps
    ranger_protocol = None
    ranger_host = None
    ranger_port = None
    rangerui_protocol = None
    rangerui_host = None
    rangerui_port = None
    solr_protocol = None
    solr_host = None
    solr_port = None
    hdfsui_protocol = None
    hdfsui_host = None
    hdfsui_port = None
    is_namenode_ha = False
    is_ranger_installed = False
    is_solr_installed = False
    yarnui_protocol = None
    yarnui_host = None
    yarnui_port = None

    from . import configs
    protocol = AMBARI_BASE_URL.split(':')[0]  # Extract protocol from AMBARI_BASE_URL
    accessor = configs.api_accessor(
        host=AMBARI_HOST,
        login=USERNAME,
        password=PASSWORD,
        protocol=protocol,
        port=ambariws_port,
        unsafe=True
    )
    # Example: Fetch hdfs-site, ranger-admin-site, solr-env, and custom config types
    try:
        hdfs_site, _ = configs.get_current_config(CLUSTER_NAME, 'hdfs-site', accessor)
        hdfsui_protocol = 'https' if hdfs_site.get('dfs.http.policy', '').lower() == 'https_only' else 'http'
        # Try both dfs.namenode.{protocol}-address and dfs.namenode.http-address/dfs.namenode.https-address for compatibility
        hdfsui_host = None
        hdfsui_port = None
        address_key = f'dfs.namenode.{hdfsui_protocol}-address'
        if address_key in hdfs_site:
            address = hdfs_site[address_key]
            if ':' in address:
                hdfsui_host, hdfsui_port = address.split(':', 1)
        else:
            # Fallback to legacy keys
            legacy_key = 'dfs.namenode.https-address' if hdfsui_protocol == 'https' else 'dfs.namenode.http-address'
            if legacy_key in hdfs_site:
                address = hdfs_site[legacy_key]
                if ':' in address:
                    hdfsui_host, hdfsui_port = address.split(':', 1)
        # Use Ambari API to get NameNode host
        namenode_host = None
        nn_service_url = f"{AMBARI_BASE_URL}/api/v1/clusters/{CLUSTER_NAME}/hosts?host_components/HostRoles/component_name=NAMENODE"
        try:
            response = requests.get(nn_service_url, auth=(USERNAME, PASSWORD), timeout=10, verify=False)
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                if items:
                    namenode_host = items[0]['Hosts']['host_name']
        except Exception as e:
            print(f"[WARN] Could not fetch NameNode host from Ambari API: {e}")
    except Exception as e:
        print(f"[WARN] Could not fetch hdfs-site: {e}")

    try:
        ranger_admin_properties, _ = configs.get_current_config(CLUSTER_NAME, 'admin-properties', accessor)
        is_ranger_installed = True
        ranger_base_url = ranger_admin_properties.get('policymgr_external_url', None)
        rangerui_base_url = ranger_base_url

    except Exception as e:
        print(f"[INFO] Ranger not installed or could not fetch ranger-admin-site: {e}")
        is_ranger_installed = False

    try:
        solr_env, _ = configs.get_current_config(CLUSTER_NAME, 'infra-solr-env', accessor)
        is_solr_installed = True
        solr_protocol = 'https' if solr_env.get('infra_solr_ssl_enabled', 'false').lower() == 'true' else 'http'
        # Use Ambari API to get Solr host
        solr_host = None
        solr_port = solr_env.get('infra_solr_port', None)
        try:
            solr_service_url = f"{AMBARI_BASE_URL}/api/v1/clusters/{CLUSTER_NAME}/hosts?host_components/HostRoles/component_name=INFRA_SOLR"
            response = requests.get(solr_service_url, auth=(USERNAME, PASSWORD), timeout=10, verify=False)
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                if items:
                    solr_host = items[0]['Hosts']['host_name']
        except Exception as e:
            print(f"[WARN] Could not fetch Solr host from Ambari API: {e}")
    except Exception as e:
        print(f"[INFO] Solr not installed or could not fetch infra-solr-env: {e}")
        is_solr_installed = False

    try:
        yarn_site, _ = configs.get_current_config(CLUSTER_NAME, 'yarn-site', accessor)
        yarn_log_url = yarn_site.get('yarn.log.server.web-service.url', None)
        yarnui_protocol = None
        yarnui_host = None
        yarnui_port = None
        if yarn_log_url:
            # Remove everything from /ws onward
            import re
            match = re.match(r'^(https?)://([^:/]+)(?::(\d+))?', yarn_log_url)
            if match:
                yarnui_protocol = match.group(1)
                yarnui_host = match.group(2)
                yarnui_port = match.group(3)
    except Exception as e:
        print(f"[WARN] Could not fetch yarn-site or parse yarn.log.server.web-service.url: {e}")

    topology_vars = {
        'ambari_ui_url': AMBARI_BASE_URL,
        'ambariws_protocol': ambariws_protocol,
        'ambariws_host': ambariws_host,
        'ambariws_port': ambariws_port,
        'ranger_base_url': ranger_base_url,
        'rangerui_base_url': rangerui_base_url,
        'solr_protocol': solr_protocol,
        'solr_host': solr_host,
        'solr_port': solr_port,
        'hdfsui_protocol': hdfsui_protocol,
        'hdfsui_host': namenode_host,
        'hdfsui_port': hdfsui_port,
        'namenode_host': namenode_host,
        'yarnui_protocol': yarnui_protocol,
        'yarnui_host': yarnui_host,
        'yarnui_port': yarnui_port,
        'is_namenode_ha': is_namenode_ha,
        'is_ranger_installed': is_ranger_installed,
        'is_solr_installed': is_solr_installed
    }
    print("[DEBUG] Topology variables initialized:")
    for k, v in topology_vars.items():
        print(f"  {k}: {v}")
    return topology_vars

def apply_topology_to_knox():
    """
    Reads the rendered topology XML from disk and applies it to Knox's advanced topology via Ambari API using configs.py.
    """
    from .params import AMBARI_HOST, USERNAME, PASSWORD, AMBARI_BASE_URL, CLUSTER_NAME, PORT
    from . import configs
    import os
    rendered_path = os.path.join(os.path.dirname(__file__), '../rendered_topology.xml')
    if not os.path.exists(rendered_path):
        print(f"[ERROR] Rendered topology file not found at {rendered_path}")
        return
    with open(rendered_path, 'r') as f:
        topology_xml = f.read()
    # Use configs.py to update Knox's advanced topology
    try:
        accessor = configs.api_accessor(
            host=AMBARI_HOST,
            login=USERNAME,
            password=PASSWORD,
            protocol=AMBARI_BASE_URL.split(':')[0],
            port=PORT,
            unsafe=True
        )
        def update_knox_topology(cluster, config_type, accessor):
            properties, attributes = configs.get_current_config(cluster, config_type, accessor)
            # Set the 'content' property for the topology config type (Ambari/Knox expects this)
            properties['content'] = topology_xml
            return properties, attributes
        configs.update_config(
            cluster=CLUSTER_NAME,
            config_type='topology',  # This should match the config type used in Ambari for Knox topology
            config_updater=update_knox_topology,
            accessor=accessor,
            version_note='Update Knox advanced topology via automation'
        )
        print("[SUCCESS] Applied advanced topology to Knox via Ambari API.")
        print("[INFO] If you want to verify, check the 'topology' config type in Ambari for the Knox service.")
    except Exception as e:
        print(f"[ERROR] Failed to apply topology to Knox: {e}")

