import boto3
from fastapi import FastAPI, HTTPException
from mangum import Mangum
from pydantic import BaseModel

MAX_RETRIES = 3
IP_SET_NAME = 'test-ip-set'
IP_SET_ID = '2741a49f-24b9-4b39-b777-13077544bfc7'

waf_client = boto3.client('wafv2')


class IPs(BaseModel):
    ip_list: list[str]


app = FastAPI(title='SAM FastAPI', version='0.1.0', root_path='/Prod/')


@app.get('/hello', status_code=200)
async def root():
    return {'message': 'Hello SAM World'}


@app.post('/whitelist')
async def add_to_whitelist(ips: IPs):
    # 使用AWS SDK来添加IP到WAF的白名单

    # 首先获取当前的IP集合及LockToken
    ip_set = waf_client.get_ip_set(Id=IP_SET_ID, Name=IP_SET_NAME, Scope='REGIONAL')
    current_ips = ip_set['IPSet']['Addresses']
    lock_token = ip_set['LockToken']

    # 添加新的IP到列表中
    updated_ips = set(current_ips)  # 使用set避免重复
    for ip in ips.ip_list:
        updated_ips.add(ip)

    # 更新IP集合
    try:
        response = waf_client.update_ip_set(
            Id=IP_SET_ID,
            Name=IP_SET_NAME,
            Scope='REGIONAL',
            LockToken=lock_token,
            Addresses=list(updated_ips)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {'message': 'IPs added to whitelist.'}


@app.delete('/whitelist')
async def delete_from_whitelist(ips: IPs):
    # 使用AWS SDK来从WAF的白名单中删除IP

    # 首先获取当前的IP集合及LockToken
    ip_set = waf_client.get_ip_set(Id=IP_SET_ID, Name=IP_SET_NAME, Scope='REGIONAL')
    current_ips = set(ip_set['IPSet']['Addresses'])
    lock_token = ip_set['LockToken']

    # 从集合中移除指定的IP
    for ip in ips.ip_list:
        current_ips.discard(ip)

    # 使用更新后的IP集合进行更新
    try:
        response = waf_client.update_ip_set(
            Id=IP_SET_ID,
            Name=IP_SET_NAME,
            Scope='REGIONAL',
            LockToken=lock_token,
            Addresses=list(current_ips)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {'message': 'IPs removed from whitelist.'}


lambda_handler = Mangum(app)
