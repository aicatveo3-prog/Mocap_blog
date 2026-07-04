#!/usr/bin/env python3
# ─────────────────────────────────────────────────────────────
# 초안 미리보기 빌더
# Jekyll 로 빌드된 _site 에서, 이번 초안에 새로 추가/수정된 글 페이지를
# "CSS 까지 안에 박은 자체 완결형 HTML" 로 변환한다.
# 어떤 브라우저/폰에서 열어도 실제 사이트와 동일하게 보이고, 외부 의존이 없다.
#
# 사용:
#   python build_preview.py --site _site --css _site/assets/css/style.css \
#     --siteurl https://aicatveo3-prog.github.io/Mocap_blog \
#     --out preview_out --pr 3 --posts "_posts/2026-07-04-a.md _posts/2026-07-04-b.md"
#
# 표준출력으로 "슬러그<TAB>상대경로" 를 한 줄씩 찍는다(워크플로우가 링크를 만든다).
# ─────────────────────────────────────────────────────────────
import argparse
import glob
import os
import re
import sys
import html as htmllib

BANNER = (
    '<div style="position:sticky;top:0;z-index:9999;'
    'background:#0d9488;color:#fff;text-align:center;'
    'padding:10px 14px;font:600 14px/1.4 system-ui,-apple-system,sans-serif">'
    '👀 미리보기(초안) — 아직 발행되지 않았습니다. 승인해야 사이트에 올라갑니다.'
    '</div>'
)


def slug_of(post_path: str) -> str:
    """_posts/2026-07-04-my-slug.md -> my-slug"""
    base = os.path.basename(post_path)
    base = re.sub(r"\.md$", "", base)
    # 앞의 YYYY-MM-DD- 제거
    return re.sub(r"^\d{4}-\d{2}-\d{2}-", "", base)


def find_built_html(site_dir: str, slug: str):
    """_site 안에서 이 슬러그의 빌드 결과 HTML 을 찾는다."""
    hits = glob.glob(os.path.join(site_dir, "**", slug, "index.html"), recursive=True)
    if not hits:
        # permalink 가 다를 수 있으니 <slug>.html 도 시도
        hits = glob.glob(os.path.join(site_dir, "**", slug + ".html"), recursive=True)
    return hits[0] if hits else None


def make_self_contained(html: str, css: str, siteurl: str) -> str:
    # 1) 스타일시트 <link> 를 인라인 <style> 로 치환
    html = re.sub(
        r'<link[^>]+rel=["\']stylesheet["\'][^>]*>',
        "<style>\n" + css + "\n</style>",
        html,
        count=1,
    )
    # 2) 남은 /baseurl/ 상대경로를 절대 URL 로 (nav·RSS·홈 링크가 살아있게)
    base = siteurl.rstrip("/")
    # href="/Mocap_blog/..."  '/Mocap_blog' 부분만 정확히 치환
    path_prefix = "/" + base.split("/", 3)[-1] if base.count("/") >= 3 else ""
    if path_prefix and path_prefix != "/":
        html = html.replace('="' + path_prefix + '/', '="' + base + '/')
        html = html.replace("='" + path_prefix + "/", "='" + base + "/")
    # 3) 상단 미리보기 배너 삽입
    html = re.sub(r"(<body[^>]*>)", r"\1\n" + BANNER, html, count=1)
    return html


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", required=True)
    ap.add_argument("--css", required=True)
    ap.add_argument("--siteurl", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pr", required=True)
    ap.add_argument("--posts", required=True, help="공백으로 구분된 _posts/*.md 목록")
    args = ap.parse_args()

    try:
        with open(args.css, encoding="utf-8") as f:
            css = f.read()
    except OSError:
        css = ""  # CSS 를 못 읽어도 최소한 내용은 보이게

    out_dir = os.path.join(args.out, "pr-" + str(args.pr))
    os.makedirs(out_dir, exist_ok=True)

    posts = [p for p in args.posts.split() if p.strip()]
    entries = []  # (slug, title, relpath)

    for post in posts:
        slug = slug_of(post)
        built = find_built_html(args.site, slug)
        if not built:
            print("WARN: 빌드 결과를 못 찾음: " + slug, file=sys.stderr)
            continue
        with open(built, encoding="utf-8") as f:
            page = f.read()
        # 제목 추출(배너/목록용)
        m = re.search(r"<h1[^>]*>(.*?)</h1>", page, re.S)
        title = htmllib.unescape(re.sub(r"<[^>]+>", "", m.group(1)).strip()) if m else slug
        page = make_self_contained(page, css, args.siteurl)
        rel = "pr-" + str(args.pr) + "/" + slug + ".html"
        with open(os.path.join(out_dir, slug + ".html"), "w", encoding="utf-8") as f:
            f.write(page)
        entries.append((slug, title, rel))

    # 목록 페이지(초안 여러 편을 한 곳에서)
    if entries:
        items = "".join(
            '<li style="margin:10px 0"><a href="./' + slug + '.html">'
            + htmllib.escape(title) + "</a></li>"
            for slug, title, _ in entries
        )
        index = (
            "<!doctype html><meta charset=utf-8>"
            "<meta name=viewport content='width=device-width,initial-scale=1'>"
            "<title>초안 미리보기 PR #" + str(args.pr) + "</title>"
            + BANNER
            + "<div style='max-width:680px;margin:24px auto;padding:0 18px;"
            "font:16px/1.6 system-ui,-apple-system,sans-serif'>"
            "<h2>오늘의 초안 " + str(len(entries)) + "편</h2><ul>"
            + items
            + "</ul></div>"
        )
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(index)

    # 워크플로우가 읽을 결과 출력
    for slug, title, rel in entries:
        print(slug + "\t" + title + "\t" + rel)


if __name__ == "__main__":
    main()
