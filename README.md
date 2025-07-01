# Knox Utility

A comprehensive Python utility for automating Apache Knox Gateway configuration and management in Hadoop clusters via Ambari API.

## 📋 Overview

This utility simplifies Knox Gateway deployment and configuration by:
- **Detecting Knox Installation**: Checks if Knox is installed in your Hadoop cluster
- **Automated Configuration**: Sets up Knox proxy users in Hadoop core-site configuration
- **Topology Management**: Generates and applies advanced Knox topology configurations
- **Ambari Integration**: Seamlessly integrates with Ambari for cluster management
- **Template-based Setup**: Uses Jinja2 templates for flexible topology configuration

## 🚀 Features

### Current Features
- ✅ Knox installation detection via Ambari API
- ✅ Automatic proxy user configuration (`proxyuser.knox.*` properties)
- ✅ Advanced topology template rendering with service discovery
- ✅ SSL/TLS support with configurable security
- ✅ Multi-service topology support (HDFS, YARN, Ranger, Solr, etc.)
- ✅ Configuration synchronization with Ambari properties
- ✅ Makefile automation for easy deployment

### Supported Services in Topology
- **Core Hadoop**: HDFS, YARN, WebHDFS, WebHCat
- **Processing**: Hive, Oozie, HBase
- **Analytics**: Druid (Coordinator, Overlord, Router, Broker)
- **Notebooks**: Zeppelin
- **Management**: Ambari UI/WebSocket, Ranger, Solr

## 📁 Project Structure

```
knox-utility/
├── knox_utils/
│   ├── cluster.py          # Knox detection & configuration logic
│   ├── configs.py          # Ambari API configuration management
│   ├── params.py           # Configuration parameters
│   └── update_config.py    # Auto-sync with Ambari properties
├── templates/
│   └── advaned_topology_template.j2  # Knox topology Jinja2 template
├── config.ini              # Ambari connection configuration
├── main.py                 # CLI entry point
├── Makefile               # Build and deployment automation
└── requirements.txt       # Python dependencies
```

## 🔧 Installation & Setup

### Prerequisites
- Python 3.6+
- Access to Ambari server
- Knox Gateway installed in your Hadoop cluster

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd knox-utility

# Install and check Knox status
make install

# Configure Knox (sets proxy users and topology)
make configure-knox

# For remote Ambari servers
make install-remote
```

### Manual Installation
```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Check Knox installation
python main.py --check-knox

# Configure Knox
python main.py --configure-knox
```

## ⚙️ Configuration

### config.ini
Update the Ambari connection details:
```ini
[ambari]
username = admin
password = admin
cluster_name = your_cluster_name
protocol = https
port = 8446
host = your.ambari.host
```

### Command Line Options
```bash
python main.py [OPTIONS]

Options:
  --check-knox          Check if Knox is installed
  --configure-knox      Configure Knox proxy users and topology
  --local {true,false}  Update config.ini from Ambari properties (default: true)
```

## 🛠️ What This Utility Does

### 1. Knox Detection
- Queries Ambari API to verify Knox service installation
- Handles SSL/TLS configurations automatically
- Provides clear status reporting

### 2. Proxy User Configuration
- Automatically configures `hadoop.proxyuser.knox.groups=*`
- Sets `hadoop.proxyuser.knox.hosts=*` in core-site
- Uses Ambari API for seamless configuration updates

### 3. Topology Generation
- Discovers cluster services automatically
- Generates comprehensive Knox topology XML
- Supports conditional service inclusion (Ranger, Solr, HA configurations)
- Applies topology to Knox configuration

### 4. Service Discovery
The utility automatically detects and configures:
- **HDFS**: NameNode addresses, HA configuration
- **YARN**: ResourceManager endpoints
- **Ranger**: Admin and UI endpoints (if installed)
- **Solr**: Search service endpoints (if installed)
- **Ambari**: UI and WebSocket endpoints

## 🔮 Future Improvements & Suggestions

### 🎯 High Priority Enhancements

#### 1. **Enhanced Security & SSO**
```python
# Suggested additions to main.py
parser.add_argument('--setup-sso', action='store_true', help='Configure Knox SSO')
parser.add_argument('--setup-ldap', action='store_true', help='Configure LDAP authentication')
parser.add_argument('--disable-sso', action='store_true', help='Disable Knox SSO')
```

#### 2. **Service Health Monitoring**
- Add health checks for Knox Gateway service
- Monitor topology deployment status
- Validate service connectivity through Knox

#### 3. **Advanced Configuration Management**
- Support for multiple topology templates
- Environment-specific configurations (dev/staging/prod)
- Configuration backup and rollback capabilities

#### 4. **Enhanced CLI Experience**
```bash
# Suggested new commands
knox-util status          # Comprehensive status dashboard
knox-util validate        # Validate configuration and connectivity
knox-util backup          # Backup current configurations
knox-util restore         # Restore from backup
knox-util logs            # View Knox and related service logs
```

### 🔧 Technical Improvements

#### 1. **Error Handling & Resilience**
- Implement retry mechanisms for API calls
- Add comprehensive error logging
- Graceful handling of partial failures

#### 2. **Testing & Quality Assurance**
```python
# Add test structure
tests/
├── unit/
│   ├── test_cluster.py
│   ├── test_configs.py
│   └── test_params.py
├── integration/
│   └── test_ambari_integration.py
└── fixtures/
    └── sample_responses.json
```

#### 3. **Configuration Validation**
- Schema validation for config.ini
- Pre-flight checks before configuration changes
- Compatibility checks between Knox and Hadoop versions

#### 4. **Performance Optimizations**
- Parallel API calls for service discovery
- Caching of cluster information
- Asynchronous operations for large clusters

### 🚀 Feature Additions

#### 1. **Multi-Cluster Support**
```ini
# Enhanced config.ini
[cluster_prod]
username = admin
password = admin
cluster_name = prod_cluster
host = prod.ambari.host

[cluster_dev]
username = admin
password = admin
cluster_name = dev_cluster
host = dev.ambari.host
```

#### 2. **Knox Policy Management**
- Automated whitelist management using hostname suffixes
- Role-based access control configuration
- Policy templates for different user groups

#### 3. **Integration Enhancements**
- Ranger plugin management (AclsAuthz vs XASecurePDPKnox)
- Automated certificate management
- Integration with external identity providers

#### 4. **Monitoring & Alerting**
- Knox Gateway metrics collection
- Performance monitoring dashboard
- Automated alerts for configuration drift

### 📊 Operational Improvements

#### 1. **Documentation & Usability**
- Interactive configuration wizard
- Troubleshooting guides
- Best practices documentation

#### 2. **Deployment Automation**
- Docker containerization
- Ansible playbooks
- CI/CD pipeline integration

#### 3. **Audit & Compliance**
- Configuration change tracking
- Audit log generation
- Compliance reporting

## 🐛 Current TODOs (From Original)
- [ ] Demo LDAP service management
- [ ] Ranger plugin management (AclsAuthz vs XASecurePDPKnox)
- [ ] Hostname suffix whitelist configuration
- [ ] SSO setup and configuration
- [ ] Knox SSO topology enhancements:
  - [ ] `knoxsso.token.ttl:3600000`
  - [ ] `knoxsso.cookie.samesite:Lax`
  - [ ] `knoxsso.cookie.secure.only:false`
- [ ] UI sanity checks
- [ ] HDFS and Ranger-infra audit checks
- [ ] SSO disablement functionality

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review existing issues
3. Create a new issue with detailed information

---

**Note**: This utility is designed for Hadoop clusters managed by Apache Ambari. Ensure you have proper access credentials and backup your configurations before making changes.