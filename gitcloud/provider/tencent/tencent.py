#!/usr/bin/env python3
"""
Tencent Cloud Unified Provisioning Script
------------------------------------------
Unified entry point for provisioning Tencent Cloud resources (CVM + MySQL).

Features:
- Accept resource specification via JSON or command-line arguments
- Support default configurations (minimal setup)
- Provision CVM instance and MySQL database together
- Share VPC and security groups between resources
- Return structured information about created resources

Requirements:
- tencentcloud-sdk-python
- tencentcloud-sdk-python-cdb
- Tencent Cloud API credentials

Usage:
    # Using JSON specification
    python tencent.py --spec resources.json

    # Using command-line arguments
    python tencent.py --cvm-cpu 4 --cvm-memory 8 --db-cpu 2 --db-memory 4000

    # Using defaults (2-core CVM + 2-core MySQL)
    python tencent.py
"""

import os
import sys
import json
import time
import argparse
import subprocess
import re
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any

# Import local modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from credentials import get_tencent_credentials, generate_ssh_keypair
from network import create_vpc_and_subnets, create_security_group_for_all, create_security_group_for_mysql

# Try to import Tencent Cloud SDK
try:
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
    from tencentcloud.cvm.v20170312 import cvm_client, models as cvm_models
    from tencentcloud.cdb.v20170320 import cdb_client, models as cdb_models
    from tencentcloud.vpc.v20170312 import vpc_client, models as vpc_models
except ImportError:
    print("❌ Error: Tencent Cloud SDK not found.")
    print("Please install it with:")
    print("pip install tencentcloud-sdk-python tencentcloud-sdk-python-cdb")
    sys.exit(1)


@dataclass
class CVMSpec:
    """CVM instance specification"""
    cpu_cores: int = 2
    memory_gb: int = 4
    disk_gb: int = 50
    gpu_type: Optional[str] = None  # T4, V100, A10, A100, or None


@dataclass
class MySQLSpec:
    """MySQL instance specification"""
    cpu_cores: int = 2
    memory_mb: int = 4000
    storage_gb: int = 100
    version: str = "8.0"


@dataclass
class ResourceSpec:
    """Complete resource specification"""
    cvm: Optional[CVMSpec] = None
    mysql: Optional[MySQLSpec] = None
    region: str = "ap-guangzhou"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResourceSpec':
        """Create ResourceSpec from dictionary"""
        cvm_data = data.get('cvm')
        mysql_data = data.get('mysql')

        cvm = CVMSpec(**cvm_data) if cvm_data else None
        mysql = MySQLSpec(**mysql_data) if mysql_data else None

        return cls(
            cvm=cvm,
            mysql=mysql,
            region=data.get('region', 'ap-guangzhou')
        )

    @classmethod
    def from_file(cls, filepath: str) -> 'ResourceSpec':
        """Load ResourceSpec from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def default(cls) -> 'ResourceSpec':
        """Return default resource specification"""
        return cls(
            cvm=CVMSpec(cpu_cores=2, memory_gb=4, disk_gb=50),
            region="ap-guangzhou"
        )


@dataclass
class ProvisionedResources:
    """Information about provisioned resources"""
    cvm_instance_id: Optional[str] = None
    cvm_public_ip: Optional[str] = None
    cvm_private_ip: Optional[str] = None
    ssh_private_key_path: Optional[str] = None

    mysql_instance_id: Optional[str] = None
    mysql_host: Optional[str] = None
    mysql_port: Optional[int] = None
    mysql_username: Optional[str] = None
    mysql_password: Optional[str] = None

    vpc_id: Optional[str] = None
    subnets: Optional[Dict[str, str]] = None
    security_group_ids: Optional[list] = None
    region: str = "ap-guangzhou"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    def save(self, filepath: str):
        """Save to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        print(f"💾 Provisioned resources info saved to: {filepath}")


class TencentProvisioner:
    """Tencent Cloud resource provisioner"""

    def __init__(self, spec: ResourceSpec, session_dir=None):
        self.spec = spec
        self.provisioned = ProvisionedResources(region=spec.region)

        # Use provided session directory or create a new one
        if session_dir:
            self.session_dir = Path(session_dir)
            self.session_name = self.session_dir.name
            print("\n" + "="*70)
            print(f"📁 Using Session Directory: {self.session_dir}")
            print(f"   Session ID: {self.session_name}")
            print("="*70 + "\n")
        else:
            # Create session directory at the start
            session_base = Path.home() / ".gitcloud" / "session"
            session_base.mkdir(parents=True, exist_ok=True)

            # Create timestamped session subdirectory
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            self.session_dir = session_base / f"session_{timestamp}"
            self.session_dir.mkdir(parents=True, exist_ok=True)
            self.session_name = f"session_{timestamp}"

            # Print session info immediately
            print("\n" + "="*70)
            print(f"📁 Session Directory Created: {self.session_dir}")
            print(f"   Session ID: {self.session_name}")
            print("   All files for this session will be stored here.")
            print("="*70 + "\n")

        # Get credentials
        secret_id, secret_key = get_tencent_credentials()
        self.cred = credential.Credential(secret_id, secret_key)

        # Initialize clients
        self._init_clients()

    def _init_clients(self):
        """Initialize Tencent Cloud API clients"""
        # CVM client
        http_profile_cvm = HttpProfile()
        http_profile_cvm.endpoint = "cvm.tencentcloudapi.com"
        client_profile_cvm = ClientProfile()
        client_profile_cvm.httpProfile = http_profile_cvm
        self.cvm_client = cvm_client.CvmClient(self.cred, self.spec.region, client_profile_cvm)

        # CDB (MySQL) client
        http_profile_cdb = HttpProfile()
        http_profile_cdb.endpoint = "cdb.tencentcloudapi.com"
        client_profile_cdb = ClientProfile()
        client_profile_cdb.httpProfile = http_profile_cdb
        self.cdb_client = cdb_client.CdbClient(self.cred, self.spec.region, client_profile_cdb)

        # VPC client
        http_profile_vpc = HttpProfile()
        http_profile_vpc.endpoint = "vpc.tencentcloudapi.com"
        client_profile_vpc = ClientProfile()
        client_profile_vpc.httpProfile = http_profile_vpc
        self.vpc_client = vpc_client.VpcClient(self.cred, self.spec.region, client_profile_vpc)

    def _save_session_info(self, stage, info):
        """Save session information at each stage"""
        info_file = self.session_dir / f"{stage}_info.txt"
        with open(info_file, 'w') as f:
            f.write(f"Stage: {stage}\n")
            f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n")
            f.write(info)
            f.write("\n")
        print(f"   💾 Session info saved: {info_file.name}")

    def provision(self) -> ProvisionedResources:
        """Provision all specified resources"""
        print("\n🚀 Starting Tencent Cloud Resource Provisioning")
        print("="*70)

        try:
            # Save initial specification
            spec_info = f"""Resource Specification:
Region: {self.spec.region}

CVM:
{f"  CPU: {self.spec.cvm.cpu_cores} cores" if self.spec.cvm else "  Not provisioned"}
{f"  Memory: {self.spec.cvm.memory_gb} GB" if self.spec.cvm else ""}
{f"  Disk: {self.spec.cvm.disk_gb} GB" if self.spec.cvm else ""}
{f"  GPU: {self.spec.cvm.gpu_type or 'None'}" if self.spec.cvm else ""}

MySQL:
{f"  CPU: {self.spec.mysql.cpu_cores} cores" if self.spec.mysql else "  Not provisioned"}
{f"  Memory: {self.spec.mysql.memory_mb} MB" if self.spec.mysql else ""}
{f"  Storage: {self.spec.mysql.storage_gb} GB" if self.spec.mysql else ""}
"""
            self._save_session_info("00_specification", spec_info)

            # Step 1: Create network resources (VPC, subnets)
            self._create_network()

            # Step 2: Provision CVM if specified
            if self.spec.cvm:
                self._provision_cvm()

            # Step 3: Provision MySQL if specified
            if self.spec.mysql:
                self._provision_mysql()

            print("\n" + "="*70)
            print("✅ All resources provisioned successfully!")
            print("="*70)

            return self.provisioned

        except Exception as e:
            print(f"\n❌ Provisioning failed: {e}")
            error_info = f"Error: {str(e)}\n"
            self._save_session_info("99_error", error_info)
            print("\n🧹 Cleaning up resources...")
            self.cleanup()
            raise

    def _create_network(self):
        """Create VPC and subnets"""
        print("\n🌐 Creating network resources...")

        # Create VPC and subnets
        vpc_id, subnets = create_vpc_and_subnets(self.vpc_client, self.spec.region)
        self.provisioned.vpc_id = vpc_id
        self.provisioned.subnets = subnets
        self.provisioned.security_group_ids = []

        print(f"✅ VPC created: {vpc_id}")
        print(f"✅ Subnets created: {len(subnets)} zones")

        # Save network info
        network_info = f"""VPC ID: {vpc_id}
Subnets:
"""
        for zone, subnet_id in subnets.items():
            network_info += f"  {zone}: {subnet_id}\n"
        self._save_session_info("01_network", network_info)

    def _provision_cvm(self):
        """Provision CVM instance"""
        print("\n💻 Provisioning CVM instance (this may take 2-3 minutes)...")

        cvm_spec = self.spec.cvm

        # Get instance type
        instance_type, gpu_enabled = self._get_instance_type(
            cvm_spec.cpu_cores,
            cvm_spec.memory_gb,
            cvm_spec.gpu_type
        )

        print(f"   Instance type: {instance_type}")
        print(f"   CPU: {cvm_spec.cpu_cores} cores")
        print(f"   Memory: {cvm_spec.memory_gb} GB")
        print(f"   Disk: {cvm_spec.disk_gb} GB")
        print(f"   GPU: {cvm_spec.gpu_type if cvm_spec.gpu_type else 'None'}")

        # Generate SSH keypair in session directory
        print("   Generating SSH keypair...")
        private_key_path, public_key = generate_ssh_keypair(self.session_dir)
        self.provisioned.ssh_private_key_path = private_key_path
        print(f"   SSH key saved to: {private_key_path}")

        # Create security group for CVM
        print("   Creating security group...")
        sg_id = create_security_group_for_all(self.cred, self.spec.region)
        self.provisioned.security_group_ids.append(sg_id)

        # Create CVM instance
        instance_id = self._create_cvm_instance(
            instance_type, public_key, sg_id, gpu_enabled, cvm_spec.disk_gb
        )
        self.provisioned.cvm_instance_id = instance_id

        # Wait for instance to be running
        public_ip, private_ip = self._wait_for_cvm_running(instance_id)
        self.provisioned.cvm_public_ip = public_ip
        self.provisioned.cvm_private_ip = private_ip

        # Save CVM info
        cvm_info = f"""Instance ID: {instance_id}
Public IP: {public_ip}
Private IP: {private_ip}
SSH Key: {private_key_path}
SSH Command: ssh -i {private_key_path} ubuntu@{public_ip}
Security Group: {sg_id}
"""
        self._save_session_info("02_cvm", cvm_info)

        # Setup Docker and model
        success = self.setup_docker(public_ip, private_key_path, gpu_enabled)

        if success:
            # Show usage instructions
            print("setup docker env success")

    def _provision_mysql(self):
        """Provision MySQL database"""
        print("\n🗄️  Provisioning MySQL database (this may take 3-4 minutes)...")

        mysql_spec = self.spec.mysql

        print(f"   CPU: {mysql_spec.cpu_cores} cores")
        print(f"   Memory: {mysql_spec.memory_mb} MB")
        print(f"   Storage: {mysql_spec.storage_gb} GB")
        print(f"   Version: MySQL {mysql_spec.version}")

        # Create security group for MySQL
        print("   Creating security group for MySQL...")
        sg_id = create_security_group_for_mysql(self.cred, self.spec.region)
        self.provisioned.security_group_ids.append(sg_id)

        # Create MySQL instance (returns instance_id and root password)
        instance_id, root_password = self._create_mysql_instance(mysql_spec, sg_id)
        self.provisioned.mysql_instance_id = instance_id

        # Wait for instance to be ready
        instance = self._wait_for_mysql_ready(instance_id)
        self.provisioned.mysql_host = instance.Vip
        self.provisioned.mysql_port = instance.Vport

        # Use root account directly instead of creating a new account
        self.provisioned.mysql_username = "root"
        self.provisioned.mysql_password = root_password

        print(f"✅ MySQL instance provisioned: {instance_id}")
        print(f"   Host: {instance.Vip}:{instance.Vport}")
        print(f"   Username: root")
        print(f"   Password: {root_password}")

        # Save MySQL info
        mysql_info = f"""Instance ID: {instance_id}
Host: {instance.Vip}
Port: {instance.Vport}
Username: root
Password: {root_password}
Connection: mysql -h {instance.Vip} -P {instance.Vport} -u root -p
Security Group: {sg_id}
"""
        self._save_session_info("03_mysql", mysql_info)

    def _get_instance_type(self, cpu_cores, memory_gb, gpu_type=None):
        """Map CPU/memory/GPU to Tencent Cloud instance type"""
        if gpu_type and gpu_type.upper() != 'NONE':
            gpu_map = {
                'T4': 'GN7.2XLARGE32',
                'V100': 'GN8.4XLARGE64',
                'A10': 'GN7.5XLARGE80',
                'A100': 'GN7.20XLARGE320',
            }
            instance_type = gpu_map.get(gpu_type.upper(), 'GN7.2XLARGE32')
            return instance_type, True

        # CPU-only instances
        if cpu_cores <= 2 and memory_gb <= 4:
            return 'S5.MEDIUM4', False
        elif cpu_cores <= 2 and memory_gb <= 8:
            return 'S5.LARGE8', False
        elif cpu_cores <= 4 and memory_gb <= 16:
            return 'S5.2XLARGE16', False
        elif cpu_cores <= 8 and memory_gb <= 32:
            return 'S5.4XLARGE32', False
        elif cpu_cores <= 16 and memory_gb <= 64:
            return 'S5.8XLARGE64', False
        else:
            return 'S5.16XLARGE128', False

    def _create_cvm_instance(self, instance_type, ssh_public_key, sg_id, gpu_enabled, disk_gb):
        """Create CVM instance"""
        # Get available zones
        zones = self._get_available_zones()

        # # Choose image
        # if gpu_enabled:
        #     image_id = "img-eb30mz89"  # Ubuntu 20.04 + CUDA
        # else:
        #     image_id = "img-487zeit5"  # Ubuntu 22.04
        image_id = "img-487zeit5"  # Ubuntu 22.04

        # Try to create in each zone
        for zone in zones:
            try:
                req = cvm_models.RunInstancesRequest()
                import base64
                # 如果是gpu的机器，初始化安装gpu驱动
                if gpu_enabled:
                    params = {
                    "InstanceChargeType": "POSTPAID_BY_HOUR",
                    "Placement": {
                        "Zone": zone
                    },
                    "InstanceType": instance_type,
                    "ImageId": image_id,
                    "SystemDisk": {
                        "DiskType": "CLOUD_PREMIUM",
                        "DiskSize": disk_gb
                    },
                    "InternetAccessible": {
                        "InternetChargeType": "TRAFFIC_POSTPAID_BY_HOUR",
                        "InternetMaxBandwidthOut": 100,
                        "PublicIpAssigned": True
                    },
                    "VirtualPrivateCloud": {
                        "VpcId": self.provisioned.vpc_id,
                        "SubnetId": self.provisioned.subnets.get(zone)
                    },
                    "InstanceName": f"gitcloud-llm-{int(time.time())}",
                    "UserData": subprocess.check_output([
                        "base64", "-i", "-"
                    ], input=f"""#!/bin/bash
# Setup SSH key
mkdir -p /home/ubuntu/.ssh
echo '{ssh_public_key}' >> /home/ubuntu/.ssh/authorized_keys
chmod 700 /home/ubuntu/.ssh
chmod 600 /home/ubuntu/.ssh/authorized_keys
chown -R ubuntu:ubuntu /home/ubuntu/.ssh
echo 'ubuntu ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/ubuntu
chmod 440 /etc/sudoers.d/ubuntu

# Install GPU driver automatically using Tencent Cloud's official script
# Reference: https://cloud.tencent.com/document/product/560/112129

# Clean up any previous installation files
sudo rm -f /tmp/user_define_install_info.ini
sudo rm -f /tmp/auto_install.sh
sudo rm -f /tmp/auto_install.log

# Create configuration file with driver versions (exactly as per official docs)
sudo bash -c 'cat > /tmp/user_define_install_info.ini << EOF
DRIVER_VERSION=535.161.07
CUDA_VERSION=12.4.0
CUDNN_VERSION=8.9.7
DRIVER_URL=
CUDA_URL=
CUDNN_URL=
EOF'

# Download and run the auto-install script (run synchronously with timeout in background)
sudo wget https://mirrors.tencentyun.com/install/GPU/auto_install.sh -O /tmp/auto_install.sh
sudo chmod +x /tmp/auto_install.sh
sudo /tmp/auto_install.sh > /tmp/auto_install.log 2>&1 &
""".encode()).decode().strip(),
                    "SecurityGroupIds": [sg_id],
                    "InstanceCount": 1
                }
                else:
                    params = {
                    "InstanceChargeType": "POSTPAID_BY_HOUR",
                    "Placement": {"Zone": zone},
                    "InstanceType": instance_type,
                    "ImageId": image_id,
                    "SystemDisk": {
                        "DiskType": "CLOUD_PREMIUM",
                        "DiskSize": disk_gb
                    },
                    "InternetAccessible": {
                        "InternetChargeType": "TRAFFIC_POSTPAID_BY_HOUR",
                        "InternetMaxBandwidthOut": 100,
                        "PublicIpAssigned": True
                    },
                    "VirtualPrivateCloud": {
                        "VpcId": self.provisioned.vpc_id,
                        "SubnetId": self.provisioned.subnets.get(zone)
                    },
                    "InstanceName": f"gitcloud-{int(time.time())}",
                    "UserData": base64.b64encode(f"""#!/bin/bash
mkdir -p /home/ubuntu/.ssh
echo '{ssh_public_key}' >> /home/ubuntu/.ssh/authorized_keys
chmod 700 /home/ubuntu/.ssh
chmod 600 /home/ubuntu/.ssh/authorized_keys
chown -R ubuntu:ubuntu /home/ubuntu/.ssh
echo 'ubuntu ALL=(ALL) NOPASSWD:ALL' > /etc/sudoers.d/ubuntu
chmod 440 /etc/sudoers.d/ubuntu
""".encode()).decode(),
                    "SecurityGroupIds": [sg_id],
                    "InstanceCount": 1
                }
                            
                req.from_json_string(json.dumps(params))
                resp = self.cvm_client.RunInstances(req)
                instance_id = resp.InstanceIdSet[0]

                print(f"✅ Instance created in zone {zone}: {instance_id}")
                return instance_id

            except TencentCloudSDKException as e:
                if 'ResourceInsufficient' in str(e) or 'InvalidZone' in str(e):
                    print(f"   ⚠️  Zone {zone} unavailable, trying next...")
                    continue
                raise

        raise Exception("Failed to create CVM instance in all zones")
    

    def exec_claude(self, base_image, repo_url, model_provider='deepseek', api_key=None):
        """
        Execute Claude CLI inside a Docker container on the remote server.
        Automatically passes cloud service information (MySQL, etc.) to Claude.

        Args:
            base_image: Docker image to use (e.g., hegaoyuan/python:latest)
            repo_url: GitHub repository URL to clone and setup
            model_provider: AI model provider ('deepseek' or 'anthropic')
            api_key: API key for the model provider
        """
        public_ip = self.provisioned.cvm_public_ip
        private_key_path = self.provisioned.ssh_private_key_path

        # Use provided API key or prompt
        anthropic_api_key = api_key
        if not anthropic_api_key:
            print("⚠️ Warning: API key not provided")
            anthropic_api_key = safe_input(f"Enter your API key for {model_provider}: ")

        # Build cloud services information section
        cloud_services_info = []

        # Add MySQL information if available
        if self.provisioned.mysql_instance_id:
            mysql_info = f"""
MySQL Database:
- Host: {self.provisioned.mysql_host}
- Port: {self.provisioned.mysql_port}
- Username: {self.provisioned.mysql_username}
- Password: {self.provisioned.mysql_password}
- Connection String: mysql://{self.provisioned.mysql_username}:{self.provisioned.mysql_password}@{self.provisioned.mysql_host}:{self.provisioned.mysql_port}/your_database_name
- Note: You need to create the database first if the application requires a specific database name"""
            cloud_services_info.append(mysql_info)

        # Combine cloud services info
        cloud_services_section = ""
        if cloud_services_info:
            cloud_services_section = "\n\nAvailable Cloud Services:\n" + "\n".join(cloud_services_info)
            cloud_services_section += "\n\nIMPORTANT: Configure the application to use these cloud services. Update configuration files, environment variables, or connection strings as needed."

        # Claude prompt for setting up and running the project
        # Include server info and cloud services so Claude can configure them
        claude_prompt = f"""clone, setup and run {repo_url}.

Server Information:
- Public IP: {public_ip}
- SSH Key: {private_key_path}
- Working Directory: /workspace{cloud_services_section}

Setup Instructions:
1. Clone the repository
2. Install dependencies
3. Configure the application to use the provided cloud services (if applicable)
4. Set up any required environment variables or configuration files
5. Initialize database schema if needed (create database, run migrations, etc.)
6. Start the application

At the end of the setup process, provide clear instructions to the user on how to access and experience this project:
- If it is a web application: Tell the user to visit http://{public_ip}:PORT where PORT is the actual port number
- If it is a script or CLI tool: Tell the user to SSH to the server with: ssh -i {private_key_path} ubuntu@{public_ip}, then provide the exact command to run
- If it is an API: Provide example curl commands using http://{public_ip}:PORT
- Include any necessary credentials, endpoints, or usage examples

Be specific and provide ready-to-use commands or URLs."""

        # Display cloud services info if available
        if cloud_services_info:
            print("\n📋 Cloud Services Available:")
            for info in cloud_services_info:
                print(info)
            print("\n💡 Claude will configure the application to use these services")

        # Escape prompt for safe embedding in bash script (escape $ and backticks)
        safe_prompt = claude_prompt.replace('\\', '\\\\').replace('$', '\\$').replace('`', '\\`')

        # Create a Docker run script that will execute on the remote server
        if model_provider == 'deepseek':
            docker_run_script = f"""#!/bin/bash
set -e

echo "🐳 Starting Docker container with image: {base_image}"
echo "📦 Repository: {repo_url}"
echo "🤖 Model: DeepSeek"
echo "🌐 Server IP: {public_ip}"
echo ""

# Pull the latest image
docker pull {base_image}

# Claude prompt
CLAUDE_PROMPT=$(cat <<'PROMPT_EOF'
{safe_prompt}
PROMPT_EOF
)

# Run Docker container with Claude CLI
# - Use host network mode for easy port access
# - Mount workspace directory
# - Set environment variables for DeepSeek API
# - Interactive mode with pseudo-TTY
docker run --rm -it \\
  --network host \\
  -v /home/ubuntu/workspace:/workspace \\
  -w /workspace \\
  -e ANTHROPIC_BASE_URL=https://api.deepseek.com/anthropic \\
  -e ANTHROPIC_AUTH_TOKEN="{anthropic_api_key}" \\
  -e API_TIMEOUT_MS=600000 \\
  -e ANTHROPIC_MODEL=deepseek-chat \\
  -e ANTHROPIC_SMALL_FAST_MODEL=deepseek-chat \\
  -e CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 \\
  {base_image} \\
  bash -c "cd /workspace && claude \\\"$CLAUDE_PROMPT\\\""

echo ""
echo "✅ Docker container execution completed!"
"""
        else:  # anthropic
            docker_run_script = f"""#!/bin/bash
set -e

echo "🐳 Starting Docker container with image: {base_image}"
echo "📦 Repository: {repo_url}"
echo "🤖 Model: Anthropic Claude Sonnet 4.5"
echo "🌐 Server IP: {public_ip}"
echo ""

# Pull the latest image
docker pull {base_image}

# Claude prompt
CLAUDE_PROMPT=$(cat <<'PROMPT_EOF'
{safe_prompt}
PROMPT_EOF
)

# Run Docker container with Claude CLI
# - Use host network mode for easy port access
# - Mount workspace directory
# - Set environment variables for Anthropic API
# - Interactive mode with pseudo-TTY
docker run --rm -it \\
  --network host \\
  -v /home/ubuntu/workspace:/workspace \\
  -w /workspace \\
  -e ANTHROPIC_API_KEY="{anthropic_api_key}" \\
  {base_image} \\
  bash -c "cd /workspace && claude \\\"$CLAUDE_PROMPT\\\""

echo ""
echo "✅ Docker container execution completed!"
"""

        # Save Docker run script to session directory
        docker_script_path = self.session_dir / "docker_run.sh"
        with open(docker_script_path, 'w') as f:
            f.write(docker_run_script)

        # Save complete resource summary
        info_file = self.session_dir / "resources_summary.txt"

        with open(info_file, 'w') as f:
            f.write("="*70 + "\n")
            f.write("GitCloud - Provisioned Resources Information\n")
            f.write("="*70 + "\n\n")
            f.write(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Repository: {repo_url}\n\n")

            f.write("CVM Instance:\n")
            f.write(f"  - Instance ID: {self.provisioned.cvm_instance_id}\n")
            f.write(f"  - Public IP: {public_ip}\n")
            f.write(f"  - Private IP: {self.provisioned.cvm_private_ip}\n")
            f.write(f"  - SSH Key: {private_key_path}\n")
            f.write(f"  - SSH Command: ssh -i {private_key_path} ubuntu@{public_ip}\n\n")

            if self.provisioned.mysql_instance_id:
                f.write("MySQL Database:\n")
                f.write(f"  - Instance ID: {self.provisioned.mysql_instance_id}\n")
                f.write(f"  - Host: {self.provisioned.mysql_host}\n")
                f.write(f"  - Port: {self.provisioned.mysql_port}\n")
                f.write(f"  - Username: {self.provisioned.mysql_username}\n")
                f.write(f"  - Password: {self.provisioned.mysql_password}\n")
                f.write(f"  - Connection: mysql -h {self.provisioned.mysql_host} -P {self.provisioned.mysql_port} -u {self.provisioned.mysql_username} -p\n\n")

            f.write("="*70 + "\n")
            f.write("IMPORTANT: Save this information!\n")
            f.write("This file contains all credentials to access your cloud resources.\n")
            f.write("="*70 + "\n")

        # Display the important info with clear separation
        print("\n" + "="*70)
        print("📋 IMPORTANT: Resource Information Saved")
        print("="*70)
        print(f"\n✅ All resource information has been saved to:")
        print(f"   {info_file}")
        print("\n💡 You can view this information anytime by running:")
        print(f"   cat {info_file}")
        print("\n" + "="*70)
        print()

        # Ask user to confirm before starting interactive Claude
        input("Press ENTER to start Claude interactive session (this will clear the screen)...")

        # Upload Docker run script to remote server
        print("\n📤 Uploading Docker run script to remote server...")
        subprocess.run([
            "scp", "-i", private_key_path,
            "-o", "StrictHostKeyChecking=no",
            "-o", "PasswordAuthentication=no",
            str(docker_script_path), f"ubuntu@{public_ip}:/tmp/claude_docker_run.sh"
        ], check=True)

        # Execute the script on remote server with interactive terminal
        print("\n🔗 Connecting to remote server and starting Docker container...")
        print(f"   Image: {base_image}")
        print(f"   Repository: {repo_url}")
        print("")

        result = subprocess.run([
            "ssh", "-t",  # Force pseudo-terminal allocation for interactive Docker session
            "-i", private_key_path,
            "-o", "StrictHostKeyChecking=no",
            "-o", "PasswordAuthentication=no",
            f"ubuntu@{public_ip}",
            "chmod +x /tmp/claude_docker_run.sh && /tmp/claude_docker_run.sh"
        ])

        if result.returncode != 0:
            print(f"\n⚠️ Docker container execution exited with code {result.returncode}")
            raise Exception("Docker container execution failed")

        # Remind user about the saved info
        print("\n" + "="*70)
        print("✅ Claude CLI execution in Docker container complete!")
        print("="*70)
        print(f"\n📋 Resource information is saved at: {info_file}")
        print(f"💡 View it anytime: cat {info_file}")
        print()

        return True

    def setup_docker(self, public_ip, private_key_path, gpu_enabled):
        print("\n🔧 Setting up Docker environment...")
        print("⏳ Waiting for SSH to be ready (this may take 1-2 minutes)...")

        # Wait for SSH
        max_retries = 30
        for i in range(max_retries):
            try:
                result = subprocess.run(
                ["ssh", "-i", private_key_path,
                "-o", "StrictHostKeyChecking=no",
                "-o", "PasswordAuthentication=no",
                "-o", "ConnectTimeout=5",
                 f"ubuntu@{public_ip}",
                 "echo 'SSH OK'"],
                capture_output=True,
                timeout=10
            )
                if result.returncode == 0:
                    print("✅ SSH connection established")
                    break
            except:
                pass

            if i < max_retries - 1:
                time.sleep(10)
            else:
                print("❌ Failed to establish SSH connection")
                return False

        print("\n📦 Installing Docker and NVIDIA Container Toolkit...(for GPU Instance)")

        # Setup script
        setup_script_1 = """#!/bin/bash
set -e

# Wait for cloud-init to complete
echo "⏳ Waiting for cloud-init to complete..."
cloud-init status --wait || true
sleep 5

# Function to wait for package manager locks to be released
wait_for_apt() {
    local max_wait=300
    local elapsed=0

    echo "⏳ Waiting for package manager locks to be released..."

    while [ $elapsed -lt $max_wait ]; do
        # Check all common lock files
        if ! sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1 && \
           ! sudo fuser /var/lib/dpkg/lock >/dev/null 2>&1 && \
           ! sudo fuser /var/lib/apt/lists/lock >/dev/null 2>&1 && \
           ! sudo lsof /var/lib/dpkg/lock-frontend >/dev/null 2>&1; then
            echo "✅ Package manager is ready"
            return 0
        fi

        if [ $((elapsed % 30)) -eq 0 ]; then
            echo "Still waiting... ($elapsed/$max_wait seconds)"
        fi

        sleep 5
        elapsed=$((elapsed + 5))
    done

    echo "⚠️ Timeout waiting for package manager, proceeding anyway..."
    return 1
}

# Wait for apt to be available
wait_for_apt

# Kill any hanging apt processes as last resort
sudo pkill -9 apt-get || true
sudo pkill -9 dpkg || true
sudo rm -f /var/lib/dpkg/lock-frontend /var/lib/dpkg/lock /var/lib/apt/lists/lock 2>/dev/null || true
sudo dpkg --configure -a || true

# Final wait
sleep 3

# Install Docker using Aliyun mirror (for China network)
echo "📦 Installing Docker..."

# Add Aliyun Docker GPG key
curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Aliyun Docker repository
echo \
  "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://mirrors.aliyun.com/docker-ce/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update and install Docker
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker ubuntu
sudo systemctl enable docker
sudo systemctl start docker

# Configure Docker to use multiple China mirrors
sudo mkdir -p /etc/docker
sudo tee /etc/docker/daemon.json <<-'EOF'
{
  "registry-mirrors": [
    "https://docker.rainbond.cc",
    "https://docker.m.daocloud.io",
    "https://docker.nju.edu.cn",
    "https://dockerproxy.com"
  ]
}
EOF
sudo systemctl daemon-reload
sudo systemctl restart docker

# Wait for Docker to restart
sleep 3
"""
        nvidia_part = """
# Install NVIDIA Container Toolkit (using USTC mirror for China network)
echo "📦 Installing NVIDIA Container Toolkit..."

# Step 1: Add GPG key
echo "Adding NVIDIA GPG key..."
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg

# Step 2: Configure USTC mirror source (replace official source with China mirror)
echo "Configuring USTC mirror source..."
curl -s -L https://mirrors.ustc.edu.cn/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \\
  sed 's#deb https://nvidia.github.io#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://mirrors.ustc.edu.cn#g' | \\
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Step 3: Update package list and install
echo "Installing NVIDIA Container Toolkit packages..."
sudo apt-get update
sudo apt-get install -y nvidia-docker2 nvidia-container-toolkit

# Step 4: Configure Docker runtime to support NVIDIA GPU
echo "Configuring Docker runtime..."
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker

# Verify NVIDIA setup
echo "🧪 Testing NVIDIA GPU access..."
nvidia-smi
"""

        setup_script_2 = """
# Create working directory
sudo mkdir -p /home/ubuntu/workspace
sudo chown -R ubuntu:ubuntu /home/ubuntu/workspace

echo "✅ Setup complete!"
"""

        setup_script = setup_script_1
        if gpu_enabled:
            setup_script += nvidia_part
        setup_script += setup_script_2

        script_path = "/tmp/llm_setup.sh"
        with open(script_path, 'w') as f:
            f.write(setup_script)

        # Upload and run setup script
        print("📤 Uploading setup script...")
        subprocess.run([
        "scp", "-i", private_key_path,
        "-o", "StrictHostKeyChecking=no",
        "-o", "PasswordAuthentication=no",
        script_path, f"ubuntu@{public_ip}:/tmp/setup.sh"
        ], check=True)

        print("⚙️ Running setup script (this will take 5-10 minutes)...")
        result = subprocess.run([
        "ssh", "-i", private_key_path,
        "-o", "StrictHostKeyChecking=no",
        "-o", "PasswordAuthentication=no",
        f"ubuntu@{public_ip}",
        "chmod +x /tmp/setup.sh && /tmp/setup.sh"
        ])

        if result.returncode != 0:
            print("❌ Setup script failed")
            raise Exception("Setup script failed")
    
        return True


    def _create_mysql_instance(self, mysql_spec, sg_id):
        """Create MySQL instance and return instance_id and root password"""
        zones = self._get_available_zones()
        memory = self._get_mysql_memory(mysql_spec.cpu_cores, mysql_spec.memory_mb)

        # Generate root password
        # Password must contain at least 2 types: letters, numbers, special chars (8-64 chars)
        import secrets
        import string
        alphabet = string.ascii_letters + string.digits + '@#$%'
        root_password = "GitCloud@" + ''.join(secrets.choice(alphabet) for _ in range(15))

        print(f"   🔐 Generated root password: {root_password}")

        for zone in zones:
            if zone not in self.provisioned.subnets:
                continue

            try:
                req = cdb_models.CreateDBInstanceHourRequest()
                params = {
                    "Memory": memory,
                    "Volume": mysql_spec.storage_gb,
                    "GoodsNum": 1,
                    "Zone": zone,
                    "UniqVpcId": self.provisioned.vpc_id,
                    "UniqSubnetId": self.provisioned.subnets[zone],
                    "ProjectId": 0,
                    "InstanceRole": "master",
                    "EngineVersion": mysql_spec.version,
                    "InstanceName": "gitcloud-mysql",
                    "SecurityGroup": [sg_id],
                    "ProtectMode": 0,
                    "DeployMode": 0,
                    "MasterRegion": self.spec.region,
                    "Port": 3306,
                    "Password": root_password
                }
                req.from_json_string(json.dumps(params))

                resp = self.cdb_client.CreateDBInstanceHour(req)
                instance_id = resp.InstanceIds[0]

                print(f"✅ MySQL instance created in zone {zone}: {instance_id}")
                return instance_id, root_password

            except TencentCloudSDKException as e:
                if 'TradeError' in str(e) or '售罄' in str(e):
                    print(f"   ⚠️  Zone {zone} unavailable, trying next...")
                    continue
                raise

        raise Exception("Failed to create MySQL instance in all zones")

    def _get_mysql_memory(self, cpu_cores, memory_mb):
        """Map CPU/memory to MySQL instance memory spec"""
        if cpu_cores == 1 and memory_mb <= 1000:
            return 1000
        elif cpu_cores == 1 and memory_mb <= 2000:
            return 2000
        elif cpu_cores == 2 and memory_mb <= 4000:
            return 4000
        elif cpu_cores == 4 and memory_mb <= 8000:
            return 8000
        elif cpu_cores >= 8:
            return 16000
        else:
            return 4000

    def _get_available_zones(self):
        """Get available zones for the region"""
        try:
            req = cvm_models.DescribeZonesRequest()
            resp = self.cvm_client.DescribeZones(req)
            return [zone.Zone for zone in resp.ZoneSet if zone.ZoneState == "AVAILABLE"]
        except:
            # Fallback to common zones
            return [f"{self.spec.region}-{i}" for i in range(1, 7)]

    def _wait_for_cvm_running(self, instance_id, max_wait=300):
        """Wait for CVM instance to be running"""
        print("   Waiting for instance to be running...")

        start_time = time.time()
        while time.time() - start_time < max_wait:
            req = cvm_models.DescribeInstancesRequest()
            params = {"InstanceIds": [instance_id]}
            req.from_json_string(json.dumps(params))

            resp = self.cvm_client.DescribeInstances(req)
            if resp.InstanceSet:
                instance = resp.InstanceSet[0]
                if instance.InstanceState == "RUNNING":
                    public_ip = instance.PublicIpAddresses[0] if instance.PublicIpAddresses else None
                    private_ip = instance.PrivateIpAddresses[0] if instance.PrivateIpAddresses else None
                    return public_ip, private_ip

            time.sleep(10)

        raise TimeoutError("Instance did not become running in time")

    def _wait_for_mysql_ready(self, instance_id, max_wait=600):
        """Wait for MySQL instance to be ready"""
        print("   Waiting for MySQL instance to be ready...")

        start_time = time.time()
        while time.time() - start_time < max_wait:
            req = cdb_models.DescribeDBInstancesRequest()
            params = {"InstanceIds": [instance_id]}
            req.from_json_string(json.dumps(params))

            resp = self.cdb_client.DescribeDBInstances(req)
            if resp.TotalCount > 0:
                instance = resp.Items[0]
                if instance.Status == 1:  # 1 = running
                    return instance

            time.sleep(10)

        raise TimeoutError("MySQL instance did not become ready in time")

    def cleanup(self):
        """Cleanup all provisioned resources"""
        print("\n🧹 Cleaning up resources...")

        try:
            # Terminate CVM instance
            if self.provisioned.cvm_instance_id:
                print(f"   Terminating CVM: {self.provisioned.cvm_instance_id}")
                req = cvm_models.TerminateInstancesRequest()
                params = {"InstanceIds": [self.provisioned.cvm_instance_id]}
                req.from_json_string(json.dumps(params))
                self.cvm_client.TerminateInstances(req)

            # Isolate MySQL instance
            if self.provisioned.mysql_instance_id:
                print(f"   Isolating MySQL: {self.provisioned.mysql_instance_id}")
                req = cdb_models.IsolateDBInstanceRequest()
                params = {"InstanceId": self.provisioned.mysql_instance_id}
                req.from_json_string(json.dumps(params))
                self.cdb_client.IsolateDBInstance(req)

            # Delete security groups
            if self.provisioned.security_group_ids:
                for sg_id in self.provisioned.security_group_ids:
                    try:
                        print(f"   Deleting security group: {sg_id}")
                        req = vpc_models.DeleteSecurityGroupRequest()
                        params = {"SecurityGroupId": sg_id}
                        req.from_json_string(json.dumps(params))
                        self.vpc_client.DeleteSecurityGroup(req)
                    except:
                        pass

            # Delete subnets
            if self.provisioned.subnets:
                for zone, subnet_id in self.provisioned.subnets.items():
                    try:
                        print(f"   Deleting subnet: {subnet_id}")
                        req = vpc_models.DeleteSubnetRequest()
                        params = {"SubnetId": subnet_id}
                        req.from_json_string(json.dumps(params))
                        self.vpc_client.DeleteSubnet(req)
                    except:
                        pass

            # Delete VPC
            if self.provisioned.vpc_id:
                try:
                    print(f"   Deleting VPC: {self.provisioned.vpc_id}")
                    req = vpc_models.DeleteVpcRequest()
                    params = {"VpcId": self.provisioned.vpc_id}
                    req.from_json_string(json.dumps(params))
                    self.vpc_client.DeleteVpc(req)
                except:
                    pass

            print("✅ Cleanup completed")

        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}")

def safe_input(prompt):
    """
    Safe input function that filters out ANSI escape sequences from arrow keys and other special keys.
    Supports paste operations (Ctrl+V).
    """
    try:
        # Try to use readline for better input handling
        import readline
    except ImportError:
        pass

    user_input = input(prompt)
    # Remove ANSI escape sequences (e.g., ^[[A, ^[[B, ^[[C, ^[[D)
    cleaned = re.sub(r'\x1b\[[0-9;]*[A-Za-z]', '', user_input)
    # Remove other control characters except newline and tab
    cleaned = re.sub(r'[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]', '', cleaned)
    return cleaned.strip()

def main():
    parser = argparse.ArgumentParser(
        description="Unified Tencent Cloud Resource Provisioning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default configuration (2-core CVM)
  python tencent.py

  # Specify custom configuration via command line
  python tencent.py --cvm-cpu 4 --cvm-memory 8 --db-cpu 2 --db-memory 4000

  # Use JSON specification file
  python tencent.py --spec resources.json

  # Use analyzer output (provider spec format)
  python tencent.py --analyzer-spec analyzer_output.json

  # Only provision CVM (no database)
  python tencent.py --cvm-cpu 4 --cvm-memory 8 --no-db

  # Only provision MySQL (no CVM)
  python tencent.py --db-cpu 2 --db-memory 4000 --no-cvm
        """
    )

    parser.add_argument('--spec', type=str,
                       help='JSON file with resource specification')
    parser.add_argument('--analyzer-spec', type=str,
                       help='JSON file with analyzer provider specification (from analyzer.py --provider-spec)')
    parser.add_argument('--region', type=str, default='ap-guangzhou',
                       help='Tencent Cloud region (default: ap-guangzhou)')

    # CVM arguments
    parser.add_argument('--cvm-cpu', type=int,
                       help='CVM CPU cores')
    parser.add_argument('--cvm-memory', type=int,
                       help='CVM memory in GB')
    parser.add_argument('--cvm-disk', type=int,
                       help='CVM disk size in GB')
    parser.add_argument('--cvm-gpu', type=str,
                       choices=['T4', 'V100', 'A10', 'A100'],
                       help='CVM GPU type')
    parser.add_argument('--no-cvm', action='store_true',
                       help='Do not provision CVM')

    # MySQL arguments
    parser.add_argument('--db-cpu', type=int,
                       help='MySQL CPU cores')
    parser.add_argument('--db-memory', type=int,
                       help='MySQL memory in MB')
    parser.add_argument('--db-storage', type=int,
                       help='MySQL storage in GB')
    parser.add_argument('--db-version', type=str,
                       choices=['5.6', '5.7', '8.0'],
                       help='MySQL version')
    parser.add_argument('--no-db', action='store_true',
                       help='Do not provision MySQL')    
    parser.add_argument('--base_image', type=str,
                        help="Base Docker Image")
    parser.add_argument('--repo', '--repo-url', dest='repo_url', type=str,
                       help='GitHub repository URL to clone and setup')
    parser.add_argument('--model', type=str, default='deepseek',
                       choices=['deepseek', 'anthropic'],
                       help='AI model provider (default: deepseek)')
    parser.add_argument('--api-key', type=str,
                       help='API key for the AI model provider')

    parser.add_argument('--output', type=str,
                       help='Output file for provisioned resources info')
    parser.add_argument('--cleanup', action='store_true',
                       help='Cleanup resources after creation (for testing)')
    parser.add_argument('--session-dir', type=str,
                       help='Existing session directory to use (created by main.py)')

    args = parser.parse_args()

    print("🚀 Tencent Cloud Unified Provisioning Script")
    print("="*70)

    # Build resource specification
    if args.analyzer_spec:
        # Load from analyzer output (provider spec format)
        print(f"\n📄 Loading analyzer specification from: {args.analyzer_spec}")
        spec = ResourceSpec.from_file(args.analyzer_spec)
    elif args.spec:
        # Load from JSON file
        print(f"\n📄 Loading specification from: {args.spec}")
        spec = ResourceSpec.from_file(args.spec)
    else:
        # Build from command-line arguments or use defaults
        cvm = None
        mysql = None

        if not args.no_cvm:
            cvm = CVMSpec(
                cpu_cores=args.cvm_cpu or 2,
                memory_gb=args.cvm_memory or 4,
                disk_gb=args.cvm_disk or 50,
                gpu_type=args.cvm_gpu
            )
        # If both are None, use defaults
        if cvm is None and mysql is None:
            spec = ResourceSpec.default()
        else:
            spec = ResourceSpec(cvm=cvm, mysql=mysql, region=args.region)

    # Display configuration
    print("\n📊 Resource Configuration:")
    print(f"   Region: {spec.region}")

    if spec.cvm:
        print(f"\n   CVM Instance:")
        if spec.cvm.gpu_type:
            print(f"     Disk: {spec.cvm.disk_gb} GB")
            print(f"     GPU: {spec.cvm.gpu_type}")
        else:
            print(f"     CPU: {spec.cvm.cpu_cores} cores")
            print(f"     Memory: {spec.cvm.memory_gb} GB")
            print(f"     Disk: {spec.cvm.disk_gb} GB")
            print(f"     GPU: None")

    if spec.mysql:
        print(f"\n   MySQL Database:")
        print(f"     CPU: {spec.mysql.cpu_cores} cores")
        print(f"     Memory: {spec.mysql.memory_mb} MB")
        print(f"     Storage: {spec.mysql.storage_gb} GB")
        print(f"     Version: {spec.mysql.version}")

    # Confirm provisioning
    confirm = input("\nProceed with provisioning? (Y/n): ").strip().lower()
    if confirm and confirm != 'y':
        print("❌ Cancelled by user")
        sys.exit(0)

    # Provision resources
    try:
        # Use provided session directory if available
        session_dir = args.session_dir if hasattr(args, 'session_dir') and args.session_dir else None
        provisioner = TencentProvisioner(spec, session_dir=session_dir)
        provisioned = provisioner.provision()

        # Display results
        print("\n📋 Provisioned Resources:")

        if provisioned.cvm_instance_id:
            print(f"\n💻 CVM Instance:")
            print(f"   Instance ID: {provisioned.cvm_instance_id}")
            print(f"   Public IP: {provisioned.cvm_public_ip}")
            print(f"   Private IP: {provisioned.cvm_private_ip}")
            print(f"   SSH: ssh -i {provisioned.ssh_private_key_path} ubuntu@{provisioned.cvm_public_ip}")

        if provisioned.mysql_instance_id:
            print(f"\n🗄️  MySQL Database:")
            print(f"   Instance ID: {provisioned.mysql_instance_id}")
            print(f"   Host: {provisioned.mysql_host}:{provisioned.mysql_port}")
            print(f"   Username: {provisioned.mysql_username}")
            print(f"   Password: {provisioned.mysql_password}")
            print(f"   Connection: mysql -h {provisioned.mysql_host} -P {provisioned.mysql_port} -u {provisioned.mysql_username} -p")

        # Save to file only if user explicitly provided an output file
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            provisioned.save(args.output)

        provisioner.exec_claude(args.base_image, args.repo_url, args.model, args.api_key)

        # Cleanup if requested
        if args.cleanup:
            print("\n⚠️  Cleanup requested (waiting 10 seconds)...")
            time.sleep(10)
            provisioner.cleanup()

    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(130)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
