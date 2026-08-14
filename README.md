# BlockIP-secretsong

> **GitHub Description (About 한 줄):**
> 승인된 공격자 IP를 AWS WAF IP Set에 등록해 실시간 차단하는 Lambda — SOAR 자동 대응의 최종 실행 단계

SOAR 워크플로우에서 담당자가 IP 차단을 승인한 뒤 실행되는 최종 액션 Lambda입니다. AWS WAF의 IP Set에 공격자 IP를 추가해서, 서비스 API Gateway 앞단에서 해당 IP의 요청이 즉시 차단되도록 합니다.

## 설계 결정: NACL 대신 WAF를 선택한 이유

이 프로젝트는 여러 사용자가 함께 쓰는 **공유 계정 환경**에서 진행되었습니다. 최초에는 Network ACL(Deny 룰)로 IP 차단을 구현하려 했으나, NACL은 **서브넷 전체**에 적용되는 리소스라 다른 사용자의 리소스에도 영향을 줄 수 있다는 문제를 인지했습니다. 이에 따라 **특정 리소스(API Gateway) 단위로만 영향을 주는 AWS WAF**로 설계를 전환했습니다. 실무에서도 웹 서비스 앞단의 IP 차단에는 WAF가 더 일반적으로 쓰이는 방식입니다.

## 동작 방식

1. Step Functions 실행 컨텍스트(`riskResult.Payload.analysis.src_ip`) 또는 직접 이벤트(`src_ip`)에서 차단 대상 IP를 추출합니다.
2. `get_ip_set`으로 현재 WAF IP Set의 주소 목록과 `LockToken`(동시 수정 방지용)을 조회합니다.
3. 대상 IP(`/32` CIDR)가 목록에 없으면 추가합니다.
4. `update_ip_set`으로 갱신합니다.

## 입력 예시 (Step Functions 컨텍스트)

```json
{
  "riskResult": {
    "Payload": {
      "analysis": { "src_ip": "192.168.1.100", "risk_level": "HIGH" }
    }
  }
}
```

## 출력 예시

```json
{ "statusCode": 200, "blocked_ip": "192.168.1.100", "ip_set": "SOARBlockedIPs-secretsong" }
```

## 사전 준비 (WAF 콘솔)

1. WAF & Shield → IP sets → Create IP set (Region: 서울, IPv4, 빈 상태로 생성)
2. Web ACLs → Create web ACL → Regional resources에서 차단 대상 API Gateway 연결 → IP Set 기반 룰(Block) 추가

## 필요 IAM 권한

```json
{
  "Effect": "Allow",
  "Action": ["wafv2:GetIPSet", "wafv2:UpdateIPSet"],
  "Resource": "arn:aws:wafv2:<region>:<account-id>:regional/ipset/<IP_SET_NAME>/<IP_SET_ID>"
}
```

## 트러블슈팅 노트

- `AccessDeniedException (wafv2:GetIPSet)`: 코드에 하드코딩된 리소스 이름/ID와 실제 생성된 리소스(계정별 접미사 포함)가 불일치했던 사례. 에러 메시지에 포함된 실제 ARN을 그대로 코드/IAM 정책에 반영해 해결.

## 관련 리소스

- 호출 주체: Step Functions SOAR 워크플로우의 `BlockIP` state (승인 성공 시)
- 이전 단계: [ApprovalProcessor-secretsong](../ApprovalProcessor-secretsong)

## 기술 스택

Python 3.12 · boto3 · AWS WAF (wafv2) · AWS Lambda
