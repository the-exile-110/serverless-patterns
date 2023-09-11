import boto3
from pydantic import BaseModel, ValidationError

MAX_RETRIES = 3

# Both name and IDs are determined based on grade_id
IP_SETS = {
    "1": {"name": "ip_set_1", "id": "cee3c953-a408-4317-bad4-0eabae69b48f"},
    "2": {"name": "ip_set_2", "id": "57acce0a-c99a-46f4-a151-e48dbe2870ec"},
    "3": {"name": "ip_set_3", "id": "b1c737ab-8bfd-4a5a-a0dc-15acb4f19763"}
}

waf_client = boto3.client('wafv2')

class IPs(BaseModel):
    ip: str
    action: str  # "add", "delete" or "update"
    old_ip: str = None  # Used when action is "update"
    grade_id: str  # "1", "2", or "3"

def get_current_ips_and_lock_token(ip_set_id, ip_set_name):
    ip_set = waf_client.get_ip_set(Id=ip_set_id, Name=ip_set_name, Scope='REGIONAL')
    return set(ip_set['IPSet']['Addresses']), ip_set['LockToken']

def update_ips_in_whitelist(ip, old_ip, action, current_ips, lock_token, ip_set_id, ip_set_name):
    if action == "add":
        current_ips.add(ip)
    elif action == "delete":
        current_ips.discard(ip)
    elif action == "update":
        current_ips.discard(old_ip)
        current_ips.add(ip)

    response = waf_client.update_ip_set(
        Id=ip_set_id,
        Name=ip_set_name,
        Scope='REGIONAL',
        LockToken=lock_token,
        Addresses=list(current_ips)
    )

    return {'message': f'IPs {action}ed successfully.'}

def lambda_handler(event, context):
    try:
        ips = IPs(**event)
    except ValidationError as e:
        return {
            'statusCode': 400,
            'body': str(e)
        }

    if ips.grade_id not in IP_SETS:
        return {
            'statusCode': 400,
            'body': "Invalid grade_id provided."
        }
    ip_set_id = IP_SETS[ips.grade_id]["id"]
    ip_set_name = IP_SETS[ips.grade_id]["name"]

    current_ips, lock_token = get_current_ips_and_lock_token(ip_set_id, ip_set_name)

    try:
        return update_ips_in_whitelist(ips.ip, ips.old_ip, ips.action, current_ips, lock_token, ip_set_id, ip_set_name)
    except Exception as e:
        return {
            'statusCode': 400,
            'body': str(e)
        }
