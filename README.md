# CoinEasy Channel Forwarder Bot

Wallet V KR / Squid KR / Yellow KR / OriginTrail KR 채널의 새 공지를 **@coiniseasy** 로 자동 포워딩합니다.

## 작동 방식
- Telethon **user account** 사용 (봇 admin 권한 불필요)
- 원본 그대로 forward → 출처 자동 표시
- StringSession 방식 → Railway에 세션 파일 업로드 불필요

## 사전 준비
사용할 텔레그램 계정이 다음 채널에 모두 가입되어 있어야 함:
- @WalletvKR (소스)
- @squid_kor_update (소스)
- @YellowKorea_ann (소스)
- @Origintrailkr (소스)
- @coiniseasy (목적지 — **포스팅 권한 필요, 즉 admin이거나 본인 소유**)

## 1단계: 로컬에서 세션 문자열 생성 (1회만)

```bash
pip install -r requirements.txt
export TELEGRAM_API_ID=12345         # my.telegram.org
export TELEGRAM_API_HASH=abcdef...
python generate_session.py
```

전화번호 + OTP 입력하면 긴 문자열이 출력됨. 복사해두세요.

## 2단계: Railway 배포

새 Railway 서비스 생성 후 환경변수 3개 설정:

| 이름 | 값 |
|---|---|
| `TELEGRAM_API_ID` | 12345 |
| `TELEGRAM_API_HASH` | abcdef... |
| `TELETHON_SESSION_STRING` | (1단계에서 복사한 문자열) |

선택:
| 이름 | 기본값 |
|---|---|
| `COINEASY_ANNOUNCE_CHANNEL` | `coiniseasy` |

배포 후 로그에서 다음 메시지 확인:
```
✓ source @WalletvKR -> ...
✓ source @squid_kor_update -> ...
✓ source @YellowKorea_ann -> ...
✓ destination -> ...
Listening for new messages...
```

## 소스 채널 추가
`forwarder.py` 의 `SOURCE_CHANNELS` 리스트에 추가 → redeploy.

## 보안 주의
`TELETHON_SESSION_STRING` 은 본인 텔레그램 계정 로그인 권한과 동일합니다.
절대 git에 커밋하지 말고, Railway secret으로만 관리하세요.
