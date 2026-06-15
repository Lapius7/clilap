#!/usr/bin/env python3
"""Unified utility server for clilap.org — headers/uuid/b64/dns/whois/epoch/color/hash"""

import base64, colorsys, datetime, hashlib, re, subprocess, time, uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote

PORT = 3211

BROWSER_KEYS = ('mozilla', 'webkit', 'trident', 'opera')
def is_browser(ua): return any(k in ua.lower() for k in BROWSER_KEYS)

# ANSI
R  = '\x1b[0m'
B  = '\x1b[1m'
D  = '\x1b[2m'
C  = '\x1b[36m'
BC = '\x1b[1;36m'
Y  = '\x1b[33m'
BY = '\x1b[1;33m'
BG = '\x1b[1;32m'
BW = '\x1b[1;37m'
DC = '\x1b[2;36m'
BR = '\x1b[1;31m'

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
            elif code.startswith('48;2;'):
                parts = code.split(';')
                if len(parts) >= 5:
                    r, g, b = parts[2], parts[3], parts[4]
                    out.append(f'<span style="background:rgb({r},{g},{b});color:#fff">'); depth += 1
            elif code in _A2H:
                out.append(f'<span style="{_A2H[code]}">'); depth += 1
        else:
            out.append({'&':'&amp;','<':'&lt;','>':'&gt;'}.get(text[i], text[i])); i += 1
    out.extend(['</span>'] * depth)
    return ''.join(out)

def html_wrap(ansi_text, title='CLI Utils'):
    css = ('*{box-sizing:border-box;margin:0;padding:0}'
           'body{background:#000;color:#aaa;font-family:"Courier New",Consolas,Monaco,monospace;'
           'font-size:12px;line-height:1.5;padding:16px}'
           'pre{font-family:inherit;white-space:pre;margin:0}'
           'a{color:#4ec9b0;text-decoration:none}a:hover{text-decoration:underline}')
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{css}</style></head>'
            f'<body><pre>{ansi_to_html(ansi_text)}</pre></body></html>')

def sep(nc): return '═' * 60 if nc else DC + '═' * 60 + R
def c(code, text, nc): return text if nc else code + text + R
def hint(nc, text): return c(DC, text, nc)

# ── /headers ─────────────────────────────────────────────────────────────
def do_headers(req_headers, nc):
    lines = [sep(nc), c(BC, 'Request Headers', nc), '']
    for k, v in req_headers.items():
        lines.append(c(BY, f'  {k}: ', nc) + c(BW, v, nc))
    lines.append(sep(nc))
    return '\n'.join(lines) + '\n'

# ── /uuid ─────────────────────────────────────────────────────────────────
def do_uuid(n, nc):
    lines = [sep(nc)]
    for _ in range(min(max(n, 1), 100)):
        lines.append('  ' + c(BG, str(uuid.uuid4()), nc))
    lines.append(sep(nc))
    lines.append(hint(nc, '  /uuid/{n}  — generate n UUIDs (max 100)'))
    return '\n'.join(lines) + '\n'

# ── /b64 ─────────────────────────────────────────────────────────────────
def do_b64(action, data, nc):
    try:
        if isinstance(data, str):
            data = data.encode()
        if action == 'encode':
            result = base64.b64encode(data).decode()
        else:
            result = base64.b64decode(data + b'==').decode('utf-8', errors='replace')
        lines = [sep(nc), '  ' + c(BG, result, nc), sep(nc)]
    except Exception as e:
        lines = [sep(nc), '  ' + c(BR, f'Error: {e}', nc), sep(nc)]
    lines.append(hint(nc, '  /b64/encode/{text}  /b64/decode/{text}'))
    lines.append(hint(nc, '  echo text | curl -d @- clilap.org/b64/encode'))
    return '\n'.join(lines) + '\n'

def do_b64_help(nc):
    lines = [sep(nc),
             c(BC, '  base64 encode / decode', nc), '',
             c(BW, '  $ curl clilap.org/b64/encode/hello', nc),
             c(BW, '  $ curl clilap.org/b64/decode/aGVsbG8=', nc),
             c(BW, '  $ echo "hello" | curl -d @- clilap.org/b64/encode', nc),
             sep(nc)]
    return '\n'.join(lines) + '\n'

# ── /hash ─────────────────────────────────────────────────────────────────
HASH_ALGOS = ['md5', 'sha1', 'sha256', 'sha512', 'sha3_256', 'sha3_512']

def do_hash(algo, data, nc):
    if algo not in HASH_ALGOS:
        lines = [sep(nc),
                 c(BR, f'  Unknown algo: {algo}', nc),
                 c(D, f'  Supported: {", ".join(HASH_ALGOS)}', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'
    if isinstance(data, str):
        data = data.encode()
    h = hashlib.new(algo, data)
    digest = h.hexdigest()
    bits = len(digest) * 4
    lines = [sep(nc),
             c(DC, '  algo   ', nc) + c(BW, algo, nc),
             c(DC, '  input  ', nc) + c(BW, f'{len(data)} bytes', nc),
             c(DC, '  bits   ', nc) + c(BW, str(bits), nc),
             '',
             '  ' + c(BG, digest, nc),
             sep(nc)]
    lines.append(hint(nc, f'  /hash/{algo}/{{text}}  |  echo text | curl -d @- clilap.org/hash/{algo}'))
    return '\n'.join(lines) + '\n'

def do_hash_help(nc):
    lines = [sep(nc),
             c(BC, '  hash', nc), '',
             *[c(BW, f'  $ curl clilap.org/hash/{a}/hello', nc) for a in HASH_ALGOS[:3]],
             c(D, '  ...', nc),
             c(D, f'  algos: {", ".join(HASH_ALGOS)}', nc),
             c(BW, '  $ echo "hello" | curl -d @- clilap.org/hash/sha256', nc),
             sep(nc)]
    return '\n'.join(lines) + '\n'

# ── /epoch ─────────────────────────────────────────────────────────────────
def _rel(secs):
    secs = abs(int(secs))
    if secs < 60:   return f'{secs}s ago'
    if secs < 3600: return f'{secs//60}m ago'
    if secs < 86400: return f'{secs//3600}h ago'
    return f'{secs//86400}d ago'

def do_epoch(value, nc):
    now = time.time()
    def fmt(ts):
        try:
            dt_utc   = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
            dt_local = datetime.datetime.fromtimestamp(ts).astimezone()
            tz_name  = dt_local.strftime('%Z')
        except (OSError, OverflowError, ValueError):
            return sep(nc) + '\n' + c(BR, '  Timestamp out of range.', nc) + '\n' + sep(nc) + '\n'
        lines = [sep(nc),
                 c(DC, '  unix  ', nc) + c(BY, str(int(ts)), nc),
                 c(DC, '  utc   ', nc) + c(BW, dt_utc.strftime('%Y-%m-%d %H:%M:%S UTC'), nc),
                 c(DC, f'  {tz_name.lower():<6}', nc) + c(BW, dt_local.strftime(f'%Y-%m-%d %H:%M:%S {tz_name}'), nc),
                 c(DC, '  iso   ', nc) + c(BW, dt_utc.isoformat(), nc)]
        if value is not None:
            lines.append(c(DC, '  rel   ', nc) + c(BW, _rel(now - ts), nc))
        lines.append(sep(nc))
        lines.append(hint(nc, '  /epoch/{unix|YYYY-MM-DD|YYYY-MM-DDTHH:MM:SS}'))
        return '\n'.join(lines) + '\n'

    if value is None:
        return fmt(now)
    try:
        return fmt(float(value))
    except ValueError:
        pass
    for fmts in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y/%m/%d']:
        try:
            dt = datetime.datetime.strptime(value, fmts).replace(tzinfo=datetime.timezone.utc)
            return fmt(dt.timestamp())
        except ValueError:
            pass
    lines = [sep(nc), c(BR, f'  Cannot parse: {value}', nc),
             hint(nc, '  Formats: unix timestamp, YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS'),
             sep(nc)]
    return '\n'.join(lines) + '\n'

# ── /dns ─────────────────────────────────────────────────────────────────
DNS_TYPES = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA', 'PTR']
_DOMAIN_RE = re.compile(r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?'
                        r'(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$')

def _valid_domain(d):
    return bool(d) and len(d) <= 253 and bool(_DOMAIN_RE.match(d))

def do_dns(domain, rtype, nc):
    if not _valid_domain(domain):
        lines = [sep(nc), c(BR, f'  Invalid domain: {domain[:60]}', nc), sep(nc)]
        return '\n'.join(lines) + '\n'
    rtype = rtype.upper()
    if rtype not in DNS_TYPES:
        rtype = 'A'
    try:
        res = subprocess.run(
            ['dig', '+short', '+time=5', domain, rtype],
            capture_output=True, text=True, timeout=10)
        records = [r.strip() for r in res.stdout.strip().splitlines() if r.strip()]
        lines = [sep(nc),
                 c(BC, f'  {domain}', nc) + c(DC, f'  [{rtype}]', nc),
                 '']
        if records:
            for r in records:
                lines.append(c(BG, '  → ', nc) + c(BW, r, nc))
        else:
            lines.append(c(D, '  (no records)', nc))
        lines.append(sep(nc))
        others = [t for t in DNS_TYPES if t != rtype]
        lines.append(hint(nc, '  /dns/{domain}/{type}  types: ' + ' '.join(others)))
    except Exception as e:
        lines = [sep(nc), c(BR, f'  Error: {e}', nc), sep(nc)]
    return '\n'.join(lines) + '\n'

def do_dns_help(nc):
    lines = [sep(nc), c(BC, '  dns lookup', nc), '',
             c(BW, '  $ curl clilap.org/dns/google.com', nc),
             c(BW, '  $ curl clilap.org/dns/google.com/MX', nc),
             c(D, f'  types: {", ".join(DNS_TYPES)}', nc),
             sep(nc)]
    return '\n'.join(lines) + '\n'

# ── /whois ─────────────────────────────────────────────────────────────────
_WHOIS_PATTERNS = [
    ('Registrar',    r'Registrar:\s*(.+)'),
    ('Created',      r'(?:Creation Date|Created|Registered On?):\s*(.+)'),
    ('Expires',      r'(?:Registry Expiry Date|Expir(?:y|ation) Date|Expiry):\s*(.+)'),
    ('Updated',      r'Updated Date:\s*(.+)'),
    ('Status',       r'Domain Status:\s*(\S+)'),
    ('Name Servers', r'Name Server:\s*(.+)'),
]

def do_whois(domain, nc):
    if not _valid_domain(domain):
        lines = [sep(nc), c(BR, f'  Invalid domain: {domain[:60]}', nc), sep(nc)]
        return '\n'.join(lines) + '\n'
    try:
        res = subprocess.run(['whois', domain], capture_output=True, text=True, timeout=15)
        raw = res.stdout
        found = {}
        for key, pat in _WHOIS_PATTERNS:
            m = re.findall(pat, raw, re.IGNORECASE)
            if m:
                if key == 'Name Servers':
                    found[key] = '  '.join(dict.fromkeys(x.strip().lower() for x in m[:4]))
                else:
                    found[key] = m[0].strip()[:70]
        lines = [sep(nc), c(BC, f'  whois: {domain}', nc), '']
        if found:
            for k, v in found.items():
                lines.append(c(DC, f'  {k:<14}', nc) + c(BW, v, nc))
        else:
            for line in raw.splitlines()[:25]:
                if line.strip() and not line.startswith('%'):
                    lines.append('  ' + line.strip()[:70])
        lines.append(sep(nc))
    except Exception as e:
        lines = [sep(nc), c(BR, f'  Error: {e}', nc), sep(nc)]
    return '\n'.join(lines) + '\n'

# ── /color ─────────────────────────────────────────────────────────────────
def do_color(value, nc):
    value = value.lstrip('#').strip()
    try:
        if ',' in value:
            parts = [int(x.strip()) for x in value.split(',')]
            r, g, b = parts[0], parts[1], parts[2]
            hex_val = f'{r:02x}{g:02x}{b:02x}'
        else:
            h = value.lower()
            if len(h) == 3:
                h = h[0]*2 + h[1]*2 + h[2]*2
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            hex_val = h
    except Exception:
        lines = [sep(nc), c(BR, f'  Cannot parse: {value}', nc),
                 hint(nc, '  /color/ff6b6b  or  /color/255,107,107'),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    hls = colorsys.rgb_to_hls(r/255, g/255, b/255)
    hue = int(hls[0] * 360)
    lum = int(hls[1] * 100)
    sat = int(hls[2] * 100)
    swatch = f'\x1b[48;2;{r};{g};{b}m     \x1b[0m'

    lines = [sep(nc),
             f'  {swatch}  ' + c(BY, f'#{hex_val.upper()}', nc),
             '',
             c(DC, '  hex  ', nc) + c(BY,  f'#{hex_val.upper()}', nc),
             c(DC, '  rgb  ', nc) + c(BW,  f'rgb({r}, {g}, {b})', nc),
             c(DC, '  hsl  ', nc) + c(BW,  f'hsl({hue}, {sat}%, {lum}%)', nc),
             sep(nc)]
    lines.append(hint(nc, '  /color/{hex}  or  /color/{R,G,B}'))
    return '\n'.join(lines) + '\n'

def do_color_help(nc):
    lines = [sep(nc), c(BC, '  color', nc), '',
             c(BW, '  $ curl clilap.org/color/ff6b6b', nc),
             c(BW, '  $ curl clilap.org/color/255,107,107', nc),
             c(D,  '  shows hex / rgb / hsl + terminal swatch', nc),
             sep(nc)]
    return '\n'.join(lines) + '\n'

# ── Handler ───────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def _send(self, body, html=False, status=200):
        ct = 'text/html; charset=utf-8' if html else 'text/plain; charset=utf-8'
        self.send_response(status)
        self.send_header('Content-Type', ct)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body.encode('utf-8'))

    def _read_body(self):
        length = min(int(self.headers.get('Content-Length', 0)), 1_048_576)  # 1 MB cap
        return self.rfile.read(length) if length > 0 else b''

    def _dispatch(self, method):
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        ua = self.headers.get('User-Agent', '')
        browser = is_browser(ua)
        nc = 'nocolor' in qs or 'nc' in qs or browser

        parts = [p for p in parsed.path.split('/') if p]
        service = parts[0] if parts else ''
        args = parts[1:]

        body_bytes = self._read_body() if method == 'POST' else b''

        def respond(text):
            if browser:
                self._send(html_wrap(text, service), html=True)
            else:
                self._send(text)

        # /headers
        if service == 'headers':
            respond(do_headers(dict(self.headers), nc))

        # /uuid
        elif service == 'uuid':
            try:
                n = int(args[0]) if args else int(qs.get('n', ['1'])[0])
            except (ValueError, IndexError):
                n = 1
            respond(do_uuid(n, nc))

        # /b64
        elif service == 'b64':
            if not args:
                respond(do_b64_help(nc)); return
            action = args[0]
            if action not in ('encode', 'decode'):
                respond(do_b64_help(nc)); return
            data = body_bytes if body_bytes else unquote('/'.join(args[1:])) if len(args) > 1 else ''
            respond(do_b64(action, data, nc))

        # /hash
        elif service == 'hash':
            if not args:
                respond(do_hash_help(nc)); return
            algo = args[0]
            data = body_bytes if body_bytes else unquote('/'.join(args[1:])).encode() if len(args) > 1 else b''
            respond(do_hash(algo, data, nc))

        # /epoch
        elif service == 'epoch':
            value = unquote(args[0]) if args else None
            respond(do_epoch(value, nc))

        # /dns
        elif service == 'dns':
            if not args:
                respond(do_dns_help(nc)); return
            domain = args[0]
            rtype = args[1] if len(args) > 1 else 'A'
            respond(do_dns(domain, rtype, nc))

        # /whois
        elif service == 'whois':
            if not args:
                lines = [sep(nc), c(BC, '  whois', nc), '',
                         c(BW, '  $ curl clilap.org/whois/google.com', nc),
                         sep(nc)]
                respond('\n'.join(lines) + '\n'); return
            respond(do_whois(args[0], nc))

        # /color
        elif service == 'color':
            if not args:
                respond(do_color_help(nc)); return
            respond(do_color(unquote('/'.join(args)), nc))

        else:
            self._send('Not found\n', status=404)

    def do_GET(self):
        try:
            self._dispatch('GET')
        except Exception:
            try:
                self._send('Internal error\n', status=500)
            except Exception:
                pass

    def do_POST(self):
        try:
            self._dispatch('POST')
        except Exception:
            try:
                self._send('Internal error\n', status=500)
            except Exception:
                pass

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    print(f'utils server listening on 127.0.0.1:{PORT}')
    server.serve_forever()
