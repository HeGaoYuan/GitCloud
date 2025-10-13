import sys
import time
import json

# Try to import Tencent Cloud SDK
try:
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
    from tencentcloud.cvm.v20170312 import cvm_client, models as cvm_models
    from tencentcloud.vpc.v20170312 import vpc_client, models as vpc_models
except ImportError:
    print("❌ Error: Tencent Cloud SDK not found.")
    print("Please install it with:")
    print("pip install tencentcloud-sdk-python")
    sys.exit(1)

def create_vpc_and_subnets(vpc_client_obj, region):
    """Create VPC and subnets for multiple availability zones"""
    print("\n📡 Creating VPC and Subnets...")

    try:
        # Create VPC with timestamp for uniqueness
        vpc_timestamp = int(time.time())
        req = vpc_models.CreateVpcRequest()
        params = {
            "VpcName": f"gitcloud-vpc-{vpc_timestamp}",
            "CidrBlock": "10.0.0.0/16"
        }
        req.from_json_string(json.dumps(params))
        resp = vpc_client_obj.CreateVpc(req)

        vpc_id = resp.Vpc.VpcId
        print(f"✅ VPC created: {vpc_id}")

        # Wait a bit for VPC to be ready
        time.sleep(3)

        # Get available zones for the region
        zones = _get_available_zones(region)

        # Create subnets for each zone
        subnets = {}
        for idx, zone in enumerate(zones):
            try:
                req = vpc_models.CreateSubnetRequest()
                params = {
                    "VpcId": vpc_id,
                    "SubnetName": f"gitcloud-subnet-{zone}",
                    "CidrBlock": f"10.0.{idx+1}.0/24",  # Different CIDR for each subnet
                    "Zone": zone
                }
                req.from_json_string(json.dumps(params))
                resp = vpc_client_obj.CreateSubnet(req)

                subnet_id = resp.Subnet.SubnetId
                subnets[zone] = subnet_id
                print(f"✅ Subnet created for {zone}: {subnet_id}")

            except TencentCloudSDKException as err:
                print(f"⚠️  Failed to create subnet for {zone}: {err}")
                # Continue with other zones

        if not subnets:
            raise Exception("Failed to create any subnets")

        return vpc_id, subnets

    except TencentCloudSDKException as err:
        print(f"❌ Failed to create VPC/Subnets: {err}")
        raise


def _get_available_zones(region):
    """Get list of availability zones to try for a region"""
    # Common availability zones for each region
    zone_mappings = {
        'ap-guangzhou': ['ap-guangzhou-3', 'ap-guangzhou-4', 'ap-guangzhou-6', 'ap-guangzhou-7'],
        'ap-shanghai': ['ap-shanghai-2', 'ap-shanghai-3', 'ap-shanghai-4', 'ap-shanghai-5'],
        'ap-beijing': ['ap-beijing-3', 'ap-beijing-4', 'ap-beijing-5', 'ap-beijing-6', 'ap-beijing-7'],
        'ap-chengdu': ['ap-chengdu-1', 'ap-chengdu-2'],
        'ap-nanjing': ['ap-nanjing-1', 'ap-nanjing-2', 'ap-nanjing-3'],
        'ap-hongkong': ['ap-hongkong-2', 'ap-hongkong-3'],
        'ap-singapore': ['ap-singapore-1', 'ap-singapore-2', 'ap-singapore-3'],
    }

    # Return zones for region, or fallback to zone-1, zone-2, zone-3
    return zone_mappings.get(region, [f"{region}-1", f"{region}-2", f"{region}-3"])

def create_security_group_for_all(cred, region="ap-guangzhou"):
    """Create a security group with SSH, HTTP ports open"""
    try:
        httpProfile = HttpProfile()
        httpProfile.endpoint = "vpc.tencentcloudapi.com"

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile

        client = vpc_client.VpcClient(cred, region, clientProfile)

        # Create security group
        req = vpc_models.CreateSecurityGroupRequest()
        params = {
            "GroupName": f"gitcloud-sg-{int(time.time())}",
            "GroupDescription": "gitcloud security group for SSH and web access"
        }
        req.from_json_string(json.dumps(params))

        resp = client.CreateSecurityGroup(req)
        sg_id = resp.SecurityGroup.SecurityGroupId
        print(f"✅ Created security group: {sg_id}")

        # Add ingress rules (first request) - Allow all inbound traffic
        ingress_req = vpc_models.CreateSecurityGroupPoliciesRequest()
        ingress_params = {
            "SecurityGroupId": sg_id,
            "SecurityGroupPolicySet": {
                "Ingress": [
                    {
                        "Protocol": "ALL",
                        "Port": "ALL",
                        "CidrBlock": "0.0.0.0/0",
                        "Action": "ACCEPT",
                        "PolicyDescription": "Allow all inbound traffic"
                    }
                ]
            }
        }
        ingress_req.from_json_string(json.dumps(ingress_params))
        client.CreateSecurityGroupPolicies(ingress_req)
        print("✅ Ingress rules configured (all ports open)")
        # Add egress rules (second request)
        egress_req = vpc_models.CreateSecurityGroupPoliciesRequest()
        egress_params = {
            "SecurityGroupId": sg_id,
            "SecurityGroupPolicySet": {
                "Egress": [
                    {
                        "Protocol": "ALL",
                        "Port": "ALL",
                        "CidrBlock": "0.0.0.0/0",
                        "Action": "ACCEPT",
                        "PolicyDescription": "Allow all outbound traffic"
                    }
                ]
            }
        }
        egress_req.from_json_string(json.dumps(egress_params))
        client.CreateSecurityGroupPolicies(egress_req)
        print("✅ Egress rules configured")
        return sg_id

    except TencentCloudSDKException as err:
        print(f"❌ Error creating security group: {err}")
        return None


def create_security_group_for_mysql(cred, region="ap-guangzhou"):
    """Create a security group with SSH, HTTP ports open"""
    try:
        httpProfile = HttpProfile()
        httpProfile.endpoint = "vpc.tencentcloudapi.com"

        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile

        client = vpc_client.VpcClient(cred, region, clientProfile)

        # Create security group
        req = vpc_models.CreateSecurityGroupRequest()
        params = {
            "GroupName": f"gitcloud-sg-{int(time.time())}",
            "GroupDescription": "gitcloud security group for SSH and web access"
        }
        req.from_json_string(json.dumps(params))

        resp = client.CreateSecurityGroup(req)
        sg_id = resp.SecurityGroup.SecurityGroupId
        print(f"✅ Created security group: {sg_id}")

        # Add ingress rules (first request) - Allow all inbound traffic
        ingress_req = vpc_models.CreateSecurityGroupPoliciesRequest()
        ingress_params = {
            "SecurityGroupId": sg_id,
            "SecurityGroupPolicySet": {
                "Ingress": [
                    {
                        "Protocol": "TCP",
                        "Port": "3306",
                        "CidrBlock": "0.0.0.0/0",
                        "Action": "ACCEPT",
                        "PolicyDescription": "Allow MySQL access from anywhere"
                    }
                ]
            }
        }
        ingress_req.from_json_string(json.dumps(ingress_params))
        client.CreateSecurityGroupPolicies(ingress_req)
        print("✅ Ingress rules configured (3306 port open)")
        return sg_id

    except TencentCloudSDKException as err:
        print(f"❌ Error creating security group: {err}")
        return None
