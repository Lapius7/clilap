#!/usr/bin/env python3
"""Minimal cheat sheet server serving tldr-pages content."""

import os
import re
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

PORT = 3209
TLDR_DIR = os.path.join(os.path.dirname(__file__), 'tldr-pages')

BROWSER_KEYS = ('mozilla', 'webkit', 'trident', 'opera')

def is_browser(ua_str):
    u = ua_str.lower()
    return any(k in u for k in BROWSER_KEYS)

# ANSI
R   = '\x1b[0m'
B   = '\x1b[1m'
D   = '\x1b[2m'
BC  = '\x1b[1;36m'
C   = '\x1b[36m'
Y   = '\x1b[33m'
BY  = '\x1b[1;33m'
BG  = '\x1b[1;32m'
BW  = '\x1b[1;37m'
DC  = '\x1b[2;36m'

PLATFORM_ORDER = ['common', 'linux', 'osx', 'windows', 'android', 'freebsd', 'netbsd', 'openbsd', 'sunos']

def _scan_langs():
    langs = []
    try:
        for d in sorted(os.listdir(TLDR_DIR)):
            full = os.path.join(TLDR_DIR, d)
            if d.startswith('pages.') and os.path.isdir(full) and not os.path.islink(full):
                langs.append(d[6:])
    except Exception:
        pass
    if 'en' in langs:
        langs.remove('en')
    langs.insert(0, 'en')
    return langs

AVAILABLE_LANGS = _scan_langs()

def find_page(cmd, lang='en'):
    """Find tldr page file for command, trying platforms in order."""
    pages_dir = 'pages' if lang == 'en' else f'pages.{lang}'
    base = os.path.join(TLDR_DIR, pages_dir)
    if not os.path.isdir(base):
        base = os.path.join(TLDR_DIR, 'pages')

    for platform in PLATFORM_ORDER:
        path = os.path.join(base, platform, cmd + '.md')
        if os.path.isfile(path):
            return path

    # fallback to en if translation not found
    if lang != 'en':
        return find_page(cmd, 'en')
    return None


def render_page(path, no_color=False):
    """Render tldr markdown as ANSI-colored terminal text."""
    with open(path, encoding='utf-8') as f:
        content = f.read()

    def c(code, text):
        return text if no_color else code + text + R

    lines = content.splitlines()
    out = []

    for line in lines:
        if line.startswith('# '):
            cmd = line[2:].strip()
            out.append(c(BY, cmd))
        elif line.startswith('> More information:'):
            url = line[len('> More information:'):].strip().strip('<>.')
            out.append(c(D, '  More info: ') + c(C, url))
        elif line.startswith('> See also:'):
            rest = line[len('> See also:'):].strip()
            out.append(c(D, '  See also: ') + c(C, rest))
        elif line.startswith('> '):
            out.append(c(D, '  ' + line[2:].strip()))
        elif line.startswith('- '):
            desc = line[2:].strip().rstrip(':')
            out.append('')
            out.append(c(BG, '  - ') + c(B, desc) + ':')
        elif line.startswith('`') and line.endswith('`'):
            cmd_text = line[1:-1]
            # highlight {{placeholders}}
            if no_color:
                out.append('    ' + cmd_text)
            else:
                highlighted = re.sub(
                    r'\{\{(.+?)\}\}',
                    lambda m: Y + '{{' + m.group(1) + '}}' + BC,
                    cmd_text
                )
                out.append('    ' + BC + highlighted + R)
        elif line == '':
            pass  # skip blank lines in source (we add our own)
        else:
            out.append('  ' + line)

    return '\n'.join(out) + '\n'


def list_commands(prefix='', lang='en'):
    """List available commands, optionally filtered by prefix."""
    pages_dir = 'pages' if lang == 'en' else f'pages.{lang}'
    base = os.path.join(TLDR_DIR, pages_dir)
    if not os.path.isdir(base):
        base = os.path.join(TLDR_DIR, 'pages')

    seen = set()
    for platform in PLATFORM_ORDER:
        pdir = os.path.join(base, platform)
        if not os.path.isdir(pdir):
            continue
        for f in sorted(os.listdir(pdir)):
            if f.endswith('.md'):
                name = f[:-3]
                if name not in seen and name.startswith(prefix):
                    seen.add(name)
    return sorted(seen)


def render_help(no_color, lang='ja', cjk_width=2):
    def c(code, text): return text if no_color else code + text + R
    BOX_IN = 22

    def bsep():
        return c(DC, '+' + '─' * (BOX_IN + 2) + '+')

    def bline(text=''):
        return c(DC, '|') + ' ' + pad_to(text, BOX_IN, cjk_width) + ' ' + c(DC, '|')

    def box(rows):
        return [bsep()] + [bline(r) for r in rows] + [bsep()]

    def merge3(b1, b2, b3):
        return [a + ' ' + b + ' ' + cc for a, b, cc in zip(b1, b2, b3)]

    art = [
        c(BC, r'      _                _   '),
        c(BC, r'  ___| |__   ___  __ _| |_ '),
        c(BC, " / __| '_ \\ / _ \\/ _`  | __|"),
        c(BC, r'| (__| | | |  __/ (_| | |_ '),
        c(BC, r' \___|_| |_|\___|\__,_|\__|'),
    ]

    if lang == 'ja':
        b1 = box([
            c(BC, '$ curl cheat/git'),
            c(BC, '$ curl cheat/curl'),
            c(BC, '$ curl cheat/docker'),
            c(BC, '$ curl cheat/vim'),
            '',
            '',
        ])
        b2 = box([
            c(BC, '$ curl cheat/:list'),
            c(D,  'コマンド一覧'),
            '',
            c(D,  '3,000以上のコマンド'),
            c(D,  '(tldr-pages)'),
            '',
        ])
        b3 = box([
            c(C, '?en') + '  ' + c(D, '英語表示'),
            c(C, '?nocolor') + '  ' + c(D, 'カラー無効'),
            '',
            c(D, 'デフォルトは日本語'),
            c(D, '?en で英語に'),
            c(D, 'フォールバック'),
        ])
        b4 = box([
            c(BC, '$ curl cheat/ls'),
            c(BC, '$ curl cheat/tar'),
            c(BC, '$ curl cheat/find'),
            c(BC, '$ curl cheat/grep'),
            '',
            '',
        ])
        b5 = box([
            c(BC, '$ curl cheat/git'),
            c(D,  '  ?en'),
            '',
            c(BC, '$ curl cheat/ls'),
            c(D,  '  ?nocolor'),
            '',
        ])
        b6 = box([
            c(D,  'データソース:'),
            c(C,  'tldr-pages'),
            '',
            c(D,  'github.com/'),
            c(C,  'tldr-pages/tldr'),
            '',
        ])
        hint = c(DC, '  ?nocolor  ?en')
    else:
        b1 = box([
            c(BC, '$ curl cheat/git'),
            c(BC, '$ curl cheat/curl'),
            c(BC, '$ curl cheat/docker'),
            c(BC, '$ curl cheat/vim'),
            '',
            '',
        ])
        b2 = box([
            c(BC, '$ curl cheat/:list'),
            c(D,  'list all commands'),
            '',
            c(D,  '3,000+ commands'),
            c(D,  '(tldr-pages)'),
            '',
        ])
        b3 = box([
            c(C, '?ja') + '  ' + c(D, 'Japanese'),
            c(C, '?nocolor') + '  ' + c(D, 'No colors'),
            '',
            c(D, 'Default: English'),
            c(D, 'Falls back to'),
            c(D, 'English if missing'),
        ])
        b4 = box([
            c(BC, '$ curl cheat/ls'),
            c(BC, '$ curl cheat/tar'),
            c(BC, '$ curl cheat/find'),
            c(BC, '$ curl cheat/grep'),
            '',
            '',
        ])
        b5 = box([
            c(BC, '$ curl cheat/git'),
            c(D,  '  ?ja'),
            '',
            c(BC, '$ curl cheat/ls'),
            c(D,  '  ?nocolor'),
            '',
        ])
        b6 = box([
            c(D,  'Data source:'),
            c(C,  'tldr-pages'),
            '',
            c(D,  'github.com/'),
            c(C,  'tldr-pages/tldr'),
            '',
        ])
        hint = c(DC, '  ?nocolor  ?ja')

    out = art + [''] + merge3(b1, b2, b3) + [''] + merge3(b4, b5, b6) + ['', hint]
    return '\n'.join(out) + '\n'

def render_help_html(lang):
    css = (
        '*{box-sizing:border-box;margin:0;padding:0}'
        'body{background:#000;color:#aaa;font-family:"Courier New",Consolas,Monaco,monospace;'
        'font-size:12px;line-height:1.6;padding:16px}'
        'pre{font-family:inherit;white-space:pre;margin:0 0 12px}'
        '.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin:8px 0}'
        '.box{border:1px solid #4b8ea8;padding:8px 10px;min-height:110px}'
        '.cmd{color:#61afef;font-weight:bold}'
        '.opt{color:#56b6c2}'
        '.dim{color:#5c6370}'
        '.hi{color:#e5c07b;font-weight:bold}'
        'a{color:#4ec9b0;text-decoration:none}a:hover{text-decoration:underline}'
        '.hint{margin-top:8px;color:#5c6370;font-size:11px}'
        '.hint .opt{color:#56b6c2}'
    )
    art_lines = [
        r'      _                _   ',
        r'  ___| |__   ___  __ _| |_',
        r" / __| '_ \\ / _ \\/ _`  | __|",
        r'| (__| | | |  __/ (_| | |_',
        r' \___|_| |_|\___|\__,_|\__|',
    ]
    art_html = '<pre style="color:#61afef;font-weight:bold">' + '\n'.join(art_lines) + '</pre>'

    def e(t): return t.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

    if lang == 'ja':
        boxes1 = [
            ['<span class="cmd">$ curl cheat/git</span>',
             '<span class="cmd">$ curl cheat/curl</span>',
             '<span class="cmd">$ curl cheat/docker</span>',
             '<span class="cmd">$ curl cheat/vim</span>'],
            ['<span class="cmd">$ curl cheat/:list</span>',
             '<span class="dim">コマンド一覧</span>',
             '',
             '<span class="dim">3,000以上のコマンド</span>',
             '<span class="dim">(tldr-pages)</span>'],
            ['<span class="opt">?en</span>  <span class="dim">英語表示</span>',
             '<span class="opt">?nocolor</span>  <span class="dim">カラー無効</span>',
             '',
             '<span class="dim">デフォルトは日本語</span>',
             '<span class="dim">?en で英語に</span>',
             '<span class="dim">フォールバック</span>'],
        ]
        boxes2 = [
            ['<span class="cmd">$ curl cheat/ls</span>',
             '<span class="cmd">$ curl cheat/tar</span>',
             '<span class="cmd">$ curl cheat/find</span>',
             '<span class="cmd">$ curl cheat/grep</span>'],
            ['<span class="cmd">$ curl cheat/git</span>',
             '<span class="dim">  ?en</span>',
             '',
             '<span class="cmd">$ curl cheat/ls</span>',
             '<span class="dim">  ?nocolor</span>'],
            ['<span class="dim">データソース:</span>',
             '<span class="opt">tldr-pages</span>',
             '',
             '<span class="dim">github.com/</span>',
             '<span class="opt">tldr-pages/tldr</span>'],
        ]
        hint_text = '<span class="opt">?nocolor</span>  <span class="opt">?en</span>'
    else:
        boxes1 = [
            ['<span class="cmd">$ curl cheat/git</span>',
             '<span class="cmd">$ curl cheat/curl</span>',
             '<span class="cmd">$ curl cheat/docker</span>',
             '<span class="cmd">$ curl cheat/vim</span>'],
            ['<span class="cmd">$ curl cheat/:list</span>',
             '<span class="dim">list all commands</span>',
             '',
             '<span class="dim">3,000+ commands</span>',
             '<span class="dim">(tldr-pages)</span>'],
            ['<span class="opt">?ja</span>  <span class="dim">Japanese</span>',
             '<span class="opt">?nocolor</span>  <span class="dim">No colors</span>',
             '',
             '<span class="dim">Default: English</span>',
             '<span class="dim">Falls back to</span>',
             '<span class="dim">English if missing</span>'],
        ]
        boxes2 = [
            ['<span class="cmd">$ curl cheat/ls</span>',
             '<span class="cmd">$ curl cheat/tar</span>',
             '<span class="cmd">$ curl cheat/find</span>',
             '<span class="cmd">$ curl cheat/grep</span>'],
            ['<span class="cmd">$ curl cheat/git</span>',
             '<span class="dim">  ?ja</span>',
             '',
             '<span class="cmd">$ curl cheat/ls</span>',
             '<span class="dim">  ?nocolor</span>'],
            ['<span class="dim">Data source:</span>',
             '<span class="opt">tldr-pages</span>',
             '',
             '<span class="dim">github.com/</span>',
             '<span class="opt">tldr-pages/tldr</span>'],
        ]
        hint_text = '<span class="opt">?nocolor</span>  <span class="opt">?ja</span>'

    def render_box(rows):
        inner = '<br>'.join(r if r else '&nbsp;' for r in rows)
        return f'<div class="box">{inner}</div>'

    grid1 = '<div class="grid">' + ''.join(render_box(b) for b in boxes1) + '</div>'
    grid2 = '<div class="grid">' + ''.join(render_box(b) for b in boxes2) + '</div>'
    hint = f'<div class="hint">{hint_text}</div>'

    return (f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>cheat - Help</title><style>{css}</style></head>'
            f'<body>{art_html}{grid1}{grid2}{hint}</body></html>')

def pad_to(s, width, cjk_width=2):
    plain = re.sub(r'\x1b\[[^m]*m', '', s)
    import unicodedata
    dw = sum(cjk_width if unicodedata.east_asian_width(ch) in ('W','F') else 1 for ch in plain)
    return s + ' ' * max(0, width - dw)

def render_lang_hint(current_lang, nc, fell_back=False):
    def c(code, text): return text if nc else code + text + R
    tokens = []
    for l in AVAILABLE_LANGS:
        if l == current_lang:
            if fell_back:
                tok = c(BY, f'[{l}') + c(D, '→en') + c(BY, ']')
            else:
                tok = c(BY, f'[{l}]')
            tokens.append(tok)
        else:
            tokens.append(c(DC, l))
    LABEL = '?'
    SEP = '  '
    margin = '  '
    indent = margin + ' ' * len(LABEL) + SEP
    lines, line, line_len = [], margin + c(C, LABEL), len(margin) + len(LABEL)
    for tok in tokens:
        plain = re.sub(r'\x1b\[[^m]*m', '', tok)
        if line_len + len(SEP) + len(plain) > 62:
            lines.append(line)
            line = indent + tok
            line_len = len(indent) + len(plain)
        else:
            line += SEP + tok
            line_len += len(SEP) + len(plain)
    if line_len > len(indent):
        lines.append(line)
    lines.append(margin + c(C, '?nocolor'))
    return '\n'.join(lines)

def lang_links_html(current_lang, fell_back=False):
    lang_parts = []
    for l in AVAILABLE_LANGS:
        if l == current_lang:
            if fell_back:
                label = f'[{l}<span style="color:#5c6370">→en</span>]'
            else:
                label = f'[{l}]'
            lang_parts.append(f'<span style="color:#e5c07b;font-weight:bold">{label}</span>')
        else:
            lang_parts.append(f'<a href="?{l}">{l}</a>')
    return ('<div style="margin-top:12px;color:#5c6370;font-size:11px;line-height:1.8">'
            f'<span style="color:#56b6c2">?</span> {" ".join(lang_parts)}'
            '<br><a href="?nocolor">?nocolor</a></div>')

# ---------- ANSI-to-HTML ----------
_A2H = {
    '1':    'font-weight:bold',
    '2':    'color:#5c6370',
    '33':   'color:#e5c07b',
    '36':   'color:#56b6c2',
    '1;31': 'color:#e06c75;font-weight:bold',
    '1;32': 'color:#98c379;font-weight:bold',
    '1;33': 'color:#e5c07b;font-weight:bold',
    '1;36': 'color:#61afef;font-weight:bold',
    '1;37': 'color:#abb2bf;font-weight:bold',
    '2;36': 'color:#4b8ea8',
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
            out.append({'&':'&amp;','<':'&lt;','>':'&gt;'}.get(text[i], text[i]))
            i += 1
    out.extend(['</span>'] * depth)
    return ''.join(out)

def html_wrap(ansi_text, title='Cheat', footer_html=''):
    css = ('*{box-sizing:border-box;margin:0;padding:0}'
           'body{background:#000;color:#aaa;'
           'font-family:"Courier New",Consolas,Monaco,"Lucida Console",monospace;'
           'font-size:12px;line-height:1.5;padding:16px}'
           'pre{font-family:inherit;white-space:pre;margin:0}'
           'a{color:#4ec9b0;text-decoration:none}a:hover{text-decoration:underline}')
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{css}</style></head>'
            f'<body><pre>{ansi_to_html(ansi_text)}</pre>{footer_html}</body></html>')

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # silence access log

    def do_GET(self):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        ua = self.headers.get('User-Agent', '')
        browser = is_browser(ua)
        no_color = 'nocolor' in qs or 'nc' in qs or browser
        _lang_key = next((k for k in qs if k in AVAILABLE_LANGS), None)
        lang = _lang_key if _lang_key else 'ja'

        def send(body, html=False):
            ct = 'text/html; charset=utf-8' if html else 'text/plain; charset=utf-8'
            self.send_response(200)
            self.send_header('Content-Type', ct)
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body.encode('utf-8'))

        if parsed.path.rstrip('/') == '/help':
            if browser:
                send(render_help_html(lang), html=True)
            else:
                send(render_help(no_color, lang))
            return

        cmd = re.sub(r'[^a-zA-Z0-9._-]', '', unquote(parsed.path.lstrip('/')).split('/')[0])

        _page_path = find_page(cmd, lang) if (cmd and cmd != ':list') else None
        _lang_dir = os.path.join(TLDR_DIR, 'pages' if lang == 'en' else f'pages.{lang}')
        fell_back = (_page_path is not None and lang != 'en'
                     and not _page_path.startswith(_lang_dir + os.sep))

        def render_body(nc, include_hint=True):
            def c(code, text): return text if nc else code + text + R
            hint = render_lang_hint(lang, nc, fell_back) if include_hint else ''
            if not cmd or cmd == ':list':
                cmds = list_commands(lang=lang)
                sep    = '═' * 60 if nc else c(DC, '═' * 60)
                header = ('Available commands: %d' % len(cmds) if nc
                          else c(BC, 'Available commands: ') + c(B, str(len(cmds))))
                body = sep + '\n' + header + '\n\n  ' + '  '.join(cmds[:100]) + '\n  ...\n' + sep
                return body + ('\n' + hint + '\n' if hint else '\n')
            if _page_path:
                sep  = '═' * 60 if nc else c(DC, '═' * 60)
                body = sep + '\n' + render_page(_page_path, nc) + sep
                return body + ('\n' + hint + '\n' if hint else '\n')
            msg  = c(DC, '  No cheat sheet found for: ') + c(B, cmd) + '\n'
            msg += c(DC, '  Try: ') + c(C, 'curl clilap.org/cheat/:list') + '\n'
            return msg

        if browser:
            send(html_wrap(render_body(False, include_hint=False), f'cheat/{cmd or ":list"}', lang_links_html(lang, fell_back)), html=True)
        else:
            send(render_body(no_color))


if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    print(f'cheat server listening on 127.0.0.1:{PORT}')
    server.serve_forever()
