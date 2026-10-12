#!/usr/bin/env python3
"""Build and publish Chirpy from a verified master snapshot; never force-push."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from html.parser import HTMLParser

SOURCE_PATHS = [':(glob)DailyEpoch/*.md', 'chirpy-src', 'Gemfile', 'Gemfile.lock', '.github']
POST_GLOB = '20??-??-??.md'
PRIVATE_MARKERS = re.compile(r'\ue200(?:cite|filecite|navlist|filenavlist|url)\ue202|turn\d+(?:search|view|file)\d+')
BASE_URL = 'https://dawn2034.github.io'


def run(args: list[str], cwd: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ, JEKYLL_ENV='production')
    if (cwd / 'Gemfile').exists():
        env['BUNDLE_GEMFILE'] = str(cwd / 'Gemfile')
    p = subprocess.run(args, cwd=cwd, env=env, text=True,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode and check:
        raise RuntimeError(f"COMMAND_FAILED exit={p.returncode}: {' '.join(args)}\n{p.stdout}")
    return p


def prepare(root: Path) -> None:
    posts = root / 'chirpy-src/_posts'
    shutil.rmtree(posts, ignore_errors=True)
    posts.mkdir(parents=True)
    sources = sorted((root / 'DailyEpoch').glob(POST_GLOB))
    if not sources:
        raise RuntimeError('NO_DAILY_SOURCES')
    for src in sources:
        shutil.copyfile(src, posts / f'{src.stem}-dailyepoch.md')
    for src in (root / 'chirpy-src/legacy-posts').glob('*.md'):
        shutil.copyfile(src, posts / src.name)
    for path in posts.glob('*.md'):
        text = path.read_text(encoding='utf-8')
        if not text.startswith('---\n') or '\n---\n' not in text[4:]:
            continue
        end = text.index('\n---\n', 4)
        front = text[4:end].replace('AutoResearch', 'Autoresearch').replace('autoresearch', 'Autoresearch')
        match = re.search(r'^date:\s*(.+?)\s*$', front, flags=re.M)
        if match:
            raw = match.group(1).strip().strip('"\'')
            try:
                stamp = datetime.strptime(raw, '%Y-%m-%d %H:%M:%S %z')
                now = datetime.now(stamp.tzinfo)
                if stamp.date() == now.date() and stamp > now:
                    front = re.sub(r'^date:\s*.+?\s*$',
                                   'date: ' + stamp.strftime('%Y-%m-%d 00:00:00 %z'),
                                   front, count=1, flags=re.M)
            except ValueError:
                pass
        path.write_text('---\n' + front + text[end:], encoding='utf-8')


def build(root: Path, site: Path) -> None:
    p = run(['bundle', 'exec', 'jekyll', 'build', '--source', 'chirpy-src',
             '--destination', str(site)], root)
    print(p.stdout)
    if 'Conflict: The following destination is shared by multiple files' in p.stdout:
        raise RuntimeError('DESTINATION_COLLISION')


class Canonical(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = dict(attrs)
        if tag == 'link' and 'canonical' in (a.get('rel') or '').split():
            self.urls.append(a.get('href') or '')


def validate(root: Path, site: Path) -> None:
    required = ['index.html', 'assets/css/jekyll-theme-chirpy.css',
                'assets/js/dist/theme.min.js', 'DailyEpoch/index.html',
                '2018/09/03/2018年暑期（05.21-08.10）实习总结/index.html']
    for name in required:
        if not (site / name).is_file():
            raise RuntimeError(f'MISSING_STATIC_FILE: {name}')
    sources = sorted((root / 'DailyEpoch').glob(POST_GLOB))
    pages = list((site / 'DailyEpoch').glob('20??-??-??/index.html'))
    if not sources or len(sources) != len(pages):
        raise RuntimeError(f'POST_COUNT_MISMATCH sources={len(sources)} html={len(pages)}')
    index = (root / 'DailyEpoch/index.md').read_text(encoding='utf-8')
    dates = re.findall(r'^- \[(20\d\d-\d\d-\d\d)\]\(', index, flags=re.M)
    if dates != sorted(set(dates), reverse=True):
        raise RuntimeError('INDEX_DUPLICATED_OR_OUT_OF_ORDER')
    for source in sources:
        date = source.stem
        text = source.read_text(encoding='utf-8')
        if PRIVATE_MARKERS.search(text):
            raise RuntimeError(f'INTERNAL_CITATION_MARKER: {source.name}')
        if date not in dates:
            raise RuntimeError(f'MISSING_INDEX_ENTRY: {date}')
        page = site / 'DailyEpoch' / date / 'index.html'
        if not page.is_file():
            raise RuntimeError(f'MISSING_DAILY_PAGE: {date}')
        parser = Canonical()
        parser.feed(page.read_text(encoding='utf-8'))
        if parser.urls != [f'{BASE_URL}/DailyEpoch/{date}/']:
            raise RuntimeError(f'CANONICAL_MISMATCH: {date}: {parser.urls}')
    for source in (root / 'chirpy-src/legacy-posts').glob('*.md'):
        text = source.read_text(encoding='utf-8')
        if text.startswith('---\n') and '\n---\n' in text[4:]:
            front = text[4:text.index('\n---\n', 4)]
            m = re.search(r'^permalink:\s*(.+?)\s*$', front, flags=re.M)
            if m:
                path = m.group(1).strip('"\'').lstrip('/')
                if not (site / path / 'index.html').is_file():
                    raise RuntimeError(f'MISSING_LEGACY_PAGE: {source.name}')
    if '鸣响的杯子' not in (site / 'index.html').read_text(encoding='utf-8'):
        raise RuntimeError('HOME_TITLE_MISSING')
    if 'DailyEpoch' not in (site / 'DailyEpoch/index.html').read_text(encoding='utf-8'):
        raise RuntimeError('DAILY_INDEX_TITLE_MISSING')
    for ext in ('*.html', '*.xml', '*.json'):
        for path in site.rglob(ext):
            if '/chirpy-preview/' in path.read_text(encoding='utf-8'):
                raise RuntimeError(f'STALE_PREVIEW_URL: {path}')
    print(f'Validated {len(sources)} DailyEpoch pages, index and canonical URLs.')


def input_changed(root: Path, before: str, after: str) -> bool:
    p = run(['git', 'diff', '--quiet', before, after, '--', *SOURCE_PATHS], root, check=False)
    if p.returncode not in (0, 1):
        raise RuntimeError(f'INPUT_COMPARISON_FAILED: {p.stdout}')
    return p.returncode == 1


def retryable_push(output: str) -> bool:
    return bool(re.search(r'non-fast-forward|fetch first', output, flags=re.I))


def publish(root: Path, site: Path) -> None:
    built_sha = os.environ.get('BUILD_SOURCE_SHA')
    if not built_sha:
        raise RuntimeError('BUILD_SOURCE_SHA_REQUIRED')
    run(['git', 'config', 'user.name', 'github-actions[bot]'], root)
    run(['git', 'config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com'], root)
    # A worktree is always based on the latest remote head. Retry only genuine
    # non-fast-forward races, never permission/security/branch-policy failures.
    for attempt in range(1, 4):
        run(['git', 'fetch', 'origin', 'master'], root)
        parent = run(['git', 'rev-parse', 'origin/master'], root).stdout.strip()
        with tempfile.TemporaryDirectory(prefix='chirpy-publish-') as tmp:
            checkout = Path(tmp) / 'checkout'
            run(['git', 'worktree', 'add', '--detach', str(checkout), parent], root)
            try:
                artifact = site
                build_sha = built_sha
                if input_changed(root, built_sha, parent):
                    print(f'SOURCE_ADVANCED: rebuilding latest {parent} (attempt {attempt})')
                    print(run(['bundle', 'install', '--jobs', '4', '--retry', '2'], checkout).stdout)
                    prepare(checkout)
                    artifact = Path(tmp) / 'site'
                    build(checkout, artifact)
                    validate(checkout, artifact)
                    build_sha = parent
                    run(['git', 'restore', '--source=HEAD', '--staged', '--worktree', '--', 'chirpy-src'], checkout)
                    run(['git', 'clean', '-fd', '--', 'chirpy-src/_posts'], checkout)
                # Keep all repository-owned sources. Never copy old Markdown back.
                excludes = ['.git', '.git/', '.github/', 'chirpy-src/',
                            'DailyEpoch/*.md', 'Gemfile', 'Gemfile.lock', 'README.md']
                run(['rsync', '-a', '--delete',
                     *[f'--exclude={x}' for x in excludes],
                     str(artifact) + '/', str(checkout) + '/'], root)
                (checkout / '.nojekyll').touch()
                receipt = {
                    'status': 'published', 'source_sha': parent,
                    'build_source_sha': build_sha,
                    'trigger_sha': os.environ.get('TRIGGER_HEAD_SHA', ''),
                    'event': os.environ.get('GITHUB_EVENT_NAME', ''),
                    'run_id': os.environ.get('GITHUB_RUN_ID', ''),
                    'run_url': f"https://github.com/{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}",
                    'published_at': datetime.now(timezone.utc).isoformat(),
                    'posts': {p.stem: hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in sorted((checkout / 'DailyEpoch').glob(POST_GLOB))}
                }
                (checkout / 'DailyEpoch/publish-status.json').write_text(
                    json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                run(['git', 'add', '-A'], checkout)
                # Ensure generated-site synchronization did not alter any source.
                p = run(['git', 'diff', '--cached', '--quiet', '--', *SOURCE_PATHS], checkout, check=False)
                if p.returncode:
                    raise RuntimeError('PUBLISH_WOULD_MODIFY_SOURCE')
                run(['git', 'commit', '-m', 'Publish Chirpy site', '-m',
                     f"Source-SHA: {parent}\nBuild-SHA: {build_sha}\nTrigger-SHA: {receipt['trigger_sha']}\nRun: {receipt['run_url']}"], checkout)
                push = run(['git', 'push', 'origin', 'HEAD:master'], checkout, check=False)
                print(push.stdout)
                if push.returncode == 0:
                    sha = run(['git', 'rev-parse', 'HEAD'], checkout).stdout.strip()
                    print(f'PUBLISHED_COMMIT_SHA={sha}')
                    summary = os.environ.get('GITHUB_STEP_SUMMARY')
                    if summary:
                        with open(summary, 'a', encoding='utf-8') as f:
                            f.write(f"## Verified Chirpy publication\n\nSource: `{parent}`\n\nPublication: `{sha}`\n\nRun: {receipt['run_url']}\n\nPages: {len(receipt['posts'])}\n")
                    return
                if not retryable_push(push.stdout):
                    raise RuntimeError(f'PUSH_REJECTED exit={push.returncode}; no retry: {push.stdout}')
                print(f'NON_FAST_FORWARD: refetching and revalidating (attempt {attempt})')
            finally:
                run(['git', 'worktree', 'remove', '--force', str(checkout)], root, check=False)
    raise RuntimeError('MASTER_CHANGED_REPEATEDLY: exhausted 3 safe attempts; no force-push')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'build', 'validate', 'publish'])
    parser.add_argument('--site', default='_site')
    args = parser.parse_args()
    root = Path.cwd().resolve()
    site = Path(args.site).resolve()
    try:
        if args.phase == 'prepare':
            prepare(root)
        else:
            globals()[args.phase](root, site)
    except Exception as exc:
        print(f'::error::{args.phase.upper()}_FAILED: {exc}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
