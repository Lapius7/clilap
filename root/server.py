#!/usr/bin/env python3
"""Root index server for clilap.org — serves the global service listing and 404 page."""

import re
import unicodedata
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

PORT = 3212

# ANSI
R  = '\x1b[0m'
D  = '\x1b[2m'
C  = '\x1b[36m'
BC = '\x1b[1;36m'
BW = '\x1b[1;37m'
DC = '\x1b[2;36m'
BR = '\x1b[1;31m'

BROWSER_KEYS = ('mozilla', 'webkit', 'trident', 'opera')
def is_browser(ua): return any(k in ua.lower() for k in BROWSER_KEYS)

def disp_width(s):
    plain = re.sub(r'\x1b\[[^m]*m', '', s)
    w = 0
    for ch in plain:
        cp  = ord(ch)
        eaw = unicodedata.east_asian_width(ch)
        if eaw in ('W', 'F'):
            w += 2
        elif 0x2600 <= cp <= 0x27FF:
            w += 2
        elif 0x1F000 <= cp <= 0x1FFFF:
            w += 2
        else:
            w += 1
    return w

def pad_to(s, width):
    return s + ' ' * max(0, width - disp_width(s))

_A2H = {
    '1':    'font-weight:bold',
    '2':    'color:#5c6370',
    '36':   'color:#56b6c2',
    '1;31': 'color:#e06c75;font-weight:bold',
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
            out.append({'&':'&amp;','<':'&lt;','>':'&gt;'}.get(text[i], text[i])); i += 1
    out.extend(['</span>'] * depth)
    return ''.join(out)

_CSS = ('*{box-sizing:border-box;margin:0;padding:0}'
        'body{background:#000;color:#aaa;'
        'font-family:"Courier New",Consolas,Monaco,"Lucida Console",monospace;'
        'font-size:12px;line-height:1.5;padding:16px}'
        'pre{font-family:inherit;white-space:pre;margin:0}'
        'a{color:#4ec9b0;text-decoration:none}a:hover{text-decoration:underline}')

def html_wrap(ansi_text, title='clilap.org'):
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{_CSS}</style></head>'
            f'<body><pre>{ansi_to_html(ansi_text)}</pre></body></html>')

def render_index(nc):
    def c(code, text): return text if nc else code + text + R
    W   = 80
    SEP = c(DC, '═' * W)
    div = c(DC, '  ' + '─' * (W - 2))
    def cmd(path, desc): return f'  {pad_to(c(BC, path), 28)} {c(D, desc)}'
    def sub(path, desc): return f'  {pad_to(c(DC, path), 28)} {c(DC, desc)}'

    return '\n'.join([
        SEP,
        f'  {c(BW, "clilap.org")}  {c(DC, "curl tools")}',
        div, '',
        cmd('/parrot',                 '🦜 カラフルなオウムのアニメーション'), '',
        cmd('/qr/TEXT',                '🔲 テキスト → QRコード'),
        sub('/qr/https://example.com', 'URL もOK'), '',
        cmd('/ipinfo',                 '🌐 現在のIP情報'),
        sub('/ipinfo/1.2.3.4',         '特定IPを調べる'), '',
        cmd('/weather/都市名',          '⛅ 天気予報 (日本語デフォルト)'),
        sub('/weather/Tokyo',          '例: 東京  /?lang=en で英語表示'),
        sub('/weather/東京都/新宿区',   '都道府県/市区町村でより正確に'), '',
        cmd('/cheat/コマンド',          '📖 コマンドチートシート'),
        sub('/cheat/git',              '例: git の使い方  /?ja  /?en で言語切替'),
        sub('/cheat/:list',            'コマンド一覧'), '',
        cmd('/headers',                '🔍 リクエストヘッダー確認'),
        cmd('/uuid/{n}',               '🔑 UUID生成 (省略で1件)'),
        cmd('/b64/encode/{text}',      '🔒 Base64 エンコード/デコード'),
        sub('/b64/decode/{text}',      ''), '',
        cmd('/hash/{algo}/{text}',     '#️⃣  ハッシュ計算'),
        sub('/hash/sha256/hello',      '例: md5 sha1 sha256 sha512'), '',
        cmd('/epoch/{value}',          '🕐 UNIXタイム変換 (省略で現在時刻)'),
        sub('/epoch/2024-01-01',       '例: YYYY-MM-DD・YYYY-MM-DDTHH:MM:SS'), '',
        cmd('/dns/{domain}/{type}',    '🌍 DNS lookup'),
        sub('/dns/google.com/MX',      '例: A AAAA MX NS TXT CNAME'), '',
        cmd('/whois/{domain}',         '📋 WHOIS lookup'),
        cmd('/color/{hex}',            '🎨 カラー変換 (hex / R,G,B)'),
        sub('/color/ff6b6b',           '例: → hex rgb hsl + スウォッチ'), '',
        cmd('/github/{user}/{repo}',   '🐙 GitHub リポジトリ情報'),
        sub('/github/curl/curl/commits', '例: readme releases commits issues prs'), '',
        div,
        f'  {c(DC, "共通オプション:")}  {c(DC, "?nocolor  ?ja  ?en")}',
        div,
        f'  {c(D, "by")} {c(C, "@Lapius7")}  {c(DC, "·")}  {c(C, "github.com/Lapius7/clilap")}',
        SEP,
    ]) + '\n'

def render_not_found(path, nc):
    def c(code, text): return text if nc else code + text + R
    SEP = c(DC, '═' * 60)
    safe_path = re.sub(r'[\x00-\x1f\x7f]', '', path)[:80]
    return '\n'.join([
        SEP,
        c(BR, '  404') + c(DC, f'  Not Found: {safe_path}'),
        '',
        c(DC, '  Services:'),
        c(BC, '    /weather   /ipinfo    /cheat     /qr'),
        c(BC, '    /headers   /uuid      /b64       /hash'),
        c(BC, '    /epoch     /dns       /whois     /color'),
        c(BC, '    /github    /parrot'),
        '',
        c(DC, '  curl clilap.org') + c(D, '  for help'),
        SEP,
    ]) + '\n'

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        parsed  = urlparse(self.path)
        qs      = parse_qs(parsed.query, keep_blank_values=True)
        ua      = self.headers.get('User-Agent', '')
        browser = is_browser(ua)
        nc      = 'nocolor' in qs or 'nc' in qs or browser

        path = parsed.path.rstrip('/') or '/'

        if path == '/':
            status = 200
            body_ansi = render_index(nc if not browser else False)
        else:
            status = 404
            body_ansi = render_not_found(path, nc if not browser else False)

        ct = 'text/html; charset=utf-8' if browser else 'text/plain; charset=utf-8'
        body = html_wrap(body_ansi, 'clilap.org' if status == 200 else '404 — clilap.org') if browser else body_ansi
        self.send_response(status)
        self.send_header('Content-Type', ct)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body.encode('utf-8'))

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    print(f'root server listening on 127.0.0.1:{PORT}')
    server.serve_forever()
