# AI 모션캡쳐 랩 🎥🤖

AI 기반 모션캡쳐 기술을 **매일 두 편씩 자동으로** 찾아 글을 쓰고 발행하는 블로그입니다.

- **콘텐츠 생성**: Claude(Anthropic) + 웹 검색으로 최신 주제 조사 후 한국어 글 작성
- **스케줄러**: GitHub Actions cron (매일 1회, 2편 생성)
- **발행**: Git 커밋 → GitHub Pages(Jekyll) 자동 배포

```
매일 06:00 KST  →  Claude가 주제 2개 검색  →  글 2편 작성  →  _posts/에 커밋  →  Pages 자동 배포
```

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
├── automation/
│   ├── generate_posts.py       # 글 생성 스크립트
│   └── requirements.txt
└── .github/workflows/
    └── daily-posts.yml         # 매일 실행되는 자동화
```

---

## 처음 설정 (한 번만)

### 1. Anthropic API 키 발급
[console.anthropic.com](https://console.anthropic.com) 에서 API 키를 만듭니다.
글 1편당 보통 수십~수백 원 수준의 비용이 듭니다(모델·길이에 따라 다름).

### 2. 저장소 시크릿 등록
저장소 → **Settings → Secrets and variables → Actions → New repository secret**

| 이름 | 값 |
|---|---|
| `ANTHROPIC_API_KEY` | 발급받은 API 키 |

(선택) 모델을 바꾸려면 **Variables** 탭에서 `ANTHROPIC_MODEL` 변수를 추가하세요.
기본값은 `claude-opus-4-8` 입니다. 비용을 낮추려면 `claude-sonnet-5` 등을 쓸 수 있습니다.

### 3. GitHub Pages 켜기
저장소 → **Settings → Pages**
- **Source**: `Deploy from a branch`
- **Branch**: `main` / `/ (root)` → **Save**

잠시 뒤 `https://<사용자명>.github.io/<저장소명>/` 에서 사이트가 열립니다.

> 이 저장소가 사용자 페이지가 아니라 프로젝트 페이지라면(`.../저장소명/` 형태),
> `_config.yml` 의 `baseurl` 을 `"/저장소명"`, `url` 을 `"https://<사용자명>.github.io"` 로
> 설정하면 링크가 정확해집니다.

### 4. 자동화 확인
저장소 → **Actions → 매일 AI 모션캡쳐 글 자동 생성 → Run workflow** 로 지금 바로 한 번 실행해
글 2편이 생성·커밋되는지 확인하세요. 이후에는 매일 자동으로 실행됩니다.

---

## 로컬에서 미리보기 (선택)

```bash
# 사이트 미리보기 (Ruby/Jekyll 필요)
bundle install
bundle exec jekyll serve      # http://localhost:4000

# 글 생성 스크립트 직접 실행 (Python 3.10+)
pip install -r automation/requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python automation/generate_posts.py
```

---

## 커스터마이즈

| 하고 싶은 것 | 바꿀 곳 |
|---|---|
| 실행 시각 변경 | `.github/workflows/daily-posts.yml` 의 `cron` |
| 하루 생성 편수 | 워크플로의 `POSTS_PER_RUN` |
| 다루는 주제·글 톤 | `automation/generate_posts.py` 의 `build_prompt()` |
| 사이트 제목·소개 | `_config.yml` |
| 디자인 | `assets/css/style.css` |

---

## 주의

모든 글은 AI가 생성한 초안입니다. 사실 확인이 필요한 내용은 각 글 하단의 **참고 자료**와
1차 자료를 반드시 확인하세요.
