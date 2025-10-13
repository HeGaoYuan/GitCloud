#!/usr/bin/env python3
"""
GitCloud Session Cleanup Script
---------------------------------
Clean up session resources including:
- SSH keys in session directory
- Session information files
- Cloud resources (CVM, MySQL, VPC, etc.)
"""

import sys
import json
import argparse
import subprocess
import shutil
from pathlib import Path

# Add gitcloud to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.cvm.v20170312 import cvm_client, models as cvm_models
    from tencentcloud.cdb.v20170320 import cdb_client, models as cdb_models
    from tencentcloud.vpc.v20170312 import vpc_client, models as vpc_models
except ImportError:
    print("❌ Error: Tencent Cloud SDK not found.")
    print("Please install it with:")
    print("pip install tencentcloud-sdk-python tencentcloud-sdk-python-cdb")
    sys.exit(1)


def parse_session_files(session_dir):
    """Parse session files to extract resource IDs"""
    resources = {
        'cvm_instance_id': None,
        'mysql_instance_id': None,
        'vpc_id': None,
        'subnets': [],
        'security_group_ids': [],
        'region': 'ap-guangzhou'  # default
    }

    # Parse CVM info
    cvm_file = session_dir / "02_cvm_info.txt"
    if cvm_file.exists():
        with open(cvm_file, 'r') as f:
            for line in f:
                if line.startswith('Instance ID:'):
                    resources['cvm_instance_id'] = line.split(':', 1)[1].strip()
                elif line.startswith('Security Group:'):
                    sg_id = line.split(':', 1)[1].strip()
                    if sg_id:
                        resources['security_group_ids'].append(sg_id)

    # Parse MySQL info
    mysql_file = session_dir / "03_mysql_info.txt"
    if mysql_file.exists():
        with open(mysql_file, 'r') as f:
            for line in f:
                if line.startswith('Instance ID:'):
                    resources['mysql_instance_id'] = line.split(':', 1)[1].strip()
                elif line.startswith('Security Group:'):
                    sg_id = line.split(':', 1)[1].strip()
                    if sg_id and sg_id not in resources['security_group_ids']:
                        resources['security_group_ids'].append(sg_id)

    # Parse network info
    network_file = session_dir / "01_network_info.txt"
    if network_file.exists():
        with open(network_file, 'r') as f:
            content = f.read()
            for line in content.split('\n'):
                if line.startswith('VPC ID:'):
                    resources['vpc_id'] = line.split(':', 1)[1].strip()
                elif ':' in line and 'subnet' in line.lower():
                    # Parse subnet IDs
                    parts = line.split(':', 1)
                    if len(parts) == 2:
                        subnet_id = parts[1].strip()
                        if subnet_id.startswith('subnet-'):
                            resources['subnets'].append(subnet_id)

    # Parse specification for region
    spec_file = session_dir / "00_specification_info.txt"
    if spec_file.exists():
        with open(spec_file, 'r') as f:
            for line in f:
                if line.startswith('Region:'):
                    resources['region'] = line.split(':', 1)[1].strip()

    return resources


def cleanup_cloud_resources(resources, region):
    """Clean up cloud resources"""
    print("\n�� Cleaning up cloud resources...")

    try:
        # Get credentials from config file
        config_file = Path.home() / ".gitcloud" / "config.json"
        if not config_file.exists():
            print("   ❌ Config file not found. Please run main.py first to set up credentials.")
            return False

        with open(config_file, 'r') as f:
            config = json.load(f)

        tencent_creds = config.get('tencent_credentials', {})
        secret_id = tencent_creds.get('secret_id')
        secret_key = tencent_creds.get('secret_key')

        if not secret_id or not secret_key:
            print("   ❌ Tencent Cloud credentials not found in config.")
            print("   Please run main.py first to set up credentials.")
            return False

        cred = credential.Credential(secret_id, secret_key)

        # Initialize clients
        # CVM client
        http_profile_cvm = HttpProfile()
        http_profile_cvm.endpoint = "cvm.tencentcloudapi.com"
        client_profile_cvm = ClientProfile()
        client_profile_cvm.httpProfile = http_profile_cvm
        cvm_cli = cvm_client.CvmClient(cred, region, client_profile_cvm)

        # CDB client
        http_profile_cdb = HttpProfile()
        http_profile_cdb.endpoint = "cdb.tencentcloudapi.com"
        client_profile_cdb = ClientProfile()
        client_profile_cdb.httpProfile = http_profile_cdb
        cdb_cli = cdb_client.CdbClient(cred, region, client_profile_cdb)

        # VPC client
        http_profile_vpc = HttpProfile()
        http_profile_vpc.endpoint = "vpc.tencentcloudapi.com"
        client_profile_vpc = ClientProfile()
        client_profile_vpc.httpProfile = http_profile_vpc
        vpc_cli = vpc_client.VpcClient(cred, region, client_profile_vpc)

        # Terminate CVM instance
        if resources['cvm_instance_id']:
            try:
                print(f"   🖥️  Terminating CVM: {resources['cvm_instance_id']}")
                req = cvm_models.TerminateInstancesRequest()
                params = {"InstanceIds": [resources['cvm_instance_id']]}
                req.from_json_string(json.dumps(params))
                cvm_cli.TerminateInstances(req)
                print(f"   ✅ CVM instance terminated")
            except Exception as e:
                print(f"   ⚠️  Failed to terminate CVM: {e}")

        # Isolate MySQL instance
        if resources['mysql_instance_id']:
            try:
                print(f"   🗄️  Isolating MySQL: {resources['mysql_instance_id']}")
                req = cdb_models.IsolateDBInstanceRequest()
                params = {"InstanceId": resources['mysql_instance_id']}
                req.from_json_string(json.dumps(params))
                cdb_cli.IsolateDBInstance(req)
                print(f"   ✅ MySQL instance isolated")
            except Exception as e:
                print(f"   ⚠️  Failed to isolate MySQL: {e}")

        # Wait a bit for resources to detach
        import time
        if resources['cvm_instance_id'] or resources['mysql_instance_id']:
            print("   ⏳ Waiting for resources to detach (30 seconds)...")
            time.sleep(30)

        # Delete security groups
        for sg_id in resources['security_group_ids']:
            try:
                print(f"   🛡️  Deleting security group: {sg_id}")
                req = vpc_models.DeleteSecurityGroupRequest()
                params = {"SecurityGroupId": sg_id}
                req.from_json_string(json.dumps(params))
                vpc_cli.DeleteSecurityGroup(req)
                print(f"   ✅ Security group deleted")
            except Exception as e:
                print(f"   ⚠️  Failed to delete security group {sg_id}: {e}")

        # Delete subnets
        for subnet_id in resources['subnets']:
            try:
                print(f"   🌐 Deleting subnet: {subnet_id}")
                req = vpc_models.DeleteSubnetRequest()
                params = {"SubnetId": subnet_id}
                req.from_json_string(json.dumps(params))
                vpc_cli.DeleteSubnet(req)
                print(f"   ✅ Subnet deleted")
            except Exception as e:
                print(f"   ⚠️  Failed to delete subnet {subnet_id}: {e}")

        # Delete VPC
        if resources['vpc_id']:
            try:
                print(f"   🌐 Deleting VPC: {resources['vpc_id']}")
                req = vpc_models.DeleteVpcRequest()
                params = {"VpcId": resources['vpc_id']}
                req.from_json_string(json.dumps(params))
                vpc_cli.DeleteVpc(req)
                print(f"   ✅ VPC deleted")
            except Exception as e:
                print(f"   ⚠️  Failed to delete VPC: {e}")

        print("\n✅ Cloud resources cleanup completed")
        return True

    except Exception as e:
        print(f"\n❌ Error during cloud cleanup: {e}")
        return False


def cleanup_local_files(session_dir, keep_logs=False):
    """Clean up local session directory"""
    print("\n🧹 Cleaning up local session files...")

    try:
        if keep_logs:
            # Only delete sensitive files (SSH keys)
            ssh_key = session_dir / "ssh_key"
            ssh_pub = session_dir / "ssh_key.pub"
            if ssh_key.exists():
                ssh_key.unlink()
                print(f"   🔑 Deleted SSH private key")
            if ssh_pub.exists():
                ssh_pub.unlink()
                print(f"   🔑 Deleted SSH public key")
            print(f"   📄 Session logs kept in: {session_dir}")
        else:
            # Delete entire session directory
            shutil.rmtree(session_dir)
            print(f"   ✅ Deleted session directory: {session_dir}")

        return True

    except Exception as e:
        print(f"   ⚠️  Error cleaning up local files: {e}")
        return False


def list_sessions():
    """List all available sessions"""
    session_base = Path.home() / ".gitcloud" / "session"

    if not session_base.exists():
        print("No sessions found.")
        return 0

    sessions = [d for d in session_base.iterdir() if d.is_dir() and d.name.startswith('session_')]
    if not sessions:
        print("No sessions found.")
        return 0

    print("\n📋 Available Sessions:")
    print("="*70)
    for session in sorted(sessions):
        session_name = session.name
        # Check what resources exist
        has_cvm = (session / "02_cvm_info.txt").exists()
        has_mysql = (session / "03_mysql_info.txt").exists()
        resources = []
        if has_cvm:
            resources.append("CVM")
        if has_mysql:
            resources.append("MySQL")

        print(f"  {session_name}")
        print(f"    Path: {session}")
        print(f"    Resources: {', '.join(resources) if resources else 'None'}")
        print()

    return 0


def main():
    parser = argparse.ArgumentParser(
        description='GitCloud Session Cleanup',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clean up a specific session (removes cloud resources and local files)
  python cleanup.py session_20250113_143022

  # Keep session logs locally (only delete SSH keys and cloud resources)
  python cleanup.py session_20250113_143022 --keep-logs

  # Only clean up local files (don't touch cloud resources)
  python cleanup.py session_20250113_143022 --local-only

  # List all sessions
  python cleanup.py --list
        """
    )

    parser.add_argument('session_id', nargs='?', help='Session ID to clean up (e.g., session_20250113_143022)')
    parser.add_argument('--keep-logs', action='store_true',
                       help='Keep session logs, only delete SSH keys and cloud resources')
    parser.add_argument('--local-only', action='store_true',
                       help='Only clean up local files, do not touch cloud resources')
    parser.add_argument('--list', action='store_true',
                       help='List all available sessions')

    args = parser.parse_args()

    gitcloud_dir = Path.home() / ".gitcloud"
    session_base = gitcloud_dir / "session"

    # List sessions
    if args.list:
        return list_sessions()

    # Validate session ID
    if not args.session_id:
        print("❌ Error: Session ID is required")
        print("Usage: python cleanup.py <session_id>")
        print("       python cleanup.py --list  (to list all sessions)")
        return 1

    session_id = args.session_id
    if not session_id.startswith('session_'):
        session_id = f'session_{session_id}'

    session_dir = session_base / session_id

    if not session_dir.exists():
        print(f"❌ Error: Session not found: {session_dir}")
        print("\nAvailable sessions:")
        subprocess.run([sys.executable, __file__, '--list'])
        return 1

    print("="*70)
    print(f"🧹 GitCloud Session Cleanup")
    print("="*70)
    print(f"\nSession: {session_id}")
    print(f"Path: {session_dir}")
    print()

    # Parse session files
    resources = parse_session_files(session_dir)

    # Show what will be cleaned up
    print("Resources to clean up:")
    if resources['cvm_instance_id']:
        print(f"  🖥️  CVM Instance: {resources['cvm_instance_id']}")
    if resources['mysql_instance_id']:
        print(f"  🗄️  MySQL Instance: {resources['mysql_instance_id']}")
    if resources['vpc_id']:
        print(f"  🌐 VPC: {resources['vpc_id']}")
    if resources['subnets']:
        print(f"  🌐 Subnets: {len(resources['subnets'])} subnet(s)")
    if resources['security_group_ids']:
        print(f"  🛡️  Security Groups: {len(resources['security_group_ids'])} group(s)")
    print(f"  📁 Local files: {session_dir}")

    # Confirm
    if not args.local_only:
        print("\n⚠️  WARNING: This will delete cloud resources and may be irreversible!")
    print("Type 'yes' to confirm cleanup:")
    confirmation = input("> ").strip().lower()

    if confirmation != 'yes':
        print("❌ Cleanup cancelled")
        return 0

    # Perform cleanup
    success = True

    # Clean up cloud resources
    if not args.local_only:
        cloud_success = cleanup_cloud_resources(resources, resources['region'])
        success = success and cloud_success

    # Clean up local files
    local_success = cleanup_local_files(session_dir, args.keep_logs)
    success = success and local_success

    if success:
        print("\n" + "="*70)
        print("✅ Session cleanup completed successfully!")
        print("="*70)
        return 0
    else:
        print("\n" + "="*70)
        print("⚠️  Session cleanup completed with errors")
        print("="*70)
        return 1


def main_with_args(args):
    """Main function that accepts parsed arguments"""
    # Handle --list
    if args.list:
        return list_sessions()

    # Check session_id
    if not args.session_id:
        print("❌ Error: session_id is required")
        print("\nUsage:")
        print("  gitcloud clean <session_id>")
        print("  gitcloud clean --list")
        return 1

    # Perform cleanup
    session_base = Path.home() / ".gitcloud" / "session"
    session_dir = session_base / args.session_id

    if not session_dir.exists():
        print(f"❌ Session directory not found: {session_dir}")
        return 1

    # Load config for credentials
    config_file = Path.home() / ".gitcloud" / "config.json"
    if not config_file.exists():
        print("❌ Config file not found. Cannot access cloud credentials.")
        return 1

    with open(config_file, 'r') as f:
        config = json.load(f)

    # Get credentials
    credentials = config.get('tencent_credentials', {})
    secret_id = credentials.get('secret_id')
    secret_key = credentials.get('secret_key')

    if not secret_id or not secret_key:
        print("❌ Tencent Cloud credentials not found in config")
        return 1

    # Parse session files
    resources = parse_session_files(session_dir)

    # Display cleanup info
    print("\n" + "="*70)
    print("🧹 GitCloud Session Cleanup")
    print("="*70)
    print(f"\nSession: {args.session_id}")
    print(f"Path: {session_dir}\n")

    print("Resources to clean up:")
    if resources['cvm_instance_id']:
        print(f"  🖥️  CVM Instance: {resources['cvm_instance_id']}")
    if resources['mysql_instance_id']:
        print(f"  🗄️  MySQL Instance: {resources['mysql_instance_id']}")
    if resources['vpc_id']:
        print(f"  🌐 VPC: {resources['vpc_id']}")
    if resources['subnets']:
        print(f"  🌐 Subnets: {len(resources['subnets'])} subnet(s)")
    if resources['security_group_ids']:
        print(f"  🛡️  Security Groups: {len(resources['security_group_ids'])} group(s)")
    print(f"  📁 Local files: {session_dir}")

    # Confirm
    if not args.local_only:
        print("\n⚠️  WARNING: This will delete cloud resources and may be irreversible!")
    print("Type 'yes' to confirm cleanup:")
    confirmation = input("> ").strip().lower()

    if confirmation != 'yes':
        print("❌ Cleanup cancelled")
        return 0

    # Perform cleanup
    success = True

    # Clean up cloud resources
    if not args.local_only:
        cloud_success = cleanup_cloud_resources(resources, resources['region'])
        success = success and cloud_success

    # Clean up local files
    local_success = cleanup_local_files(session_dir, args.keep_logs)
    success = success and local_success

    if success:
        print("\n" + "="*70)
        print("✅ Session cleanup completed successfully!")
        print("="*70)
        return 0
    else:
        print("\n" + "="*70)
        print("⚠️  Session cleanup completed with errors")
        print("="*70)
        return 1


if __name__ == '__main__':
    sys.exit(main())
