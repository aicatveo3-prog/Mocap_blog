# 텔레그램 대화형 승인 봇 (Cloudflare Worker)

텔레그램에서 **[✅ 발행] / [✏️ 수정] / [❌ 폐기]** 버튼을 누르거나 `수정 1: 내용` 으로
답장하면, 이 Worker가 GitHub PR을 병합/닫기/코멘트 처리한다.

```
당신(텔레그램) ↔ Cloudflare Worker(worker.js) ↔ GitHub PR
```

---

## 1) GitHub 토큰 발급 (PR 병합용)

1. GitHub → 우상단 프로필 → **Settings**
2. 좌하단 **Developer settings** → **Personal access tokens** → **Fine-grained tokens** → **Generate new token**
3. 설정:
   - **Repository access**: Only select repositories → `Mocap_blog`
   - **Permissions**:
     - **Contents**: Read and write
     - **Pull requests**: Read and write
4. **Generate token** → 토큰 복사 (한 번만 보임! 안전한 곳에 임시 보관)

## 2) Cloudflare Worker 만들기

1. https://dash.cloudflare.com 가입 (무료, 카드 불필요)
2. 좌측 **Workers & Pages** → **Create** → **Create Worker**
3. 이름 정하고(예: `mocap-bot`) **Deploy**
4. **Edit code** → 기본 코드를 지우고 `worker.js` 내용 전체 붙여넣기 → **Deploy**
5. Worker 주소 복사 (예: `https://mocap-bot.<계정>.workers.dev`)

## 3) Worker에 환경변수 넣기

Worker → **Settings** → **Variables and Secrets** → 아래를 추가:

| 이름 | 종류 | 값 |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | Secret | 봇 토큰 (`8012...:AAH...`) |
| `TELEGRAM_CHAT_ID` | Text | 내 chat_id (숫자) |
| `GITHUB_TOKEN` | Secret | 1)에서 발급한 토큰 |
| `GH_OWNER` | Text | `aicatveo3-prog` |
| `GH_REPO` | Text | `Mocap_blog` |
| `WEBHOOK_SECRET` | Secret | 아무 긴 랜덤 문자열(예: 32자) |

저장 후 다시 **Deploy**.

## 4) 텔레그램 웹훅 등록

브라우저 주소창에 아래를 입력(값 3개를 본인 것으로 치환):

```
https://api.telegram.org/bot<봇토큰>/setWebhook?url=<Worker주소>&secret_token=<WEBHOOK_SECRET>
```

`{"ok":true,...}` 가 나오면 성공.

> 해제하려면: `https://api.telegram.org/bot<봇토큰>/deleteWebhook`

## 5) 끝 — 사용법

- 알림의 **버튼**으로 발행/폐기
- **수정**: `수정 1: 더 짧게, 예시 추가` 처럼 답장 → 해당 PR에 코멘트로 남김
- 텍스트 명령: `발행 1`, `폐기 1`

## 보안 메모

- Worker는 **내 chat_id 에서 온 요청만** 처리한다(다른 사람이 봇을 찾아도 조작 불가).
- 웹훅은 `WEBHOOK_SECRET` 헤더로 위조를 막는다.
- 토큰은 절대 코드/저장소에 넣지 말고 **Cloudflare Secret** 으로만 보관한다.
