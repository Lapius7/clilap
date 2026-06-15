#!/usr/bin/env python3
"""GitHub info server for clilap.org — /github/:user[/:repo[/:view]]"""

import base64, json, re, urllib.request, urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 3213

BROWSER_KEYS = ('mozilla', 'webkit', 'trident', 'opera')
def is_browser(ua): return any(k in ua.lower() for k in BROWSER_KEYS)

R   = '\x1b[0m'
B   = '\x1b[1m'
D   = '\x1b[2m'
C   = '\x1b[36m'
BC  = '\x1b[1;36m'
Y   = '\x1b[33m'
BY  = '\x1b[1;33m'
BG  = '\x1b[1;32m'
BW  = '\x1b[1;37m'
DC  = '\x1b[2;36m'
BR  = '\x1b[1;31m'

UA = 'clilap.org/github'
_NAME_RE = re.compile(r'^[a-zA-Z0-9_.-]{1,100}$')
_LANG_RE  = re.compile(r'^[a-z]{2,5}$')

def _valid(s): return bool(s) and bool(_NAME_RE.match(s))

def sep(nc): return '═' * 60 if nc else DC + '═' * 60 + R
def c(code, text, nc): return text if nc else code + text + R
def hint(nc, text): return ('' if nc else DC) + text + ('' if nc else R)


def _api(path, token=None):
    url = f'https://api.github.com{path}'
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    })
    if token:
        req.add_header('Authorization', f'Bearer {token}')
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read()), int(r.headers.get('X-RateLimit-Remaining', -1))


def _fmt_num(n):
    if n is None: return '?'
    n = int(n)
    if n >= 1_000_000: return f'{n/1_000_000:.1f}M'
    if n >= 1_000:     return f'{n/1_000:.1f}k'
    return str(n)

def _timeago(iso):
    if not iso: return '?'
    import datetime
    try:
        dt = datetime.datetime.fromisoformat(iso.replace('Z', '+00:00'))
        diff = datetime.datetime.now(datetime.timezone.utc) - dt
        s = int(diff.total_seconds())
        if s < 60:     return f'{s}s ago'
        if s < 3600:   return f'{s//60}m ago'
        if s < 86400:  return f'{s//3600}h ago'
        if s < 2592000: return f'{s//86400}d ago'
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return iso[:10]


# ── /github/:user ─────────────────────────────────────────────────────────
def do_user(user, nc):
    try:
        data, _ = _api(f'/users/{user}')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return sep(nc) + '\n' + c(BR, f'  User not found: {user}', nc) + '\n' + sep(nc) + '\n'
        raise
    repos_data, _ = _api(f'/users/{user}/repos?sort=updated&per_page=8')

    name    = data.get('name') or user
    bio     = data.get('bio') or ''
    company = data.get('company') or ''
    loc     = data.get('location') or ''
    blog    = data.get('blog') or ''
    pub     = data.get('public_repos', 0)
    fol     = data.get('followers', 0)

    lines = [
        sep(nc),
        c(BW, f'  {name}', nc) + c(DC, f'  @{user}', nc),
    ]
    if bio:     lines.append(c(D,  f'  {bio}', nc))
    if loc:     lines.append(c(DC, f'  📍 {loc}', nc))
    if company: lines.append(c(DC, f'  🏢 {company}', nc))
    if blog:    lines.append(c(DC, f'  🔗 {blog}', nc))
    lines += [
        '',
        c(DC, '  repos  ', nc) + c(BY, _fmt_num(pub), nc) +
        c(DC, '   followers  ', nc) + c(BY, _fmt_num(fol), nc),
        '',
        c(BC, '  Recent repositories:', nc),
    ]
    for r in repos_data[:8]:
        rname = r.get('name', '')
        rdesc = (r.get('description') or '')[:50]
        rstars = _fmt_num(r.get('stargazers_count', 0))
        rlang  = r.get('language') or ''
        tag = f' ★{rstars}' if r.get('stargazers_count') else ''
        lang_tag = f' [{rlang}]' if rlang else ''
        lines.append(c(C, f'  {rname}', nc) + c(D, f'{lang_tag}{tag}', nc))
        if rdesc:
            lines.append(c(DC, f'    {rdesc}', nc))
    lines += [
        sep(nc),
        hint(nc, f'  /github/{user}/{{repo}}  for repo details'),
    ]
    return '\n'.join(lines) + '\n'


# ── /github/:user/:repo ───────────────────────────────────────────────────
def do_repo(user, repo, nc):
    try:
        data, _ = _api(f'/repos/{user}/{repo}')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return sep(nc) + '\n' + c(BR, f'  Not found: {user}/{repo}', nc) + '\n' + sep(nc) + '\n'
        raise

    desc     = (data.get('description') or '')
    lang     = data.get('language') or '—'
    stars    = _fmt_num(data.get('stargazers_count'))
    forks    = _fmt_num(data.get('forks_count'))
    issues   = _fmt_num(data.get('open_issues_count'))
    updated  = _timeago(data.get('updated_at'))
    pushed   = _timeago(data.get('pushed_at'))
    license_ = (data.get('license') or {}).get('spdx_id') or '—'
    topics   = data.get('topics') or []
    clone    = data.get('clone_url') or ''
    homepage = data.get('homepage') or ''

    lines = [
        sep(nc),
        c(BW, f'  {user}', nc) + c(DC, '/', nc) + c(BC, repo, nc),
    ]
    if desc:     lines.append(c(D, f'  {desc}', nc))
    if homepage: lines.append(c(DC, f'  🔗 {homepage}', nc))
    if topics:   lines.append(c(DC, '  # ', nc) + c(D, '  '.join(topics[:6]), nc))
    lines += [
        '',
        c(DC, '  language  ', nc) + c(BW, lang,    nc) +
        c(DC, '   license  ', nc) + c(BW, license_, nc),
        c(DC, '  stars     ', nc) + c(BY, stars,   nc) +
        c(DC, '   forks    ', nc) + c(BW, forks,   nc) +
        c(DC, '   issues   ', nc) + c(BR if data.get('open_issues_count', 0) else DC, issues, nc),
        c(DC, '  updated   ', nc) + c(D,  updated, nc) +
        c(DC, '   pushed   ', nc) + c(D,  pushed,  nc),
        '',
        c(DC, '  git clone ', nc) + c(C, clone, nc),
        sep(nc),
        hint(nc, f'  /github/{user}/{repo}/readme    /github/{user}/{repo}/releases'),
        hint(nc, f'  /github/{user}/{repo}/commits   /github/{user}/{repo}/issues'),
        hint(nc, f'  /github/{user}/{repo}/prs'),
    ]
    return '\n'.join(lines) + '\n'


# ── /github/:user/:repo/readme[/:lang] ───────────────────────────────────
def _decode_readme(data):
    content = base64.b64decode(data['content']).decode('utf-8', errors='replace')
    content = re.sub(r'^#{1,6}\s+', '', content, flags=re.MULTILINE)
    content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)
    content = re.sub(r'`{3}[^\n]*\n', '', content)
    content = re.sub(r'`(.+?)`', r'\1', content)
    return content

def do_readme(user, repo, lang, nc):
    # Try language-specific file first, then default README
    candidates = []
    if lang and _LANG_RE.match(lang):
        candidates += [f'README.{lang}.md', f'README-{lang}.md']
    candidates.append(None)  # None = default README endpoint

    content, label = None, 'README'
    for fname in candidates:
        try:
            if fname is None:
                data, _ = _api(f'/repos/{user}/{repo}/readme')
            else:
                data, _ = _api(f'/repos/{user}/{repo}/contents/{fname}')
            content = _decode_readme(data)
            label = fname or 'README'
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue
            raise

    if content is None:
        return sep(nc) + '\n' + c(DC, '  No README found.', nc) + '\n' + sep(nc) + '\n'

    lines = [sep(nc), c(BC, f'  {label} — {user}/{repo}', nc), '']
    for line in content.splitlines()[:80]:
        lines.append('  ' + line)
    if content.count('\n') > 80:
        lines.append(c(DC, '  ... (truncated)', nc))
    lines.append(sep(nc))
    return '\n'.join(lines) + '\n'


# ── /github/:user/:repo/releases ──────────────────────────────────────────
def do_releases(user, repo, nc):
    try:
        data, _ = _api(f'/repos/{user}/{repo}/releases?per_page=5')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return sep(nc) + '\n' + c(BR, '  Not found.', nc) + '\n' + sep(nc) + '\n'
        raise
    lines = [sep(nc), c(BC, f'  Releases — {user}/{repo}', nc), '']
    if not data:
        lines.append(c(DC, '  No releases yet.', nc))
    for r in data[:5]:
        tag  = r.get('tag_name', '?')
        name = r.get('name') or tag
        pub  = _timeago(r.get('published_at'))
        pre  = c(Y, ' [pre]', nc) if r.get('prerelease') else ''
        lines.append(c(BG, f'  {tag}', nc) + c(D, f'  {name}', nc) + pre + c(DC, f'  {pub}', nc))
        body = (r.get('body') or '').strip()
        if body:
            for bl in body.splitlines()[:3]:
                lines.append(c(D, f'    {bl[:70]}', nc))
        lines.append('')
    lines.append(sep(nc))
    return '\n'.join(lines) + '\n'


# ── /github/:user/:repo/commits ───────────────────────────────────────────
def do_commits(user, repo, nc):
    try:
        data, _ = _api(f'/repos/{user}/{repo}/commits?per_page=10')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return sep(nc) + '\n' + c(BR, '  Not found.', nc) + '\n' + sep(nc) + '\n'
        raise
    lines = [sep(nc), c(BC, f'  Commits — {user}/{repo}', nc), '']
    for item in data[:10]:
        sha   = item['sha'][:7]
        msg   = (item['commit']['message'].splitlines()[0] or '')[:65]
        when  = _timeago(item['commit']['committer']['date'])
        who   = (item['commit']['author']['name'] or '')[:20]
        lines.append(c(DC, f'  {sha}', nc) + '  ' + c(BW, msg, nc))
        lines.append(c(D,  f'         {who}  {when}', nc))
    lines.append(sep(nc))
    return '\n'.join(lines) + '\n'


# ── /github/:user/:repo/issues ────────────────────────────────────────────
def do_issues(user, repo, nc):
    try:
        data, _ = _api(f'/repos/{user}/{repo}/issues?state=open&per_page=10')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return sep(nc) + '\n' + c(BR, '  Not found.', nc) + '\n' + sep(nc) + '\n'
        raise
    items = [i for i in data if 'pull_request' not in i]
    lines = [sep(nc), c(BC, f'  Issues — {user}/{repo}', nc) + c(DC, f'  ({len(items)} shown)', nc), '']
    if not items:
        lines.append(c(BG, '  No open issues.', nc))
    for i in items[:10]:
        num   = i['number']
        title = i['title'][:65]
        when  = _timeago(i.get('updated_at'))
        labels = ' '.join(f'[{l["name"]}]' for l in i.get('labels', [])[:3])
        lines.append(c(DC, f'  #{num:<5}', nc) + c(BW, title, nc))
        if labels:
            lines.append(c(Y,  f'         {labels}', nc) + c(D, f'  {when}', nc))
        else:
            lines.append(c(D,  f'         {when}', nc))
    lines.append(sep(nc))
    return '\n'.join(lines) + '\n'


# ── /github/:user/:repo/prs ───────────────────────────────────────────────
def do_prs(user, repo, nc):
    try:
        data, _ = _api(f'/repos/{user}/{repo}/pulls?state=open&per_page=10')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return sep(nc) + '\n' + c(BR, '  Not found.', nc) + '\n' + sep(nc) + '\n'
        raise
    lines = [sep(nc), c(BC, f'  Pull Requests — {user}/{repo}', nc) + c(DC, f'  ({len(data)} open)', nc), '']
    if not data:
        lines.append(c(BG, '  No open pull requests.', nc))
    for pr in data[:10]:
        num    = pr['number']
        title  = pr['title'][:62]
        when   = _timeago(pr.get('updated_at'))
        branch = pr['head']['ref'][:30]
        lines.append(c(DC, f'  #{num:<5}', nc) + c(BW, title, nc))
        lines.append(c(D,  f'         ← {branch}  {when}', nc))
    lines.append(sep(nc))
    return '\n'.join(lines) + '\n'


# ── /github/:user/:repo/stars ─────────────────────────────────────────────
def do_stars(user, repo, nc):
    try:
        data, _ = _api(f'/repos/{user}/{repo}')
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return sep(nc) + '\n' + c(BR, '  Not found.', nc) + '\n' + sep(nc) + '\n'
        raise
    stars = data.get('stargazers_count', 0)
    return (sep(nc) + '\n' +
            c(BY, f'  ★ {stars}', nc) + c(DC, f'  {user}/{repo}', nc) + '\n' +
            sep(nc) + '\n')


def do_help(nc):
    lines = [
        sep(nc),
        c(BW, '  clilap.org/github', nc) + c(DC, '  🐙 GitHub情報をターミナルで確認', nc),
        c(D,  '  GitHub APIを使ってリポジトリ・ユーザー情報を取得します。', nc),
        '',
        c(BC, '  /github/:user', nc),
        c(DC, '    ユーザープロフィール + 最近のリポジトリ一覧', nc),
        '',
        c(BC, '  /github/:user/:repo', nc),
        c(DC, '    リポジトリ概要 (スター数・フォーク数・言語・ライセンス等)', nc),
        '',
        c(BC, '  /github/:user/:repo/', nc) + c(BY, '{view}', nc),
        *[c(DC, f'    {v}', nc) for v in
          ['readme   — READMEを表示',
           'releases — リリース履歴',
           'commits  — 最新コミット一覧',
           'issues   — オープンなIssue',
           'prs      — オープンなPR一覧',
           'stars    — スター数のみ表示']],
        '',
        c(D,  '  使用例:', nc),
        c(C,  '  curl clilap.org/github/curl/curl', nc),
        c(C,  '  curl clilap.org/github/torvalds/linux/commits', nc),
        c(C,  '  curl clilap.org/github/tj/n/releases', nc),
        c(C,  '  curl clilap.org/github/Lapius7', nc),
        sep(nc),
    ]
    return '\n'.join(lines) + '\n'


# ── ANSI → HTML ───────────────────────────────────────────────────────────
_A2H = {
    '1':'font-weight:bold','2':'color:#5c6370','33':'color:#e5c07b',
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
        'pre{font-family:inherit;white-space:pre;margin:0}'
        'a{color:#4ec9b0;text-decoration:none}a:hover{text-decoration:underline}')
_FOOTER = '<div style="margin-top:16px;padding-top:6px;border-top:1px solid #1a1a1a;color:#333;font-size:11px;">©2025 CLI Lap by Lapius7. All rights reserved.</div>'

def html_wrap(ansi_text, title='github - Clilap'):
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{_CSS}</style></head>'
            f'<body><pre>{ansi_to_html(ansi_text)}</pre>{_FOOTER}</body></html>')


# ── Handler ───────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        parsed  = urlparse(self.path)
        qs      = parse_qs(parsed.query, keep_blank_values=True)
        ua      = self.headers.get('User-Agent', '')
        browser = is_browser(ua)
        nc      = 'nocolor' in qs or 'nc' in qs

        parts = [p for p in parsed.path.split('/') if p]
        # parts[0] == 'github' (stripped by nginx), or empty
        # nginx proxies /github/* → /github/*  so parts[0] is 'github'
        if parts and parts[0] == 'github':
            parts = parts[1:]

        def respond(text, status=200):
            ct = 'text/html; charset=utf-8' if browser else 'text/plain; charset=utf-8'
            body = html_wrap(text) if browser else text
            self.send_response(status)
            self.send_header('Content-Type', ct)
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body.encode('utf-8'))

        if not parts:
            respond(do_help(nc)); return

        user     = parts[0] if parts else ''
        repo     = parts[1] if len(parts) > 1 else ''
        view     = parts[2].lower() if len(parts) > 2 else ''
        lang_arg = parts[3].lower() if len(parts) > 3 else ''

        if not _valid(user):
            respond(sep(nc) + '\n' + c(BR, f'  Invalid username: {user[:40]}', nc) + '\n' + sep(nc) + '\n'); return

        try:
            if not repo:
                respond(do_user(user, nc))
            elif not _valid(repo):
                respond(sep(nc) + '\n' + c(BR, f'  Invalid repo name: {repo[:40]}', nc) + '\n' + sep(nc) + '\n')
            elif not view:
                respond(do_repo(user, repo, nc))
            elif view == 'readme':
                respond(do_readme(user, repo, lang_arg, nc))
            elif view == 'releases':
                respond(do_releases(user, repo, nc))
            elif view == 'commits':
                respond(do_commits(user, repo, nc))
            elif view == 'issues':
                respond(do_issues(user, repo, nc))
            elif view == 'prs':
                respond(do_prs(user, repo, nc))
            elif view == 'stars':
                respond(do_stars(user, repo, nc))
            else:
                respond(do_repo(user, repo, nc))
        except urllib.error.HTTPError as e:
            body = sep(nc) + '\n' + c(BR, f'  GitHub API error: {e.code}', nc)
            if e.code == 403:
                body += '\n' + c(DC, '  Rate limit hit. Try again in a minute.', nc)
            body += '\n' + sep(nc) + '\n'
            respond(body)
        except Exception:
            respond(sep(nc) + '\n' + c(BR, '  Request failed.', nc) + '\n' + sep(nc) + '\n')


if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    print(f'github server listening on 127.0.0.1:{PORT}')
    server.serve_forever()
