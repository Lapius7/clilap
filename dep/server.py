#!/usr/bin/env python3
"""Dependency visualizer server for clilap.org — npm package.json dependency trees on port 3217."""

import json, os, re, secrets, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from urllib.request import urlopen, Request
from urllib.error import URLError

PORT = 3217
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

MAX_PACKAGES = 150
MAX_DEPTH    = 6
FETCH_TIMEOUT = 3
TOTAL_BUDGET = 25  # seconds, hard cap on total resolution time

BROWSER_KEYS = ('mozilla', 'webkit', 'trident', 'opera')
def is_browser(ua): return any(k in ua.lower() for k in BROWSER_KEYS)

# ANSI
R  = '\x1b[0m'
D  = '\x1b[2m'
C  = '\x1b[36m'
BC = '\x1b[1;36m'
BW = '\x1b[1;37m'
DC = '\x1b[2;36m'
BR = '\x1b[1;31m'
BG = '\x1b[1;32m'
BY = '\x1b[1;33m'

_A2H = {
    '1':'font-weight:bold','2':'color:#5c6370',
    '36':'color:#56b6c2','1;31':'color:#e06c75;font-weight:bold',
    '1;32':'color:#98c379;font-weight:bold','1;33':'color:#e5c07b;font-weight:bold',
    '1;36':'color:#61afef;font-weight:bold','1;37':'color:#abb2bf;font-weight:bold',
    '2;36':'color:#4b8ea8',
}

def ansi_to_html(text):
    out, depth, i = [], 0, 0
    while i < len(text):
        if text[i] == '\x1b' and i+1 < len(text) and text[i+1] == '[':
            j = text.find('m', i+2)
            if j == -1: i += 2; continue
            code = text[i+2:j]; i = j+1
            if code == '0':
                out.extend(['</span>'] * depth); depth = 0
            elif code in _A2H:
                out.append(f'<span style="{_A2H[code]}">'); depth += 1
        else:
            out.append({'&':'&amp;','<':'&lt;','>':'&gt;'}.get(text[i], text[i])); i += 1
    out.extend(['</span>'] * depth)
    return ''.join(out)

_CSS = ('*{box-sizing:border-box;margin:0;padding:0}'
        'body{background:#000;color:#aaa;font-family:"Courier New",Consolas,Monaco,monospace;'
        'font-size:12px;line-height:1.5;padding:16px}'
        'pre{font-family:inherit;white-space:pre;margin:0;overflow-x:auto}'
        'a{color:#4ec9b0;text-decoration:none}a:hover{text-decoration:underline}'
        '.nav{margin-bottom:14px;display:flex;gap:8px;flex-wrap:wrap}'
        '.nav a{display:inline-block;padding:6px 14px;border:1px solid #333;border-radius:4px;color:#aaa}'
        '.nav a.active{background:#1a1a1a;color:#4ec9b0;border-color:#4ec9b0}'
        '.nav a:hover{background:#1a1a1a;text-decoration:none}')
_FOOTER = '<div style="margin-top:16px;padding-top:6px;border-top:1px solid #1a1a1a;color:#333;font-size:11px;">©2025 CLI Lap by Lapius7. All rights reserved.</div>'

def _nav_html(rid, active):
    tabs = [('', 'tree'), ('cycles', 'cycles'), ('heavy', 'heavy'), ('licenses', 'licenses')]
    links = []
    for path, label in tabs:
        href = f'/{rid}/{path}' if path else f'/{rid}'
        cls = ' class="active"' if path == active else ''
        links.append(f'<a href="{href}"{cls}>{label}</a>')
    return f'<div class="nav">{"".join(links)}</div>'

def html_wrap(ansi_text, title='dep - Clilap', rid=None, active=''):
    nav = _nav_html(rid, active) if rid else ''
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{_CSS}</style></head>'
            f'<body>{nav}<pre>{ansi_to_html(ansi_text)}</pre>{_FOOTER}</body></html>')

def sep(nc=False): return '═' * 60 if nc else DC + '═' * 60 + R
def cc(code, text, nc): return text if nc else code + text + R
def hint(text, nc): return cc(DC, '  ' + text, nc)


# ── multipart (shared pattern with tools/server.py) ────────────────────────────

def _parse_multipart(body_bytes, content_type):
    boundary_match = re.search(r'boundary=([^\s;]+)', content_type)
    if not boundary_match:
        return {}
    boundary = boundary_match.group(1).encode()
    parts = {}
    for chunk in body_bytes.split(b'--' + boundary):
        if b'Content-Disposition' not in chunk:
            continue
        header_end = chunk.find(b'\r\n\r\n')
        if header_end == -1:
            header_end = chunk.find(b'\n\n')
            if header_end == -1: continue
            sep_len = 2
        else:
            sep_len = 4
        headers_raw = chunk[:header_end].decode('utf-8', errors='replace')
        content = chunk[header_end+sep_len:].rstrip(b'\r\n--')
        name_m = re.search(r'name="([^"]+)"', headers_raw)
        if name_m:
            parts[name_m.group(1)] = content
    return parts


# ── npm registry resolution ─────────────────────────────────────────────────────

def _fetch_pkg_info(name):
    safe = name.strip()
    if not safe or safe.startswith('.'):
        return None
    url = f'https://registry.npmjs.org/{safe.replace("/", "%2F")}/latest'
    try:
        req = Request(url, headers={'User-Agent': 'clilap.org/1.0'})
        with urlopen(req, timeout=FETCH_TIMEOUT) as r:
            data = json.loads(r.read().decode('utf-8', errors='replace'))
        return {
            'name': data.get('name', safe),
            'version': data.get('version', '?'),
            'license': data.get('license') or (data.get('licenses') or [{}])[0].get('type', 'Unknown') if isinstance(data.get('licenses'), list) else (data.get('license') or 'Unknown'),
            'deps': data.get('dependencies', {}) or {},
            'unpacked_size': (data.get('dist', {}) or {}).get('unpackedSize', 0) or 0,
        }
    except (URLError, json.JSONDecodeError, TimeoutError, OSError):
        return None

def resolve_tree(root_deps, on_progress=None):
    """BFS-resolve a dependency map into a flat package table + edge list, capped."""
    packages = {}   # name -> {version, license, unpacked_size}
    edges = []      # (parent, child)
    queue = [(name, 0) for name in root_deps.keys()]
    seen_in_queue = set(root_deps.keys())
    start = time.time()

    while queue and len(packages) < MAX_PACKAGES:
        if time.time() - start > TOTAL_BUDGET:
            break
        name, depth = queue.pop(0)
        if name in packages or depth > MAX_DEPTH:
            continue
        if on_progress:
            on_progress(name, len(packages))
        info = _fetch_pkg_info(name)
        if info is None:
            packages[name] = {'version': '?', 'license': 'Unknown', 'unpacked_size': 0, 'deps': []}
            continue
        packages[name] = {
            'version': info['version'],
            'license': info['license'] if isinstance(info['license'], str) else 'Unknown',
            'unpacked_size': info['unpacked_size'],
            'deps': list(info['deps'].keys()),
        }
        for child in info['deps'].keys():
            edges.append((name, child))
            if child not in seen_in_queue and len(packages) + len(queue) < MAX_PACKAGES:
                queue.append((child, depth + 1))
                seen_in_queue.add(child)
    return packages, edges

def detect_cycles(packages):
    graph = {name: info['deps'] for name, info in packages.items()}
    visited, in_path, cycles = set(), set(), []

    def dfs(node, path):
        if node in in_path:
            idx = path.index(node)
            cycles.append(path[idx:] + [node])
            return
        if node in visited or node not in graph:
            return
        visited.add(node); in_path.add(node); path.append(node)
        for nxt in graph.get(node, []):
            dfs(nxt, path)
        path.pop(); in_path.discard(node)

    for name in graph:
        if name not in visited:
            dfs(name, [])
    return cycles


# ── ID + storage ─────────────────────────────────────────────────────────────

def new_id():
    return secrets.token_hex(3)

def save_record(record):
    rid = new_id()
    while os.path.exists(os.path.join(DATA_DIR, f'{rid}.json')):
        rid = new_id()
    with open(os.path.join(DATA_DIR, f'{rid}.json'), 'w', encoding='utf-8') as f:
        json.dump(record, f)
    return rid

def load_record(rid):
    if not re.fullmatch(r'[0-9a-f]{6,16}', rid):
        return None
    path = os.path.join(DATA_DIR, f'{rid}.json')
    if not os.path.exists(path):
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ── rendering ────────────────────────────────────────────────────────────────

def _cmd(cmd, comment, nc, width=72):
    pad = ' ' * max(1, width - len(cmd))
    return f'  {cc(BC, cmd, nc)}{pad}{cc(D, comment, nc)}'

def render_upload_help(nc):
    W = 94
    SEP = '═' * W if nc else DC + '═' * W + R
    DIV = ('  ' + '─' * (W - 2)) if nc else DC + '  ' + '─' * (W - 2) + R
    lines = [SEP,
              f'  {cc(BW, "clilap.org/dep", nc)}  {cc(D, "📦 依存関係可視化", nc)}',
              DIV,
              cc(D, '  package.json をアップロードして依存関係ツリーを解析・URLで共有します。', nc),
              '',
              cc(BY, '  アップロード', nc),
              _cmd('curl clilap.org/dep -F file=@package.json', '# ファイルをアップロード', nc),
              _cmd('cat package.json | curl clilap.org/dep -F file=@-', '# stdinから', nc),
              '',
              cc(BY, '  取得', nc),
              _cmd('curl dep.clilap.org/{id}', '# 依存関係ツリー', nc),
              _cmd('curl dep.clilap.org/{id}/cycles', '# 循環依存検出', nc),
              _cmd('curl dep.clilap.org/{id}/heavy', '# 巨大依存ランキング (?all で全件)', nc),
              _cmd('curl dep.clilap.org/{id}/licenses', '# ライセンス検査', nc),
              SEP]
    return '\n'.join(lines) + '\n'

def render_tree(root_name, root_deps, packages, nc):
    lines = [sep(nc), cc(BC, f'  {root_name}', nc), '']
    names = sorted(root_deps.keys())

    def render_node(name, prefix, is_last, depth, visited):
        connector = '└─ ' if is_last else '├─ '
        info = packages.get(name)
        if info is None:
            lines.append(prefix + cc(D, connector + name, nc))
            return
        tag = cc(D, f"@{info['version']}", nc)
        line = prefix + cc(D, connector, nc) + cc(C, name, nc) + ' ' + tag
        if name in visited:
            lines.append(line + cc(BR, '  (循環/再出現)', nc))
            return
        lines.append(line)
        if depth >= MAX_DEPTH:
            return
        children = sorted(info.get('deps', []))
        child_prefix = prefix + ('   ' if is_last else cc(D, '│  ', nc))
        for i, child in enumerate(children):
            render_node(child, child_prefix, i == len(children) - 1, depth + 1, visited | {name})

    for i, name in enumerate(names):
        render_node(name, '', i == len(names) - 1, 1, set())

    lines += ['', cc(D, f'  パッケージ数: {len(packages)}', nc), sep(nc),
              hint(f'curl dep.clilap.org/{{id}}/cycles  curl dep.clilap.org/{{id}}/heavy  curl dep.clilap.org/{{id}}/licenses', nc)]
    return '\n'.join(lines) + '\n'

def render_cycles(packages, nc):
    cycles = detect_cycles(packages)
    lines = [sep(nc), cc(BC, '  循環依存検出', nc), '']
    if not cycles:
        lines.append(cc(BG, '  循環依存は見つかりませんでした', nc))
    else:
        for cy in cycles:
            lines.append(cc(BR, '  ⚠ ' + ' → '.join(cy), nc))
        lines.append('')
        lines.append(cc(D, f'  検出数: {len(cycles)}', nc))
    lines.append(sep(nc))
    return '\n'.join(lines) + '\n'

def render_heavy(packages, nc, show_all=False):
    ranked = sorted(packages.items(), key=lambda kv: kv[1].get('unpacked_size', 0), reverse=True)
    shown = ranked if show_all else ranked[:25]
    lines = [sep(nc), cc(BC, '  巨大依存ランキング (unpacked size)', nc), '']
    for i, (name, info) in enumerate(shown, 1):
        size = info.get('unpacked_size', 0)
        size_s = f'{size/1024:.1f} KB' if size < 1024*1024 else f'{size/1024/1024:.2f} MB'
        lines.append(f'  {cc(D, f"{i:>2}.", nc)} {cc(C, name, nc):<30} {cc(BW, size_s, nc)}')
    if not show_all and len(ranked) > 25:
        lines.append(cc(D, f'  ... +{len(ranked)-25}  (全件: ?all)', nc))
    lines.append(sep(nc))
    return '\n'.join(lines) + '\n'

def render_licenses(packages, nc):
    by_license = {}
    for name, info in packages.items():
        lic = info.get('license', 'Unknown') or 'Unknown'
        by_license.setdefault(lic, []).append(name)
    permissive = {'MIT', 'ISC', 'BSD', 'BSD-2-Clause', 'BSD-3-Clause', 'Apache-2.0', '0BSD', 'CC0-1.0'}
    copyleft   = {'GPL-2.0', 'GPL-3.0', 'AGPL-3.0', 'LGPL-2.1', 'LGPL-3.0'}

    lines = [sep(nc), cc(BC, '  ライセンス検査', nc), '']
    for lic in sorted(by_license, key=lambda l: -len(by_license[l])):
        pkgs = by_license[lic]
        tag = cc(BG, lic, nc) if lic in permissive else (cc(BR, lic, nc) if lic in copyleft else cc(BY, lic, nc))
        lines.append(f'  {tag}  {cc(D, f"({len(pkgs)})", nc)}')
        for name in sorted(pkgs):
            lines.append(cc(D, f'    {name}', nc))
        lines.append('')

    flagged = [n for lic in copyleft for n in by_license.get(lic, [])]
    if flagged:
        lines.append(cc(BR, f'  ⚠ コピーレフトライセンス検出: {len(flagged)}件 (配布時の互換性に注意)', nc))
    lines.append(sep(nc))
    return '\n'.join(lines) + '\n'


# ── handler ──────────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, body, html=False, status=200):
        ct = 'text/html; charset=utf-8' if html else 'text/plain; charset=utf-8'
        self.send_response(status)
        self.send_header('Content-Type', ct)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body.encode('utf-8'))

    def _start_chunked(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Transfer-Encoding', 'chunked')
        self.send_header('X-Accel-Buffering', 'no')
        self.end_headers()

    def _write_chunk(self, text):
        data = text.encode('utf-8')
        try:
            self.wfile.write(f'{len(data):x}\r\n'.encode('ascii') + data + b'\r\n')
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            raise

    def _end_chunked(self):
        try:
            self._write_chunk('')
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _read_body(self):
        length = min(int(self.headers.get('Content-Length', 0)), 1_048_576)
        return self.rfile.read(length) if length > 0 else b''

    def _respond(self, text, browser, title='dep - Clilap', rid=None, active=''):
        if browser:
            self._send(html_wrap(text, title, rid=rid, active=active), html=True)
        else:
            self._send(text)

    def _dispatch(self, method):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        ua = self.headers.get('User-Agent', '')
        browser = is_browser(ua)
        nc = 'nocolor' in qs or 'nc' in qs

        parts = [p for p in parsed.path.split('/') if p]
        body_bytes = self._read_body() if method == 'POST' else b''

        if method == 'POST' and not parts:
            ct = self.headers.get('Content-Type', '')
            try:
                if 'multipart' in ct:
                    fields = _parse_multipart(body_bytes, ct)
                    raw = fields.get('file', b'')
                else:
                    raw = body_bytes
                if not raw:
                    self._respond(render_upload_help(nc), browser)
                    return
                pkg = json.loads(raw.decode('utf-8', errors='replace'))
                root_name = pkg.get('name', 'package')
                root_deps = {}
                root_deps.update(pkg.get('dependencies', {}) or {})
                root_deps.update(pkg.get('devDependencies', {}) or {})
                if not root_deps:
                    self._send('依存関係が見つかりません (dependencies / devDependencies が空)\n', status=400)
                    return

                if browser:
                    packages, edges = resolve_tree(root_deps)
                    for name in root_deps:
                        packages.setdefault(name, {'version': '?', 'license': 'Unknown', 'unpacked_size': 0, 'deps': []})
                    rid = save_record({'root_name': root_name, 'root_deps': list(root_deps.keys()), 'packages': packages, 'ts': time.time()})
                    lines = [sep(nc), cc(BG, '  解析完了', nc), '',
                              cc(D, '  curl:    ', nc) + cc(BW, f'curl dep.clilap.org/{rid}', nc),
                              cc(D, '  browser: ', nc) + cc(C, f'https://dep.clilap.org/{rid}', nc),
                              sep(nc)]
                    self._respond('\n'.join(lines) + '\n', browser, 'dep - 解析完了')
                    return

                self._start_chunked()
                def progress(name, count):
                    self._write_chunk(cc(D, f'  解析中... {name} ({count})\n', nc))
                packages, edges = resolve_tree(root_deps, on_progress=progress)
                for name in root_deps:
                    packages.setdefault(name, {'version': '?', 'license': 'Unknown', 'unpacked_size': 0, 'deps': []})
                rid = save_record({'root_name': root_name, 'root_deps': list(root_deps.keys()), 'packages': packages, 'ts': time.time()})
                lines = [sep(nc), cc(BG, '  解析完了', nc), '',
                          cc(D, '  curl:    ', nc) + cc(BW, f'curl dep.clilap.org/{rid}', nc),
                          cc(D, '  browser: ', nc) + cc(C, f'https://dep.clilap.org/{rid}', nc),
                          sep(nc)]
                self._write_chunk('\n'.join(lines) + '\n')
                self._end_chunked()
            except (json.JSONDecodeError, UnicodeDecodeError):
                self._send('package.json のパースに失敗しました\n', status=400)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        if method != 'GET' and not (method == 'POST'):
            self._send('Not found\n', status=404)
            return

        if not parts:
            host = self.headers.get('Host', '').split(':')[0]
            if browser and host == 'dep.clilap.org':
                self.send_response(302)
                self.send_header('Location', 'https://clilap.org/dep')
                self.end_headers()
                return
            self._respond(render_upload_help(nc), browser)
            return

        rid = parts[0]
        record = load_record(rid)
        if record is None:
            self._send('ID が見つかりません\n', status=404)
            return

        sub = parts[1] if len(parts) > 1 else ''
        packages = record['packages']
        if sub == 'cycles':
            self._respond(render_cycles(packages, nc), browser, f'dep/{rid}/cycles', rid=rid, active='cycles')
        elif sub == 'heavy':
            show_all = 'all' in qs
            self._respond(render_heavy(packages, nc, show_all), browser, f'dep/{rid}/heavy', rid=rid, active='heavy')
        elif sub == 'licenses':
            self._respond(render_licenses(packages, nc), browser, f'dep/{rid}/licenses', rid=rid, active='licenses')
        elif not sub:
            root_deps = {name: None for name in record['root_deps']}
            self._respond(render_tree(record['root_name'], root_deps, packages, nc), browser, f'dep/{rid}', rid=rid, active='')
        else:
            self._send('Not found\n', status=404)

    def do_GET(self):
        try: self._dispatch('GET')
        except Exception: self._send('Internal error\n', status=500)

    def do_POST(self):
        try: self._dispatch('POST')
        except Exception: self._send('Internal error\n', status=500)


if __name__ == '__main__':
    server = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    print(f'dep server listening on 127.0.0.1:{PORT}')
    server.serve_forever()
