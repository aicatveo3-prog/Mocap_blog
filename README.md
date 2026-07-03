# AI 모션캡쳐 랩 🎥🤖

AI 기반 모션캡쳐 기술을 **매일 두 편씩 자동으로** 찾아 글을 쓰고 발행하는 블로그입니다.

- **엔진**: Claude Code 예약 루틴(Routine) — 매일 세션이 스스로 깨어나 실행 (별도 API 키 불필요)
- **콘텐츠 생성**: Claude가 웹 검색으로 최신 주제 조사 후 한국어 글 작성
- **발행**: Git 커밋 → GitHub Pages(Jekyll) 자동 배포

```
매일 06:00 KST  →  Claude Code 세션 자동 실행  →  주제 2개 웹검색  →  글 2편 작성  →  _posts/에 커밋·푸시  →  Pages 자동 배포
```

매일의 작업 지시서는 [`automation/daily-prompt.md`](automation/daily-prompt.md)에 있으며,
글 주제·톤·규칙을 바꾸려면 이 파일만 수정하면 됩니다.

---

## 폴더 구조

```
.
├── _config.yml                 # Jekyll 설정
├── index.html                  # 홈(글 목록)
├── about.md                    # 소개 페이지
├── feed.xml                    # Atom 피드
├── _layouts/                   # default / post 레이아웃
├── assets/css/style.css        # 스타일(라이트·다크 모드)
├── _posts/                     # 발행된 글 (자동으로 쌓임)
└── automation/
    └── daily-prompt.md         # 매일 실행되는 작업 지시서
```

---

## 어떻게 매일 자동으로 굴러가나요?

이 블로그는 **Claude Code 예약 루틴(Routine)** 으로 돌아갑니다.
매일 정해진 시각에 Claude Code 세션이 스스로 깨어나서:

1. 저장소를 최신으로 맞추고,
2. `automation/daily-prompt.md` 지시서를 따라,
3. 웹 검색으로 AI 모션캡쳐 최신 주제 2개를 찾아 한국어 글 2편을 쓰고,
4. `_posts/`에 커밋·푸시합니다.

→ GitHub Pages가 사이트를 다시 빌드해 발행합니다. **Anthropic API 키를 따로 관리할 필요가 없습니다.**

---

## 처음 설정 (한 번만)

### 1. GitHub Pages 켜기
저장소 → **Settings → Pages**
- **Source**: `Deploy from a branch`
- **Branch**: `main` / `/ (root)` → **Save**

잠시 뒤 `https://<사용자명>.github.io/<저장소명>/` 에서 사이트가 열립니다.

> 프로젝트 페이지(`.../저장소명/` 형태)라면 `_config.yml` 의 `baseurl` 을 `"/저장소명"`,
> `url` 을 `"https://<사용자명>.github.io"` 로 설정하면 링크가 정확해집니다.

### 2. 예약 루틴 활성화
Claude Code에게 "매일 블로그 글 자동 생성 루틴을 만들어줘"라고 요청하면
매일 실행되는 예약 트리거가 설정됩니다(발행 브랜치: `main`).
지금 바로 한 번 돌려보려면 "지금 오늘치 글 생성해줘"라고 하면 됩니다.

---

## 로컬에서 미리보기 (선택)

```bash
bundle install
bundle exec jekyll serve      # http://localhost:4000
```

---

## 커스터마이즈

| 하고 싶은 것 | 바꿀 곳 |
|---|---|
| 다루는 주제·글 톤·분량·편수 | `automation/daily-prompt.md` |
| 실행 시각 변경 | Claude Code 루틴(트리거)의 스케줄 |
| 사이트 제목·소개 | `_config.yml` |
| 디자인 | `assets/css/style.css` |

---

## 주의

모든 글은 AI가 생성한 초안입니다. 사실 확인이 필요한 내용은 각 글 하단의 **참고 자료**와
1차 자료를 반드시 확인하세요.
