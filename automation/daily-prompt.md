# 매일 실행되는 지시서 (Claude Code Routine)

이 파일은 매일 예약 실행되는 Claude Code 세션이 그대로 따르는 작업 지시서입니다.
글의 주제·톤·규칙을 바꾸고 싶으면 이 파일만 수정하면 됩니다.

## 목표
AI 모션캡쳐 관련 **최신 주제 2개**를 웹에서 찾아, 한국어 블로그 글 2편을 **초안**으로 작성한다.
⚠️ **사이트에 바로 발행하지 않는다.** 초안 브랜치를 만들어 push 하면, GitHub Actions가 PR을 만들고
텔레그램으로 알림을 보낸다. 사람이 PR을 **병합해야만** 발행된다.

## 작업 절차
1. 저장소 루트에서 작업한다. 발행(base) 브랜치를 최신 상태로 맞춘다.
   base 브랜치는 이 파일(`automation/daily-prompt.md`)과 `_posts/`가 있는 브랜치다.
   `main`에 있으면 `main`, 없으면 `claude/ai-mocap-blog-automation-o273mo`.
   ```
   git fetch origin && git checkout <base> && git pull --ff-only origin <base>
   ```
2. `_posts/`의 기존 글 제목을 확인해 **중복 주제를 피한다**.
3. **웹 검색**으로 서로 다른 최신 주제 2개를 찾는다. 관심 분야:
   - 마커리스(markerless) 모션캡쳐, 단일/다중 카메라 3D 포즈 추정
   - 비디오→애니메이션 변환, AI 리타게팅·모션 정제
   - 실시간 아바타·버추얼 프로덕션
   - 관련 신규 논문·오픈소스·상용 도구 발표
4. 각 주제로 한국어 글을 쓴다.
   - 분량 800~1400자, 마크다운 본문(`##` 소제목 포함).
   - H1 제목은 본문에 넣지 말 것(front matter의 `title`에만).
   - 사실을 지어내지 말고, 검색으로 확인한 내용만 쓴다.
5. 각 글을 `_posts/YYYY-MM-DD-슬러그.md`로 저장한다. front matter 형식:
   ```
   ---
   layout: post
   title: "한국어 제목"
   date: 2026-07-04 09:00:00 +0900
   description: "한 줄 요약(80자 이내)"
   categories: ["기술"]
   tags: ["ai", "motion-capture", "키워드"]
   sources:
     - "https://참고1"
     - "https://참고2"
   ---

   ## 소제목

   본문...
   ```
   - 슬러그는 영문 소문자·하이픈만 사용(예: `markerless-mocap-2026`).
   - `date`는 한국시간(+0900) 기준, 오늘 날짜.
   - `sources`에는 실제로 참고한 URL 2~5개.
6. **발행하지 않는다.** base 브랜치에서 새 초안 브랜치를 만들어 그 브랜치에만 push 한다.
   ```
   git checkout -b draft/$(date +%Y-%m-%d-%H%M)
   git add _posts
   git commit -m "draft: 자동 생성 글 ($(date +%Y-%m-%d))"
   git push -u origin draft/$(date +%Y-%m-%d-%H%M)
   ```
   - base 브랜치에는 **직접 push 하지 않는다.**
   - PR을 **직접 병합하지 않는다.** (사람이 검토·승인)
7. 초안 브랜치가 push되면 끝이다. 이후 PR 생성과 텔레그램 알림은 GitHub Actions가 자동 처리한다.

## 주의
- 각 글 하단에 참고 자료가 남으므로 sources를 꼭 채운다.
- 이미 다룬 주제와 겹치면 다른 주제로 교체한다.
- 절대 base(발행) 브랜치로 직접 push 하거나 PR을 병합하지 않는다.
