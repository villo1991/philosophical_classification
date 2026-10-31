"""Validate this publication using only the standard library; never uses a model."""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


class Document(HTMLParser):
    def __init__(self, text: str):
        super().__init__(convert_charrefs=True)
        self.refs: list[tuple[str, str]] = []
        self.anchors: set[str] = set()
        self.feed(text)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        for key in ('id', 'name'):
            if attrs.get(key):
                self.anchors.add(attrs[key])
        for key in ('href', 'src', 'poster', 'data', 'xlink:href'):
            if attrs.get(key):
                kind = 'link' if tag == 'a' and key == 'href' else 'asset'
                self.refs.append((attrs[key], kind))
        if attrs.get('srcset'):
            self.refs.extend((item.strip().split()[0], 'asset') for item in attrs['srcset'].split(','))
        if tag == 'meta' and attrs.get('http-equiv', '').lower() == 'refresh':
            match = re.search(r'url\s*=\s*(.*)', attrs.get('content', ''), re.I)
            if match:
                self.refs.append((match.group(1).strip('"\''), 'link'))
        for item in re.findall(r'url\(\s*[\'"]?([^\)\'"\s]+)', attrs.get('style', '')):
            self.refs.append((item, 'asset'))


def markdown(text):
    text = re.sub(r'```.*?```', '', text, flags=re.S)
    refs = [(m, 'link') for m in re.findall(r'!?\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)', text)]
    definitions = dict(re.findall(r'^\s*\[([^\]]+)\]:\s*(\S+)', text, re.M))
    refs.extend((definitions[key], 'link') for key in re.findall(r'\[[^\]]+\]\[([^\]]+)\]', text) if key in definitions)
    anchors = set()
    counts = {}
    for heading in re.findall(r'^#{1,6}\s+(.+)$', text, re.M):
        slug = re.sub(r'[^\w\- ]', '', heading.lower()).replace(' ', '-')
        occurrence = counts.get(slug, 0)
        counts[slug] = occurrence + 1
        anchors.add(slug + (f'-{occurrence}' if occurrence else ''))
    return refs, anchors


def check(root: Path) -> dict:
    root = root.resolve()
    errors = []
    files = sorted(p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    documents = {}
    edges = {}
    references = 0
    for path in files:
        if path.suffix.lower() == '.html':
            parsed = Document(path.read_text(encoding='utf-8'))
            documents[path] = (parsed.refs, parsed.anchors)
        elif path.suffix.lower() == '.md':
            documents[path] = markdown(path.read_text(encoding='utf-8'))
        elif path.suffix.lower() == '.css':
            documents[path] = ([(s, 'asset') for s in re.findall(r'url\(\s*[\'"]?([^\)\'"\s]+)', path.read_text())], set())
    def problem(path, message):
        errors.append(f'{path.relative_to(root).as_posix()}: {message}')
    def resolve(path, ref, kind='link'):
        nonlocal references
        references += 1
        url = urlsplit(ref)
        if url.scheme in ('http', 'https'):
            if url.hostname in ('localhost', '127.0.0.1', '::1'):
                problem(path, 'local-service reference')
            elif kind == 'asset':
                problem(path, 'network-dependent asset: ' + ref)
            return
        if url.scheme == 'data':
            return
        if url.scheme or url.netloc or ref.startswith('/'):
            problem(path, 'nonportable reference: ' + ref)
            return
        target = (path.parent / unquote(url.path)).resolve() if url.path else path
        if not target.is_relative_to(root):
            problem(path, 'reference escapes publication: ' + ref)
            return
        if target.is_dir():
            target = target / 'index.html'
        if not target.is_file():
            problem(path, 'missing reference: ' + ref)
            return
        edges.setdefault(path, set()).add(target)
        if url.fragment:
            if target not in documents:
                if target.suffix.lower() in ('.html', '.md'):
                    problem(path, 'fragment target was not parsed: ' + ref)
            elif unquote(url.fragment) not in documents[target][1]:
                problem(path, 'missing anchor: ' + ref)
    for path, (refs, _) in documents.items():
        for ref, kind in refs:
            resolve(path, ref, kind)
    # JSON paths below are actionable publication references. Historical artifact
    # identifiers and hashes are provenance values, not links to the old checkout.
    refkeys = {'matrix_file', 'results_file', 'text_file', 'source_canonical_file',
               'canonical_file', 'ledger_file', 'profile_file', 'notice_file',
               'mappings_file', 'publication_file', 'identity_file', 'html_file',
               'parameters_file', 'coordinates_file', 'cosine_file', 'neighbors_file',
               'browser_checks_file', 'file'}
    def walk_json(path, value, parent=''):
        if isinstance(value, dict):
            for key, item in value.items():
                if isinstance(item, str) and (key in refkeys or parent == 'matrices'):
                    resolve(path, item, 'link')
                else:
                    walk_json(path, item, key)
        elif isinstance(value, list):
            for item in value:
                if parent == 'screenshots' and isinstance(item, str):
                    resolve(path, item, 'asset')
                else:
                    walk_json(path, item, parent)
    for path in files:
        if path.suffix == '.json':
            try:
                walk_json(path, json.loads(path.read_text()))
            except (ValueError, OSError) as exc:
                problem(path, 'invalid JSON: ' + str(exc))
    # Scan readable derivatives too, rather than checking only the landing page.
    privacy_files = 0
    email = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}')
    personal_path = re.compile(r'/(?:home|Users)/[A-Za-z0-9_.-]+/')
    for path in files:
        if path.suffix not in ('.html', '.md', '.json', '.txt', '.csv', '.py', '.css', '.js'):
            continue
        if path.relative_to(root).as_posix() == 'assets/plotly.min.js':
            # Exact third-party bundle, including generic protocol-handling code.
            # It contains no actual file URL asset dependency; DOM refs are checked.
            continue
        text = path.read_text(encoding='utf-8')
        privacy_files += 1
        if personal_path.search(text):
            problem(path, 'personal absolute path remains')
        if email.search(text):
            problem(path, 'email address remains')
        # This checker and browser harness necessarily describe the file protocol.
        if path.suffix not in ('.py',) and re.search(r'file:/{2}', text):
            problem(path, 'file URL remains in a derivative')
    start = root / 'CORPUS_REPORT.html'
    reached = set()
    pending = deque([start])
    while pending:
        path = pending.popleft()
        if path not in reached:
            reached.add(path)
            pending.extend(edges.get(path, ()))
    plots = set((root / 'visualizations').glob('*.html'))
    for path in plots - reached:
        problem(path, 'plot is unreachable from main report')
    result_dir = root / 'results/catalog60_8192_v2'
    summary = json.loads((result_dir / 'summary.json').read_text())
    chapters = json.loads((result_dir / 'chapters.json').read_text())['rows']
    works = json.loads((result_dir / 'works.json').read_text())['rows']
    groups = json.loads((result_dir / 'philosophers.json').read_text())['rows']
    sources = json.loads((root / 'catalog/sources.json').read_text())['sources']
    counts = {'source_documents': len(sources), 'works': len(works), 'attribution_groups': len(groups),
              'native_unit_vectors': len(chapters), 'windows': sum(u['windows'] for u in chapters)}
    expected = dict(source_documents=60, works=153, attribution_groups=35, native_unit_vectors=1731, windows=1996)
    if counts != expected or summary['vectors'] != len(chapters):
        errors.append('Exported catalog/report counts disagree')
    if len({s['id'] for s in sources}) != 60 or len({w['id'] for w in works}) != 153:
        errors.append('Duplicate source/work identities')
    return {'status': 'passed' if not errors else 'failed', 'checked_documents': len(documents),
            'checked_references': references, 'privacy_scanned_files': privacy_files,
            'reachable_plot_files': len(plots & reached), 'plot_files': len(plots),
            'counts': counts, 'errors': errors,
            'vendor_exception': 'Unmodified Plotly contains generic protocol strings, not external asset references.',
            'network_requests': 0, 'inference_requests': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = check(args.root)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['status'] == 'passed' else 1


if __name__ == '__main__':
    sys.exit(main())
