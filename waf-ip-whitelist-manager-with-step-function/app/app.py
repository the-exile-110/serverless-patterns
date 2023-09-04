import boto3
from pydantic import BaseModel, ValidationError

MAX_RETRIES = 3
IP_SET_NAME = 'test-ip-set'
IP_SET_ID = '2741a49f-24b9-4b39-b777-13077544bfc7'

waf_client = boto3.client('wafv2')

class IPs(BaseModel):
    ip_list: list[str]
    action: str  # 用于指定操作是添加还是删除

def get_current_ips_and_lock_token():
    ip_set = waf_client.get_ip_set(Id=IP_SET_ID, Name=IP_SET_NAME, Scope='REGIONAL')
    return set(ip_set['IPSet']['Addresses']), ip_set['LockToken']

def add_ips_to_whitelist(ip_list, current_ips, lock_token):
    for ip in ip_list:
        current_ips.add(ip)
    response = waf_client.update_ip_set(
        Id=IP_SET_ID,
        Name=IP_SET_NAME,
        Scope='REGIONAL',
        LockToken=lock_token,
        Addresses=list(current_ips)
    )
    return {'message': 'IPs added to whitelist.'}

def delete_ips_from_whitelist(ip_list, current_ips, lock_token):
    for ip in ip_list:
        current_ips.discard(ip)
    response = waf_client.update_ip_set(
        Id=IP_SET_ID,
        Name=IP_SET_NAME,
        Scope='REGIONAL',
        LockToken=lock_token,
        Addresses=list(current_ips)
    )
    return {'message': 'IPs removed from whitelist.'}

def lambda_handler(event, context):
    try:
        ips = IPs(**event)
    except ValidationError as e:
        return {
            'statusCode': 400,
            'body': str(e)
        }

    current_ips, lock_token = get_current_ips_and_lock_token()

    try:
        match ips.action:
            case "add":
                return add_ips_to_whitelist(ips.ip_list, current_ips, lock_token)
            case "delete":
                return delete_ips_from_whitelist(ips.ip_list, current_ips, lock_token)
            case _:
                return {
                    'statusCode': 400,
                    'body': "Invalid action provided."
                }
    except Exception as e:
        return {
            'statusCode': 400,
            'body': str(e)
        }