#!/usr/bin/env python3
"""Realtime log sharing server for clilap.org.

HTTP (port 3218): PUT receives a streaming log (curl -T -), GET serves the
viewer page / raw log / grep-filtered log. WebSocket (port 3219): pushes
new lines to connected viewers in realtime.
"""

import asyncio, json, os, re, secrets, threading, time
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import websockets

PORT    = 3218
WS_PORT = 3219
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data')
os.makedirs(DATA_DIR, exist_ok=True)

RING_LIMIT = 10_000        # lines kept in memory per stream
READ_CHUNK = 4096

BROWSER_KEYS = ('mozilla', 'webkit', 'trident', 'opera')
def is_browser(ua): return any(k in ua.lower() for k in BROWSER_KEYS)

# ANSI
R  = '\x1b[0m'
D  = '\x1b[2m'
C  = '\x1b[36m'
BC = '\x1b[1;36m'
BW = '\x1b[1;37m'
DC = '\x1b[2;36m'
BY = '\x1b[1;33m'

def cc(code, text, nc): return text if nc else code + text + R

def _cmd(cmd, comment, nc, width=58):
    pad = ' ' * max(1, width - len(cmd))
    return f'  {cc(BC, cmd, nc)}{pad}{cc(D, comment, nc)}'

_A2H = {
    '1':'font-weight:bold','2':'color:#5c6370',
    '36':'color:#56b6c2','1;33':'color:#e5c07b;font-weight:bold',
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

_HELP_CSS = ('*{box-sizing:border-box;margin:0;padding:0}'
             'body{background:#000;color:#aaa;font-family:"Courier New",Consolas,Monaco,monospace;'
             'font-size:12px;line-height:1.5;padding:16px}'
             'pre{font-family:inherit;white-space:pre;margin:0;overflow-x:auto}')

def html_wrap_help(ansi_text, title='log - Clilap'):
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{_HELP_CSS}</style></head>'
            f'<body><pre>{ansi_to_html(ansi_text)}</pre></body></html>')

_CSS = ('*{box-sizing:border-box;margin:0;padding:0}'
        'body{background:#000;color:#aaa;font-family:"Courier New",Consolas,Monaco,monospace;'
        'font-size:13px;line-height:1.45;padding:48px 16px 16px}'
        '#log{white-space:pre-wrap;word-break:break-all}'
        '#status{position:fixed;top:8px;right:12px;font-size:11px;color:#555}'
        '#filter{position:fixed;top:6px;left:12px;background:#111;border:1px solid #333;'
        'color:#aaa;font-family:inherit;font-size:12px;padding:4px 8px;width:240px;z-index:10}'
        '.connected{color:#4ec9b0}.disconnected{color:#e06c75}')


# ── per-stream state ─────────────────────────────────────────────────────────

class Stream:
    def __init__(self, sid):
        self.id = sid
        self.lock = threading.Lock()
        self.lines = []          # ring buffer of decoded text lines (ANSI kept)
        self.path = os.path.join(DATA_DIR, f'{sid}.log')
        self.secret_path = os.path.join(DATA_DIR, f'{sid}.secret')
        self.closed = False

    def append(self, text_chunk):
        with self.lock:
            with open(self.path, 'a', encoding='utf-8', errors='replace') as f:
                f.write(text_chunk)
            self.lines.append(text_chunk)
            if len(self.lines) > RING_LIMIT:
                self.lines = self.lines[-RING_LIMIT:]

    def full_text(self):
        with self.lock:
            return ''.join(self.lines)

    def load_from_disk(self):
        if os.path.exists(self.path):
            with open(self.path, 'r', encoding='utf-8', errors='replace') as f:
                self.lines = [f.read()]


_streams = {}        # id -> Stream
_streams_lock = threading.Lock()

def get_stream(sid, create=False):
    with _streams_lock:
        s = _streams.get(sid)
        if s is None and create:
            s = Stream(sid)
            _streams[sid] = s
        elif s is None:
            s = Stream(sid)
            s.load_from_disk()
            if os.path.exists(s.path):
                _streams[sid] = s
            else:
                return None
        return s

def new_id():
    sid = secrets.token_hex(4)
    while os.path.exists(os.path.join(DATA_DIR, f'{sid}.log')):
        sid = secrets.token_hex(4)
    return sid

def issue_stream():
    """Create a new stream id + write-secret pair, persisted to disk."""
    sid = new_id()
    secret = secrets.token_hex(16)
    stream = get_stream(sid, create=True)
    with open(stream.secret_path, 'w', encoding='utf-8') as f:
        f.write(secret)
    return sid, secret

def check_secret(sid, secret):
    secret_path = os.path.join(DATA_DIR, f'{sid}.secret')
    if not os.path.exists(secret_path):
        return False
    with open(secret_path, 'r', encoding='utf-8') as f:
        return f.read().strip() == secret


# ── asyncio WebSocket server (runs in its own thread) ──────────────────────────

_ws_loop = None
_subscribers = {}          # id -> set of websocket connections
_subscribers_lock = threading.Lock()

async def _ws_handler(ws):
    try:
        path = ws.request.path
    except AttributeError:
        path = ws.path
    parts = [p for p in urlparse(path).path.split('/') if p]
    if not parts:
        await ws.close(code=4000, reason='missing stream id')
        return
    sid = parts[0]
    qs = parse_qs(urlparse(path).query)
    grep_pattern = qs.get('grep', [''])[0]

    stream = get_stream(sid)
    if stream is None:
        await ws.close(code=4004, reason='not found')
        return

    with _subscribers_lock:
        _subscribers.setdefault(sid, set()).add(ws)

    try:
        backlog = stream.full_text()
        if grep_pattern:
            try:
                rx = re.compile(grep_pattern)
                backlog = '\n'.join(l for l in backlog.splitlines() if rx.search(l))
            except re.error:
                pass
        await ws.send(json.dumps({'type': 'backlog', 'text': backlog}))
        async for _ in ws:
            pass  # viewers don't send anything meaningful; ignore
    except websockets.exceptions.ConnectionClosed:
        pass
    finally:
        with _subscribers_lock:
            _subscribers.get(sid, set()).discard(ws)

def broadcast(sid, text_chunk):
    if _ws_loop is None:
        return
    with _subscribers_lock:
        conns = list(_subscribers.get(sid, ()))
    if not conns:
        return
    payload = json.dumps({'type': 'append', 'text': text_chunk})
    for ws in conns:
        asyncio.run_coroutine_threadsafe(_safe_send(ws, payload), _ws_loop)

async def _safe_send(ws, payload):
    try:
        await ws.send(payload)
    except websockets.exceptions.ConnectionClosed:
        pass

def _run_ws_server():
    global _ws_loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    _ws_loop = loop

    async def main():
        async with websockets.serve(_ws_handler, '127.0.0.1', WS_PORT):
            await asyncio.Future()

    loop.run_until_complete(main())


# ── viewer HTML ──────────────────────────────────────────────────────────────

def render_viewer_html(sid, ws_authority, ws_path_prefix):
    return f'''<!DOCTYPE html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>log/{sid} - Clilap</title><style>{_CSS}</style></head>
<body>
<input id="filter" placeholder="grep filter (regex)...">
<span id="status" class="disconnected">connecting...</span>
<div id="log"></div>
<script>
const sid = {json.dumps(sid)};
const ansiUp = (s) => s
  .replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')
  .replace(/\\x1b\\[0m/g, '</span>')
  .replace(/\\x1b\\[1m/g, '<span style="font-weight:bold">')
  .replace(/\\x1b\\[2m/g, '<span style="color:#5c6370">')
  .replace(/\\x1b\\[31m/g, '<span style="color:#e06c75">')
  .replace(/\\x1b\\[32m/g, '<span style="color:#98c379">')
  .replace(/\\x1b\\[33m/g, '<span style="color:#e5c07b">')
  .replace(/\\x1b\\[34m/g, '<span style="color:#61afef">')
  .replace(/\\x1b\\[35m/g, '<span style="color:#c678dd">')
  .replace(/\\x1b\\[36m/g, '<span style="color:#56b6c2">')
  .replace(/\\x1b\\[1;3\\dm/g, m => '<span style="font-weight:bold">')
  .replace(/\\x1b\\[\\d+(;\\d+)*m/g, '');

const logEl = document.getElementById('log');
const statusEl = document.getElementById('status');
const filterEl = document.getElementById('filter');
let ws;

function connect() {{
  const proto = location.protocol === 'https:' ? 'wss' : 'ws';
  const grep = filterEl.value ? '?grep=' + encodeURIComponent(filterEl.value) : '';
  ws = new WebSocket(proto + '://' + {json.dumps(ws_authority)} + {json.dumps(ws_path_prefix)} + '/' + sid + grep);
  ws.onopen = () => {{ statusEl.textContent = 'live'; statusEl.className = 'connected'; }};
  ws.onclose = () => {{ statusEl.textContent = 'disconnected'; statusEl.className = 'disconnected'; setTimeout(connect, 2000); }};
  ws.onmessage = (ev) => {{
    const msg = JSON.parse(ev.data);
    if (msg.type === 'backlog') {{ logEl.innerHTML = ansiUp(msg.text); }}
    else if (msg.type === 'append') {{ logEl.innerHTML += ansiUp(msg.text); }}
    window.scrollTo(0, document.body.scrollHeight);
  }};
}}
filterEl.addEventListener('change', () => {{ if (ws) ws.close(); connect(); }});
connect();
</script>
</body></html>'''


# ── HTTP handler ─────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def log_message(self, *a): pass

    def _send_text(self, body, status=200, ct='text/plain; charset=utf-8'):
        data = body.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', ct)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_PUT(self):
        try:
            parsed = urlparse(self.path)
            parts = [p for p in parsed.path.split('/') if p]
            if len(parts) < 2:
                self._send_text('書き込みには /new で発行したIDとトークンが必要です\n', status=400)
                return
            sid, secret = parts[0], parts[1]
            if not check_secret(sid, secret):
                self._send_text('無効なトークンです\n', status=403)
                return
            stream = get_stream(sid, create=True)

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.send_header('Transfer-Encoding', 'chunked')
            self.send_header('X-Accel-Buffering', 'no')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()

            length_header = self.headers.get('Content-Length')
            te = (self.headers.get('Transfer-Encoding') or '').lower()

            if length_header is not None:
                remaining = int(length_header)
                while remaining > 0:
                    chunk = self.rfile.read(min(READ_CHUNK, remaining))
                    if not chunk:
                        break
                    remaining -= len(chunk)
                    text = chunk.decode('utf-8', errors='replace')
                    stream.append(text)
                    broadcast(sid, text)
            elif 'chunked' in te:
                while True:
                    size_line = self.rfile.readline().strip()
                    if not size_line:
                        break
                    try:
                        size = int(size_line.split(b';')[0], 16)
                    except ValueError:
                        break
                    if size == 0:
                        self.rfile.readline()
                        break
                    chunk = self.rfile.read(size)
                    self.rfile.readline()
                    text = chunk.decode('utf-8', errors='replace')
                    stream.append(text)
                    broadcast(sid, text)
            else:
                while True:
                    chunk = self.rfile.read(READ_CHUNK)
                    if not chunk:
                        break
                    text = chunk.decode('utf-8', errors='replace')
                    stream.append(text)
                    broadcast(sid, text)

            self._write_chunk(b'')
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            pass

    def _write_chunk(self, data):
        size = f'{len(data):x}\r\n'.encode('ascii')
        try:
            self.wfile.write(size + data + b'\r\n')
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            raise

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            qs = parse_qs(parsed.query, keep_blank_values=True)
            ua = self.headers.get('User-Agent', '')
            browser = is_browser(ua)
            parts = [p for p in parsed.path.split('/') if p]

            nc = 'nocolor' in qs or 'nc' in qs

            if not parts:
                host = self.headers.get('Host', '').split(':')[0]
                if browser and host == 'log.clilap.org':
                    self.send_response(302)
                    self.send_header('Location', 'https://clilap.org/log')
                    self.end_headers()
                    return
                W = 94
                SEP = '═' * W if nc else DC + '═' * W + R
                DIV = ('  ' + '─' * (W - 2)) if nc else DC + '  ' + '─' * (W - 2) + R
                lines = [SEP,
                          f'  {cc(BW, "clilap.org/log", nc)}  {cc(D, "📡 リアルタイムログ共有", nc)}',
                          DIV,
                          cc(D, 'コマンド出力やログファイルをリアルタイムでURL共有します。ANSI色は保持されます。', nc),
                          '',
                          cc(BY, '  アップロード (2段階)', nc),
                          _cmd('RES=$(curl -s clilap.org/log/new)', '# 1. ID + トークン発行', nc),
                          _cmd('UPLOAD=$(echo "$RES"|grep ^upload|cut -d" " -f2)', '', nc),
                          _cmd('tail -f app.log | curl -T - "$UPLOAD"', '# 2. ストリーム', nc),
                          _cmd('npm run dev 2>&1 | curl -T - "$UPLOAD"', '', nc),
                          '',
                          cc(BY, '  取得', nc),
                          _cmd('curl log.clilap.org/{id}', '# テキスト表示', nc),
                          _cmd('curl "log.clilap.org/{id}?grep=ERROR"', '# 正規表現フィルタ', nc),
                          '',
                          cc(D, '  ブラウザで開くとリアルタイム表示: https://log.clilap.org/{id}', nc),
                          SEP]
                text = '\n'.join(lines) + '\n'
                if browser:
                    self._send_text(html_wrap_help(text, 'log - Clilap'), ct='text/html; charset=utf-8')
                else:
                    self._send_text(text)
                return

            if parts[0] == 'new':
                sid, secret = issue_stream()
                lines = [
                    f'id:     {sid}',
                    f'upload: https://log.clilap.org/{sid}/{secret}',
                    f'view:   https://log.clilap.org/{sid}',
                ]
                self._send_text('\n'.join(lines) + '\n')
                return

            sid = parts[0]
            stream = get_stream(sid)
            if stream is None:
                self._send_text('ID が見つかりません\n', status=404)
                return

            if browser:
                host = self.headers.get('Host', 'log.clilap.org').split(':')[0]
                if host == 'localhost' or host.startswith('127.'):
                    ws_authority = f'{host}:{WS_PORT}'
                    ws_path_prefix = ''
                else:
                    ws_authority = host
                    ws_path_prefix = '/ws'
                html = render_viewer_html(sid, ws_authority, ws_path_prefix)
                self._send_text(html, ct='text/html; charset=utf-8')
                return

            text = stream.full_text()
            grep_pattern = qs.get('grep', [''])[0]
            if grep_pattern:
                try:
                    rx = re.compile(grep_pattern)
                    text = '\n'.join(l for l in text.splitlines() if rx.search(l))
                except re.error:
                    pass
            self._send_text(text)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            self._send_text('Internal error\n', status=500)


if __name__ == '__main__':
    ws_thread = threading.Thread(target=_run_ws_server, daemon=True)
    ws_thread.start()

    server = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    print(f'log server listening on 127.0.0.1:{PORT} (ws on {WS_PORT})')
    server.serve_forever()
