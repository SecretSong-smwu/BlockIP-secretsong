import boto3

wafv2 = boto3.client('wafv2', region_name='ap-northeast-2')

IP_SET_ID = ""  # IP Set 생성 후 ID
IP_SET_NAME = "SOARBlockedIPs-secretsong"
SCOPE = "REGIONAL"

def lambda_handler(event, context):
    analysis = event.get("riskResult", {}).get("Payload", {}).get("analysis", {})
    src_ip = analysis.get("src_ip") or event.get("src_ip")

    if not src_ip:
        return {"statusCode": 400, "error": "src_ip가 없습니다."}

    try:
        # 현재 IP Set 조회 (LockToken 필요)
        current = wafv2.get_ip_set(Name=IP_SET_NAME, Scope=SCOPE, Id=IP_SET_ID)
        addresses = current['IPSet']['Addresses']
        lock_token = current['LockToken']

        cidr = f"{src_ip}/32"
        if cidr not in addresses:
            addresses.append(cidr)

        wafv2.update_ip_set(
            Name=IP_SET_NAME,
            Scope=SCOPE,
            Id=IP_SET_ID,
            Addresses=addresses,
            LockToken=lock_token
        )

        return {"statusCode": 200, "blocked_ip": src_ip, "ip_set": IP_SET_NAME}

    except Exception as e:
        return {"statusCode": 500, "error": str(e)}
