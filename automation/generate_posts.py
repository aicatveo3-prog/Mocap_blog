#!/usr/bin/env python3
"""AI 모션캡쳐 주제를 웹에서 찾아 매일 2편의 한국어 블로그 글을 자동 생성한다.

- Anthropic Claude + web_search 서버 도구로 최신 주제를 찾고 본문을 작성한다.
- 결과를 Jekyll `_posts/YYYY-MM-DD-slug.md` 형식으로 저장한다.
- 이미 발행된 글의 제목/슬러그를 함께 넘겨 중복 주제를 피한다.

필요 환경변수:
  ANTHROPIC_API_KEY   (필수)  Anthropic API 키
  ANTHROPIC_MODEL     (선택)  기본값 claude-opus-4-8
  POSTS_PER_RUN       (선택)  1회 실행 시 생성할 글 수, 기본 2
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import sys
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parent.parent
POSTS_DIR = ROOT / "_posts"

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")
POSTS_PER_RUN = int(os.environ.get("POSTS_PER_RUN", "2"))

# 한국 시간 기준 날짜 (Actions 러너는 UTC 이므로 +9)
KST = _dt.timezone(_dt.timedelta(hours=9))
NOW = _dt.datetime.now(tz=KST)
TODAY = NOW.strftime("%Y-%m-%d")


def existing_titles() -> list[str]:
    """이미 있는 글의 제목을 모아 중복 주제 회피에 쓴다."""
    titles: list[str] = []
    if not POSTS_DIR.exists():
        return titles
    for md in POSTS_DIR.glob("*.md"):
        text = md.read_text(encoding="utf-8", errors="ignore")
        m = re.search(r'^title:\s*"?(.+?)"?\s*$', text, flags=re.MULTILINE)
        if m:
            titles.append(m.group(1).strip())
    return titles


def build_prompt(avoid: list[str], count: int) -> str:
    avoid_block = "\n".join(f"- {t}" for t in avoid) or "(없음)"
    return f"""당신은 AI 모션캡쳐 전문 테크 블로거입니다.

**작업**: 웹 검색을 사용해 'AI 모션캡쳐'와 직접 관련된 서로 다른 최신 주제 {count}개를 찾아,
각각에 대해 완성도 높은 한국어 블로그 글을 작성하세요.

**관심 분야 예시**: 마커리스(markerless) 모션캡쳐, 단일/다중 카메라 기반 3D 포즈 추정,
비디오→애니메이션 변환, AI 리타게팅·모션 정제, 실시간 아바타·버추얼 프로덕션,
관련 신규 논문/오픈소스/상용 도구 발표.

**규칙**:
1. web_search 도구로 실제 최신 정보를 조사한 뒤 작성하세요. 사실을 지어내지 마세요.
2. 아래 '이미 다룬 주제'와 중복되지 않는 새로운 주제를 고르세요.
3. 각 글은 한국어로, 800~1400자 분량, 마크다운 본문(## 소제목 포함)으로 작성하세요.
   제목(H1)은 본문에 넣지 말고 title 필드에만 넣으세요.
4. 각 글에 참고한 실제 URL을 sources 배열에 2~5개 담으세요.
5. slug 는 영문 소문자와 하이픈만 사용하세요(예: markerless-mocap-2026).

**이미 다룬 주제(피할 것)**:
{avoid_block}

**출력 형식**: 다른 설명 없이, 마지막에 아래 JSON을 하나의 ```json 코드블록으로만 출력하세요.

```json
{{
  "posts": [
    {{
      "slug": "english-hyphen-slug",
      "title": "한국어 제목",
      "description": "한 줄 요약(80자 이내)",
      "category": "카테고리(예: 기술, 도구, 논문)",
      "tags": ["ai", "motion-capture", "키워드"],
      "body_markdown": "## 소제목\\n\\n본문...",
      "sources": ["https://...", "https://..."]
    }}
  ]
}}
```
"""


def call_claude(prompt: str) -> str:
    client = anthropic.Anthropic()  # ANTHROPIC_API_KEY 환경변수 사용
    # 2편 분량 + 검색이라 출력이 길 수 있으므로 스트리밍 사용.
    with client.messages.stream(
        model=MODEL,
        max_tokens=32000,
        thinking={"type": "adaptive"},
        output_config={"effort": "high"},
        tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": 8}],
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        final = stream.get_final_message()

    # 최종 답변의 모든 text 블록을 이어붙인다(검색 결과 블록은 무시).
    parts = [b.text for b in final.content if getattr(b, "type", None) == "text"]
    return "\n".join(parts)


def extract_json(text: str) -> dict:
    """모델 출력에서 JSON 오브젝트를 추출한다."""
    # 1) ```json ... ``` 코드블록 우선
    fence = re.search(r"```json\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    candidate = fence.group(1) if fence else None
    # 2) 없으면 첫 '{' 부터 마지막 '}' 까지
    if candidate is None:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1:
            raise ValueError("모델 출력에서 JSON을 찾지 못했습니다.\n" + text[:500])
        candidate = text[start : end + 1]
    return json.loads(candidate)


def slugify(slug: str, fallback: str) -> str:
    s = re.sub(r"[^a-z0-9-]+", "-", (slug or "").lower()).strip("-")
    if not s:
        s = re.sub(r"[^a-z0-9-]+", "-", fallback.lower()).strip("-") or "post"
    return s[:60]


def unique_path(date: str, slug: str) -> Path:
    path = POSTS_DIR / f"{date}-{slug}.md"
    i = 2
    while path.exists():
        path = POSTS_DIR / f"{date}-{slug}-{i}.md"
        i += 1
    return path


def yaml_escape(value: str) -> str:
    return '"' + str(value).replace("\\", "\\\\").replace('"', '\\"') + '"'


def write_post(post: dict, when: _dt.datetime) -> Path:
    slug = slugify(post.get("slug", ""), post.get("title", "post"))
    title = post.get("title", "제목 없음").strip()
    description = post.get("description", "").strip()
    category = post.get("category", "기타").strip()
    tags = post.get("tags") or []
    sources = post.get("sources") or []
    body = (post.get("body_markdown") or "").strip()

    tags_yaml = "[" + ", ".join(yaml_escape(t) for t in tags) + "]"
    cats_yaml = "[" + yaml_escape(category) + "]"
    src_lines = "".join(f"\n  - {yaml_escape(s)}" for s in sources)

    front = (
        "---\n"
        "layout: post\n"
        f"title: {yaml_escape(title)}\n"
        f"date: {when.strftime('%Y-%m-%d %H:%M:%S %z')}\n"
        f"description: {yaml_escape(description)}\n"
        f"categories: {cats_yaml}\n"
        f"tags: {tags_yaml}\n"
        f"sources:{src_lines if sources else ' []'}\n"
        "---\n\n"
    )

    path = unique_path(when.strftime("%Y-%m-%d"), slug)
    path.write_text(front + body + "\n", encoding="utf-8")
    return path


def main() -> int:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY 환경변수가 설정되지 않았습니다.", file=sys.stderr)
        return 1

    POSTS_DIR.mkdir(exist_ok=True)
    avoid = existing_titles()
    print(f"[i] 모델={MODEL}, 생성 개수={POSTS_PER_RUN}, 기존 글={len(avoid)}편")

    prompt = build_prompt(avoid, POSTS_PER_RUN)
    raw = call_claude(prompt)
    data = extract_json(raw)

    posts = data.get("posts", [])
    if not posts:
        print("ERROR: 생성된 글이 없습니다.", file=sys.stderr)
        return 1

    # 여러 글이 같은 분:초를 갖지 않도록 시간 간격을 둔다.
    created = []
    for idx, post in enumerate(posts[:POSTS_PER_RUN]):
        when = NOW - _dt.timedelta(minutes=idx)
        path = write_post(post, when)
        created.append(path)
        print(f"[+] 생성: {path.relative_to(ROOT)}  ({post.get('title', '')})")

    print(f"[✓] 총 {len(created)}편 생성 완료.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
