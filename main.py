import argparse
from knox_utils.cluster import is_knox_installed, configure_knox
from knox_utils.params import USERNAME, PASSWORD, CLUSTER_NAME, AMBARI_BASE_URL
from knox_utils.update_config import update_config_if_needed

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check-knox', action='store_true', help='Check if Knox is installed')
    parser.add_argument('--local', default='true', choices=['true', 'false'], help='If true, update config.ini based on Ambari properties (local mode)')
    parser.add_argument('--configure-knox', action='store_true', help='Configure Knox proxyuser in Hadoop')
    args = parser.parse_args()

    local = args.local == 'true'

    # Always update config if local, before any other logic
    if local:
        update_config_if_needed()

    if args.check_knox:
        try:
            if is_knox_installed():
                print("KNOX is installed.")
            else:
                print("KNOX is NOT installed.")
        except Exception as e:
            print(e)
    elif args.configure_knox:
        try:
            configure_knox()
        except Exception as e:
            print(f"Error configuring Knox: {e}")
    else:
        print("No action specified. Use --check-knox, --configure-knox or other flags.")

if __name__ == "__main__":
    main()
