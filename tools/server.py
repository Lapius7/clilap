#!/usr/bin/env python3
"""Tools server for clilap.org — computational utilities on port 3214."""

import base64, calendar, cgi, difflib, hashlib, io, json, os, random, re
import secrets, string, subprocess, time, unicodedata
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote, quote, unquote_plus
from urllib.request import urlopen, Request
from urllib.error import URLError

PORT = 3214

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
Y  = '\x1b[33m'

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

def html_wrap(ansi_text, title='Clilap Tools'):
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{_CSS}</style></head>'
            f'<body><pre>{ansi_to_html(ansi_text)}</pre>{_FOOTER}</body></html>')

def sep(nc=False): return '═' * 60 if nc else DC + '═' * 60 + R
def cc(code, text, nc): return text if nc else code + text + R
def hint(text, nc): return cc(DC, '  ' + text, nc)


# ── /password ────────────────────────────────────────────────────────────────

_WORDS = [
    'apple','brave','cloud','dance','ember','flame','grace','honey',
    'image','joker','karma','lemon','maple','noble','ocean','piano',
    'quest','river','storm','tiger','ultra','vivid','water','xenon',
    'yacht','zebra','amber','blast','coral','drift','eagle','frost',
    'globe','haven','inner','jewel','knack','lunar','magic','night',
    'olive','pulse','quick','radar','solar','trout','under','vapor',
    'witch','xylem','young','zonal','arena','bison','crisp','delta',
    'epoch','flair','gizmo','haste','input','jumbo','knife','lathe',
    'mirth','nerve','optic','prose','quota','rhyme','scale','torch',
]

def do_password(args, qs, nc):
    no_sym = 'no-symbols' in qs or 'ns' in qs
    phrase  = args and args[0] == 'phrase'

    if phrase:
        n_words = 4
        try: n_words = max(3, min(10, int(args[1]) if len(args) > 1 else 4))
        except (ValueError, IndexError): pass
        words = [secrets.choice(_WORDS) for _ in range(n_words)]
        sep_chars = ['-', '.', '_', '+']
        sep_ch = secrets.choice(sep_chars)
        pw = sep_ch.join(w.capitalize() if secrets.randbelow(2) else w for w in words)
        pw += str(secrets.randbelow(9000) + 1000)
        lines = [sep(nc),
                 cc(BC, '  パスフレーズ生成', nc),
                 '',
                 '  ' + cc(BG, pw, nc),
                 '',
                 cc(DC, f'  ワード数: {n_words}  文字数: {len(pw)}', nc),
                 sep(nc),
                 hint('/password/phrase/5  — 5ワードのパスフレーズ', nc)]
        return '\n'.join(lines) + '\n'

    length = 20
    try: length = max(8, min(128, int(args[0]))) if args else 20
    except (ValueError, TypeError): pass

    chars = string.ascii_letters + string.digits
    if not no_sym:
        chars += '!@#$%^&*-_=+'

    while True:
        pw = ''.join(secrets.choice(chars) for _ in range(length))
        has_upper = any(c.isupper() for c in pw)
        has_lower = any(c.islower() for c in pw)
        has_digit = any(c.isdigit() for c in pw)
        has_sym   = not no_sym and any(c in '!@#$%^&*-_=+' for c in pw)
        if has_upper and has_lower and has_digit and (no_sym or has_sym):
            break

    strength = '弱い'
    if   length >= 20 and not no_sym: strength = '強い'
    elif length >= 16:                 strength = '良い'
    elif length >= 12:                 strength = '普通'

    lines = [sep(nc),
             cc(BC, '  パスワード生成', nc),
             '',
             '  ' + cc(BG, pw, nc),
             '',
             cc(DC, '  文字数:  ', nc) + cc(BW, str(length), nc),
             cc(DC, '  記号:    ', nc) + cc(BW, 'なし' if no_sym else 'あり', nc),
             cc(DC, '  強度:    ', nc) + cc(BW, strength, nc),
             sep(nc),
             hint('/password/32             — 32文字のパスワード', nc),
             hint('/password/phrase         — パスフレーズ (単語の組み合わせ)', nc),
             hint('/password?no-symbols     — 英数字のみ', nc)]
    return '\n'.join(lines) + '\n'


# ── /base ────────────────────────────────────────────────────────────────────

def do_base(args, nc):
    if len(args) < 2:
        lines = [sep(nc),
                 cc(BC, '  進数変換', nc),
                 '',
                 cc(D, '  使い方: /base/{変換元進数}/{値}', nc),
                 cc(D, '          /base/{変換元進数}/{変換先進数}/{値}', nc),
                 '',
                 cc(BW, '  $ curl clilap.org/base/10/255', nc),
                 cc(BW, '  $ curl clilap.org/base/16/ff', nc),
                 cc(BW, '  $ curl clilap.org/base/2/10/1010', nc),
                 cc(BW, '  $ curl clilap.org/base/10/2/255', nc),
                 '',
                 cc(DC, '  対応進数: 2 8 10 16', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    try:
        if len(args) == 2:
            from_base = int(args[0])
            value_str = args[1].upper()
            decimal   = int(value_str, from_base)
            targets   = [b for b in [2, 8, 10, 16] if b != from_base]
        else:
            from_base = int(args[0])
            to_base   = int(args[1])
            value_str = args[2].upper()
            decimal   = int(value_str, from_base)
            targets   = [to_base]

        if from_base not in [2, 8, 10, 16]:
            raise ValueError('対応進数: 2, 8, 10, 16')

        def to_str(n, base):
            if   base == 2:  return bin(n)[2:]
            elif base == 8:  return oct(n)[2:]
            elif base == 10: return str(n)
            elif base == 16: return hex(n)[2:].upper()

        prefix = {2:'0b', 8:'0o', 10:'', 16:'0x'}
        base_name = {2:'2進数', 8:'8進数', 10:'10進数', 16:'16進数'}

        lines = [sep(nc),
                 cc(BC, '  進数変換', nc),
                 '',
                 cc(DC, f'  入力  ', nc) + cc(BW, f'{prefix[from_base]}{value_str}', nc) +
                 cc(D, f'  ({base_name[from_base]})', nc),
                 '']
        for b in targets:
            result = to_str(decimal, b)
            lines.append(cc(DC, f'  {b}進数  ', nc) + cc(BG, f'{prefix[b]}{result}', nc))
        lines += [sep(nc),
                  hint('/base/10/255           — 10進数から全進数に変換', nc),
                  hint('/base/16/ff            — 16進数から全進数に変換', nc),
                  hint('/base/10/2/255         — 10進数 → 2進数', nc)]
        return '\n'.join(lines) + '\n'

    except (ValueError, IndexError) as e:
        lines = [sep(nc), cc(BR, f'  エラー: {e}', nc), sep(nc)]
        return '\n'.join(lines) + '\n'


# ── /urlencode /urldecode ────────────────────────────────────────────────────

def do_urlencode(text, nc):
    encoded = quote(text, safe='')
    lines = [sep(nc),
             cc(DC, '  入力     ', nc) + cc(BW, text[:200], nc),
             cc(DC, '  エンコード', nc) + cc(BG, encoded[:400], nc),
             sep(nc),
             hint('/urlencode/{テキスト}', nc)]
    return '\n'.join(lines) + '\n'

def do_urldecode(text, nc):
    try:
        decoded = unquote_plus(text)
        lines = [sep(nc),
                 cc(DC, '  入力     ', nc) + cc(BW, text[:200], nc),
                 cc(DC, '  デコード  ', nc) + cc(BG, decoded[:400], nc),
                 sep(nc),
                 hint('/urldecode/{テキスト}', nc)]
    except Exception as e:
        lines = [sep(nc), cc(BR, f'  エラー: {e}', nc), sep(nc)]
    return '\n'.join(lines) + '\n'


# ── /cal ─────────────────────────────────────────────────────────────────────

def do_cal(args, nc):
    now = datetime.now()
    year = now.year
    month = None
    try:
        if len(args) >= 2:
            year  = int(args[0])
            month = int(args[1])
        elif len(args) == 1:
            year = int(args[0])
    except ValueError:
        pass

    DOW = ['月', '火', '水', '木', '金', '土', '日']
    today = (now.year, now.month, now.day)

    def render_month(y, m):
        cal = calendar.monthcalendar(y, m)
        title = f'{y}年{m}月'
        header = cc(BC, title.center(18), nc)
        dow_row = cc(DC, ' '.join(DOW), nc)
        rows = [header, dow_row]
        for week in cal:
            cells = []
            for i, day in enumerate(week):
                if day == 0:
                    cells.append('  ')
                elif (y, m, day) == today:
                    cells.append(cc(BW, f'{day:2}', nc))
                elif i >= 5:
                    cells.append(cc(Y, f'{day:2}', nc))
                else:
                    cells.append(f'{day:2}')
            rows.append(' '.join(cells))
        return rows

    lines = [sep(nc), cc(BC, '  カレンダー', nc), '']

    if month:
        for row in render_month(year, month):
            lines.append('  ' + row)
    else:
        for start_m in range(1, 13, 3):
            months_rows = [render_month(year, m) for m in range(start_m, min(start_m+3, 13))]
            max_rows = max(len(r) for r in months_rows)
            for i in range(max_rows):
                row_parts = []
                for mr in months_rows:
                    row_parts.append((mr[i] if i < len(mr) else '').ljust(22))
                lines.append('  ' + '  '.join(row_parts))
            lines.append('')

    lines += [sep(nc),
              hint('/cal                   — 今年のカレンダー', nc),
              hint('/cal/2026              — 指定年', nc),
              hint('/cal/2026/3            — 2026年3月', nc)]
    return '\n'.join(lines) + '\n'


# ── /cron ─────────────────────────────────────────────────────────────────────

_WEEKDAYS_JP = ['日', '月', '火', '水', '木', '金', '土']
_MONTHS_JP   = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月']

def _cron_field_jp(val, unit, names=None):
    def name(n):
        try: i = int(n); return names[i] if names and 0 <= i < len(names) else n
        except: return n

    if val == '*':    return f'毎{unit}'
    if val.startswith('*/'):
        return f'{val[2:]}{unit}おき'
    if ',' in val:
        return '、'.join(name(v) for v in val.split(','))
    if '-' in val and '/' not in val:
        a, b = val.split('-', 1)
        return f'{name(a)}〜{name(b)}'
    if '/' in val:
        rng, step = val.split('/', 1)
        base = '毎' if rng == '*' else f'{rng}から'
        return f'{base}{step}{unit}おき'
    return name(val)

def do_cron(expr, nc):
    expr = expr.strip()

    presets = {
        '@yearly':   '0 0 1 1 *',
        '@annually': '0 0 1 1 *',
        '@monthly':  '0 0 1 * *',
        '@weekly':   '0 0 * * 0',
        '@daily':    '0 0 * * *',
        '@midnight': '0 0 * * *',
        '@hourly':   '0 * * * *',
        '@reboot':   None,
    }
    if expr in presets:
        if expr == '@reboot':
            desc = '起動時に実行'
        else:
            expr = presets[expr]

    fields = expr.split() if expr not in presets else expr.split()
    if len(fields) != 5:
        lines = [sep(nc),
                 cc(BR, '  cron式が不正です (フィールドは5つ必要)', nc),
                 cc(D,  '  書式: 分 時 日 月 曜日', nc),
                 cc(BW, '  例: 0 9 * * 1-5', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    minute, hour, dom, month, dow = fields

    parts = []
    if minute == '0' and hour != '*':
        h_desc = _cron_field_jp(hour, '時')
        if not any(h_desc.endswith(s) for s in ['時', 'おき']):
            h_desc += '時'
        parts.append(f'{h_desc}00分')
    else:
        parts.append(f'{_cron_field_jp(minute, "分")}')
        if hour != '*':
            parts.append(f'{_cron_field_jp(hour, "時")}')

    if dow != '*':
        parts.append(f'{_cron_field_jp(dow, "曜日", _WEEKDAYS_JP)}曜日')
    elif dom != '*':
        parts.append(f'{_cron_field_jp(dom, "日")}')

    if month != '*':
        parts.append(f'{_cron_field_jp(month, "月", _MONTHS_JP)}')

    desc = '、'.join(parts) + 'に実行'

    lines = [sep(nc),
             cc(BC, '  cron式', nc),
             '',
             cc(BW, f'  {expr}', nc),
             '',
             cc(DC, '  説明', nc),
             cc(BG, f'  {desc}', nc),
             '',
             cc(DC, '  フィールド', nc),
             cc(D,  f'  {"分":<12} {minute}', nc),
             cc(D,  f'  {"時":<12} {hour}', nc),
             cc(D,  f'  {"日 (月内)":<12} {dom}', nc),
             cc(D,  f'  {"月":<12} {month}', nc),
             cc(D,  f'  {"曜日":<12} {dow}', nc),
             sep(nc),
             hint('/cron/0_9_*_*_1-5      — 平日9時 (スペースは_に)', nc),
             hint('/cron/@daily            — プリセット (@daily @weekly @hourly など)', nc)]
    return '\n'.join(lines) + '\n'


# ── /json ─────────────────────────────────────────────────────────────────────

def do_json(body_bytes, qs, nc):
    if not body_bytes:
        lines = [sep(nc),
                 cc(BC, '  JSONフォーマッター', nc),
                 '',
                 cc(D, '  JSONをPOSTしてフォーマット・バリデートします:', nc),
                 cc(BW, '  $ curl -d @file.json clilap.org/json', nc),
                 cc(BW, "  $ echo '{\"a\":1}' | curl -d @- clilap.org/json", nc),
                 '',
                 cc(DC, '  オプション:', nc),
                 cc(D,  '  ?indent=N    — インデント幅 (デフォルト: 2)', nc),
                 cc(D,  '  ?compact     — コンパクト表示 (空白なし)', nc),
                 cc(D,  '  ?keys        — キーをソート', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'
    try:
        indent = None if 'compact' in qs else int(qs.get('indent', ['2'])[0])
        sort_keys = 'keys' in qs
        data = json.loads(body_bytes)
        formatted = json.dumps(data, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
        n_chars = len(body_bytes)
        n_keys  = len(data) if isinstance(data, dict) else len(data) if isinstance(data, list) else 1
        type_map = {'dict': 'オブジェクト', 'list': '配列', 'str': '文字列',
                    'int': '数値', 'float': '数値', 'bool': '真偽値', 'NoneType': 'null'}
        type_name = type_map.get(type(data).__name__, type(data).__name__)
        lines = [sep(nc),
                 cc(BC, '  JSON', nc) + cc(DC, f'  {type_name}  {n_keys}件  {n_chars}バイト', nc),
                 '']
        for line in formatted.splitlines()[:500]:
            lines.append('  ' + line)
        lines += ['', sep(nc)]
        return '\n'.join(lines) + '\n'
    except json.JSONDecodeError as e:
        lines = [sep(nc), cc(BR, f'  JSONエラー: {e}', nc), sep(nc)]
        return '\n'.join(lines) + '\n'


# ── /totp ─────────────────────────────────────────────────────────────────────

import hmac, struct

def _totp(secret_b32, digits=6, period=30):
    try:
        s = secret_b32.upper().replace(' ', '')
        padding = (8 - len(s) % 8) % 8
        secret_bytes = base64.b32decode(s + '=' * padding, casefold=True)
    except Exception:
        raise ValueError('Base32シークレットが不正です')
    ts = int(time.time()) // period
    msg = struct.pack('>Q', ts)
    h = hmac.new(secret_bytes, msg, hashlib.sha1).digest()
    offset = h[-1] & 0x0F
    code = struct.unpack('>I', h[offset:offset+4])[0] & 0x7FFFFFFF
    otp = str(code % (10 ** digits)).zfill(digits)
    remaining = period - (int(time.time()) % period)
    return otp, remaining

def do_totp(secret, nc):
    if not secret:
        lines = [sep(nc),
                 cc(BC, '  TOTP生成', nc),
                 '',
                 cc(D, '  使い方: /totp/{BASE32シークレット}', nc),
                 cc(BW, '  $ curl clilap.org/totp/JBSWY3DPEHPK3PXP', nc),
                 '',
                 cc(BR, '  ⚠ 実際の認証コードをHTTP経由で送信しないでください', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'
    try:
        otp, remaining = _totp(secret)
        bar_len = 20
        filled = int(bar_len * remaining / 30)
        bar = '█' * filled + '░' * (bar_len - filled)
        lines = [sep(nc),
                 cc(BC, '  TOTP', nc),
                 '',
                 cc(BG, f'  {otp}', nc),
                 '',
                 cc(DC, f'  有効期限   ', nc) + cc(BW, f'あと{remaining}秒', nc),
                 cc(DC, f'  残り時間   ', nc) + cc(Y, bar, nc),
                 sep(nc),
                 hint('/totp/{BASE32シークレット}', nc)]
    except ValueError as e:
        lines = [sep(nc), cc(BR, f'  エラー: {e}', nc), sep(nc)]
    return '\n'.join(lines) + '\n'


# ── /ascii ─────────────────────────────────────────────────────────────────────

_FIGLET_FONTS = [
    'banner', 'big', 'block', 'bubble', 'digital', 'ivrit', 'lean',
    'mini', 'script', 'shadow', 'slant', 'small', 'smscript', 'smslant',
    'speed', 'standard', 'term', 'thin', 'ogre', 'larry3d', 'roman',
]

def do_ascii(text, qs, nc):
    if not text:
        lines = [sep(nc),
                 cc(BC, '  ASCIIアート生成', nc),
                 '',
                 cc(D, '  使い方: /ascii/{テキスト}', nc),
                 cc(BW, '  $ curl clilap.org/ascii/Hello', nc),
                 cc(BW, '  $ curl "clilap.org/ascii/Hi?font=banner"', nc),
                 '',
                 cc(DC, f'  フォント: {" ".join(_FIGLET_FONTS[:8])} ...', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    font = qs.get('font', ['standard'])[0]
    if font not in _FIGLET_FONTS:
        font = 'standard'

    safe_text = re.sub(r'[^\x20-\x7e]', '', text[:80])
    if not safe_text:
        safe_text = text[:40]

    try:
        result = subprocess.run(
            ['figlet', '-f', font, '--', safe_text],
            capture_output=True, text=True, timeout=5)
        art = result.stdout.rstrip()
    except Exception:
        art = safe_text

    lines = [sep(nc), cc(BC, f'  ASCIIアート  [{font}]', nc), '']
    for line in art.splitlines():
        lines.append(cc(BW, line, nc))
    lines += ['', sep(nc),
              hint(f'/ascii/{{テキスト}}?font={font}', nc),
              hint(f'フォント: {" ".join(_FIGLET_FONTS[:6])} ...', nc)]
    return '\n'.join(lines) + '\n'


# ── /unit ─────────────────────────────────────────────────────────────────────

def _make_unit_map(upper_start, lower_start, digit_start=None, upper_exc=None, lower_exc=None):
    m = {}
    for i, ch in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
        m[ch] = upper_exc.get(ch, chr(upper_start + i)) if upper_exc else chr(upper_start + i)
    for i, ch in enumerate('abcdefghijklmnopqrstuvwxyz'):
        m[ch] = lower_exc.get(ch, chr(lower_start + i)) if lower_exc else chr(lower_start + i)
    if digit_start:
        for i, ch in enumerate('0123456789'):
            m[ch] = chr(digit_start + i)
    return m

_UNITS = {
    # 長さ: base = meter
    'm':1,'km':1e3,'cm':1e-2,'mm':1e-3,'mi':1609.344,'ft':0.3048,
    'in':0.0254,'yd':0.9144,'nm':1e-9,'um':1e-6,'mile':1609.344,
    'foot':0.3048,'feet':0.3048,'inch':0.0254,'meter':1,'kilometer':1e3,

    # 重さ: base = kg
    'kg':1,'g':1e-3,'mg':1e-6,'t':1e3,'lb':0.453592,'oz':0.028349,
    'pound':0.453592,'gram':1e-3,'ton':1e3,

    # 時間: base = second
    's':1,'ms':1e-3,'us':1e-6,'ns':1e-9,'min':60,'h':3600,
    'd':86400,'w':604800,'week':604800,'month':2592000,'year':31536000,
    'second':1,'minute':60,'hour':3600,'day':86400,

    # データ: base = byte
    'B':1,'KB':1e3,'MB':1e6,'GB':1e9,'TB':1e12,'PB':1e15,
    'KiB':1024,'MiB':1048576,'GiB':1073741824,'TiB':1099511627776,
    'byte':1,'bytes':1,

    # 速度: base = m/s
    'mps':1,'kph':1/3.6,'mph':0.44704,'knot':0.514444,
    'km/h':1/3.6,'m/s':1,
}

_TEMP_UNITS = {'c', 'f', 'k', 'celsius', 'fahrenheit', 'kelvin'}

def _convert_temp(val, frm, to):
    frm, to = frm.lower()[0], to.lower()[0]
    if frm == 'c': c = val
    elif frm == 'f': c = (val - 32) * 5/9
    else: c = val - 273.15
    if to == 'c': return c
    elif to == 'f': return c * 9/5 + 32
    else: return c + 273.15

def _parse_value_unit(s):
    m = re.match(r'^(-?[\d.]+(?:e[+-]?\d+)?)\s*(.+)$', s, re.IGNORECASE)
    if not m: raise ValueError(f'パースできません: {s}')
    return float(m.group(1)), m.group(2).strip()

def do_unit(args, nc):
    if len(args) < 2:
        lines = [sep(nc), cc(BC, '  単位変換', nc), '',
                 cc(D, '  使い方: /unit/{値}{単位}/{変換先単位}', nc),
                 cc(BW, '  $ curl clilap.org/unit/100km/mi', nc),
                 cc(BW, '  $ curl clilap.org/unit/1024MB/GB', nc),
                 cc(BW, '  $ curl clilap.org/unit/100C/F', nc),
                 cc(BW, '  $ curl clilap.org/unit/3600s/h', nc),
                 '',
                 cc(DC, '  カテゴリ: 長さ  重さ  時間  データ  速度  温度', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'
    try:
        val, from_unit = _parse_value_unit(unquote(args[0]))
        to_unit = unquote(args[1])

        fu = from_unit.lower().rstrip('s') if from_unit.lower() not in _UNITS else from_unit
        tu = to_unit.lower().rstrip('s') if to_unit.lower() not in _UNITS else to_unit

        if from_unit.lower().rstrip('s') in _TEMP_UNITS or from_unit.upper() in ('C','F','K'):
            result = _convert_temp(val, from_unit, to_unit)
            fmt_r = f'{result:.4g}'
            lines = [sep(nc),
                     cc(BC, '  単位変換', nc), '',
                     cc(BW, f'  {val} {from_unit}', nc) + cc(DC, '  =  ', nc) + cc(BG, f'{fmt_r} {to_unit}', nc),
                     sep(nc)]
            return '\n'.join(lines) + '\n'

        from_factor = _UNITS.get(from_unit) or _UNITS.get(from_unit.lower()) or _UNITS.get(fu)
        to_factor   = _UNITS.get(to_unit)   or _UNITS.get(to_unit.lower())   or _UNITS.get(tu)

        if from_factor is None:
            raise ValueError(f'未知の単位: {from_unit}')
        if to_factor is None:
            raise ValueError(f'未知の単位: {to_unit}')

        result = val * from_factor / to_factor
        fmt_v = f'{val:g}'
        fmt_r = f'{result:.6g}'

        lines = [sep(nc), cc(BC, '  単位変換', nc), '',
                 cc(BW, f'  {fmt_v} {from_unit}', nc) + cc(DC, '  =  ', nc) + cc(BG, f'{fmt_r} {to_unit}', nc),
                 sep(nc),
                 hint('/unit/100km/mi         — 距離', nc),
                 hint('/unit/1024MB/GiB       — データサイズ', nc),
                 hint('/unit/100C/F           — 温度', nc)]
        return '\n'.join(lines) + '\n'

    except (ValueError, ZeroDivisionError) as e:
        lines = [sep(nc), cc(BR, f'  エラー: {e}', nc), sep(nc)]
        return '\n'.join(lines) + '\n'


# ── /mock ─────────────────────────────────────────────────────────────────────

_FIRST_NAMES = ['Alice','Bob','Carol','Dave','Eve','Frank','Grace','Hiro',
                'Iris','Jack','Kate','Leo','Maya','Nate','Olivia','Paul',
                'Quinn','Ruby','Sam','Tina','Uma','Victor','Wendy','Xena',
                'Yuki','Zach']
_LAST_NAMES  = ['Smith','Johnson','Williams','Brown','Jones','Garcia',
                'Miller','Davis','Wilson','Moore','Taylor','Anderson',
                'Thomas','Jackson','White','Harris','Martin','Thompson',
                'Young','Tanaka','Sato','Suzuki']
_CITIES      = ['Tokyo','New York','London','Paris','Sydney','Toronto',
                'Berlin','Seoul','Singapore','Dubai','Osaka','Chicago']
_DOMAINS     = ['gmail.com','yahoo.com','hotmail.com','outlook.com',
                'example.com','test.org','mail.net']
_LOREM_WORDS = ('lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod '
                'tempor incididunt ut labore et dolore magna aliqua ut enim ad minim '
                'veniam quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea '
                'commodo consequat duis aute irure dolor in reprehenderit in voluptate '
                'velit esse cillum dolore eu fugiat nulla pariatur excepteur sint '
                'occaecat cupidatat non proident sunt in culpa qui officia deserunt '
                'mollit anim id est laborum').split()

def _fake_user(seed=None):
    rng = random.Random(seed)
    first = rng.choice(_FIRST_NAMES)
    last  = rng.choice(_LAST_NAMES)
    return {
        'id':        str(__import__('uuid').uuid4()),
        'name':      f'{first} {last}',
        'email':     f'{first.lower()}.{last.lower()}{rng.randint(1,99)}@{rng.choice(_DOMAINS)}',
        'age':       rng.randint(18, 65),
        'city':      rng.choice(_CITIES),
        'active':    rng.choice([True, False]),
        'createdAt': f'2024-{rng.randint(1,12):02d}-{rng.randint(1,28):02d}T'
                     f'{rng.randint(0,23):02d}:{rng.randint(0,59):02d}:00Z',
    }

def _lorem_para(rng, min_s=4, max_s=8):
    n_sentences = rng.randint(min_s, max_s)
    sentences = []
    for _ in range(n_sentences):
        n_words = rng.randint(8, 18)
        words = [rng.choice(_LOREM_WORDS) for _ in range(n_words)]
        words[0] = words[0].capitalize()
        sentences.append(' '.join(words) + '.')
    return ' '.join(sentences)

def do_mock(args, nc):
    kind = args[0] if args else 'json'
    try:
        n = max(1, min(50, int(args[1]))) if len(args) > 1 else 1
    except (ValueError, IndexError):
        n = 1

    rng = random.Random()

    if kind == 'lorem':
        lines = [sep(nc), cc(BC, f'  Lorem Ipsum  [{n}段落]', nc), '']
        for i in range(n):
            para = _lorem_para(rng)
            lines.append(f'  {para}')
            if i < n-1: lines.append('')
        lines += [sep(nc), hint('/mock/lorem/3    — 3段落', nc)]
        return '\n'.join(lines) + '\n'

    items = [_fake_user(rng.randint(0, 999999)) for _ in range(n)]
    if n == 1:
        out = json.dumps(items[0], indent=2, ensure_ascii=False)
    else:
        out = json.dumps(items, indent=2, ensure_ascii=False)

    lines = [sep(nc), cc(BC, f'  モックJSON  [{n}件]', nc), '']
    for line in out.splitlines()[:300]:
        lines.append('  ' + line)
    if len(out.splitlines()) > 300:
        lines.append(cc(D, '  ... (省略)', nc))
    lines += ['', sep(nc),
              hint('/mock/json/5     — 偽ユーザー5件', nc),
              hint('/mock/lorem/3   — Lorem 3段落', nc)]
    return '\n'.join(lines) + '\n'


# ── /md ─────────────────────────────────────────────────────────────────────

def _inline_md(text, nc):
    text = re.sub(r'\*\*(.+?)\*\*', lambda m: cc(BW, m.group(1), nc), text)
    text = re.sub(r'__(.+?)__',     lambda m: cc(BW, m.group(1), nc), text)
    text = re.sub(r'\*(.+?)\*',     lambda m: cc(D,  m.group(1), nc), text)
    text = re.sub(r'_(.+?)_',       lambda m: cc(D,  m.group(1), nc), text)
    text = re.sub(r'`(.+?)`',       lambda m: cc(C,  m.group(1), nc), text)
    text = re.sub(r'\[(.+?)\]\((.+?)\)',
                  lambda m: cc(C, m.group(1), nc) + cc(D, f'({m.group(2)})', nc), text)
    return text

def do_md(body_bytes, nc):
    if not body_bytes:
        lines = [sep(nc), cc(BC, '  Markdownレンダリング', nc), '',
                 cc(D, '  MarkdownテキストをPOSTしてください:', nc),
                 cc(BW, '  $ curl -d @README.md clilap.org/md', nc),
                 cc(BW, '  $ cat file.md | curl -d @- clilap.org/md', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    text = body_bytes.decode('utf-8', errors='replace')
    lines = [sep(nc)]
    in_code = False
    for raw in text.splitlines()[:500]:
        if raw.startswith('```'):
            in_code = not in_code
            if in_code:
                lang = raw[3:].strip()
                lines.append(cc(DC, f'  ▸ {lang}' if lang else '  ▸ コード', nc))
            continue
        if in_code:
            lines.append(cc(C, '  ' + raw, nc)); continue
        if raw.startswith('# '):
            w = 58
            lines += [cc(DC, '  ' + '─'*w, nc), cc(BW, '  ' + raw[2:], nc), cc(DC, '  ' + '─'*w, nc)]
        elif raw.startswith('## '):
            lines.append(cc(BC, '  ── ' + raw[3:], nc))
        elif raw.startswith('### '):
            lines.append(cc(BW, '  ' + raw[4:], nc))
        elif raw.startswith('> '):
            lines.append(cc(D, '  │ ' + _inline_md(raw[2:], nc), nc))
        elif re.match(r'^[-*+] ', raw):
            lines.append(f'  {cc(C, "•", nc)} {_inline_md(raw[2:], nc)}')
        elif re.match(r'^\d+\. ', raw):
            m = re.match(r'^(\d+)\. (.+)', raw)
            if m: lines.append(f'  {cc(C, m.group(1)+".", nc)} {_inline_md(m.group(2), nc)}')
        elif re.match(r'^-{3,}$', raw):
            lines.append(cc(DC, '  ' + '─'*58, nc))
        else:
            lines.append(_inline_md('  ' + raw, nc))
    lines += [sep(nc)]
    return '\n'.join(lines) + '\n'


# ── /gitignore ───────────────────────────────────────────────────────────────

_GITIGNORE_ALIASES = {
    'node': 'Node', 'nodejs': 'Node', 'js': 'Node', 'javascript': 'Node',
    'python': 'Python', 'py': 'Python', 'django': 'Python', 'flask': 'Python',
    'rust': 'Rust', 'go': 'Go', 'golang': 'Go',
    'java': 'Java', 'kotlin': 'Kotlin', 'scala': 'Scala',
    'ruby': 'Ruby', 'rails': 'Rails',
    'php': 'PHP', 'laravel': 'PHP',
    'c': 'C', 'cpp': 'C++', 'c++': 'C++',
    'swift': 'Swift', 'objc': 'Objective-C',
    'macos': 'macOS', 'mac': 'macOS', 'osx': 'macOS',
    'windows': 'Windows', 'win': 'Windows',
    'linux': 'Linux',
    'vim': 'Vim', 'emacs': 'Emacs',
    'vscode': 'VisualStudioCode', 'vs': 'VisualStudio',
    'jetbrains': 'JetBrains', 'intellij': 'JetBrains', 'idea': 'JetBrains',
    'terraform': 'Terraform', 'android': 'Android', 'unity': 'Unity',
    'flutter': 'Flutter', 'dart': 'Dart', 'r': 'R',
    'haskell': 'Haskell', 'elm': 'Elm', 'elixir': 'Elixir',
    'ts': 'Node', 'typescript': 'Node',
    'react': 'Node', 'vue': 'Node', 'angular': 'Node', 'svelte': 'Node',
    'nextjs': 'Node', 'nuxt': 'Node',
}

def _fetch_gitignore(name):
    url = f'https://raw.githubusercontent.com/github/gitignore/main/{name}.gitignore'
    req = Request(url, headers={'User-Agent': 'clilap.org/1.0'})
    try:
        with urlopen(req, timeout=8) as r:
            return r.read().decode('utf-8')
    except URLError:
        return None

def do_gitignore(lang_str, nc):
    if not lang_str:
        lines = [sep(nc), cc(BC, '  .gitignore生成', nc), '',
                 cc(D, '  使い方: /gitignore/{言語}', nc),
                 cc(D, '          /gitignore/{言語1},{言語2}', nc),
                 cc(BW, '  $ curl clilap.org/gitignore/node', nc),
                 cc(BW, '  $ curl clilap.org/gitignore/python,macos,vscode', nc),
                 '',
                 cc(DC, '  主な対応言語: node python rust go java ruby php macos windows', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    langs = [l.strip().lower() for l in lang_str.split(',') if l.strip()]
    lines = [sep(nc)]
    for lang in langs[:5]:
        name = _GITIGNORE_ALIASES.get(lang, lang.capitalize())
        content = _fetch_gitignore(name)
        if content is None:
            lines.append(cc(BR, f'  # 見つかりません: {name}.gitignore', nc))
            lines.append('')
            continue
        lines.append(cc(BC, f'  ### {name} ###', nc))
        for l in content.splitlines():
            if l.startswith('#'):
                lines.append(cc(DC, l, nc))
            elif l.strip():
                lines.append(cc(BW, l, nc))
            else:
                lines.append('')
        lines.append('')
    lines += [sep(nc), hint('/gitignore/node,python,macos — 複数言語を組み合わせ', nc)]
    return '\n'.join(lines) + '\n'


# ── /license ─────────────────────────────────────────────────────────────────

_LICENSES = {
    'mit':         'MIT',
    'apache':      'Apache-2.0',
    'apache-2.0':  'Apache-2.0',
    'gpl':         'GPL-3.0',
    'gpl-3':       'GPL-3.0',
    'gpl-3.0':     'GPL-3.0',
    'gpl-2':       'GPL-2.0',
    'gpl-2.0':     'GPL-2.0',
    'lgpl':        'LGPL-2.1',
    'lgpl-2.1':    'LGPL-2.1',
    'lgpl-3':      'LGPL-3.0',
    'mpl':         'MPL-2.0',
    'mpl-2.0':     'MPL-2.0',
    'isc':         'ISC',
    'bsd-2':       'BSD-2-Clause',
    'bsd-3':       'BSD-3-Clause',
    'unlicense':   'Unlicense',
    'agpl':        'AGPL-3.0',
    'agpl-3.0':    'AGPL-3.0',
    'cc0':         'CC0-1.0',
    'wtfpl':       'WTFPL',
}

def _fetch_license(spdx_id, holder, year):
    url = f'https://api.github.com/licenses/{spdx_id.lower()}'
    req = Request(url, headers={'User-Agent': 'clilap.org/1.0',
                                'Accept': 'application/vnd.github.v3+json'})
    try:
        with urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
    except URLError:
        return None, None
    body = data.get('body', '')
    body = body.replace('[year]', str(year)).replace('[fullname]', holder)
    body = body.replace('[yyyy]', str(year)).replace('[name of copyright owner]', holder)
    return data.get('name', spdx_id), body

def do_license(args, qs, nc):
    if not args:
        lines = [sep(nc), cc(BC, '  ライセンステキスト', nc), '',
                 cc(D, '  使い方: /license/{タイプ}', nc),
                 cc(BW, '  $ curl clilap.org/license/mit', nc),
                 cc(BW, '  $ curl "clilap.org/license/apache?holder=Lapius7"', nc),
                 '',
                 cc(DC, '  対応タイプ: ' + ' '.join(sorted(set(_LICENSES.values()))), nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    key = args[0].lower()
    spdx = _LICENSES.get(key, key.upper())
    holder = qs.get('holder', [''])[0] or qs.get('name', ['Your Name'])[0]
    year   = qs.get('year', [str(datetime.now().year)])[0]

    name, body = _fetch_license(spdx, holder, year)
    if body is None:
        lines = [sep(nc), cc(BR, f'  ライセンスが見つかりません: {spdx}', nc),
                 cc(D, f'  対応: mit  apache  gpl  lgpl  bsd-2  bsd-3  isc  unlicense', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    lines = [sep(nc), cc(BC, f'  {name}', nc), '']
    for l in body.splitlines():
        lines.append('  ' + cc(D, l, nc) if l.strip() else '')
    lines += ['', sep(nc), hint(f'/license/{key}?holder=あなたの名前', nc)]
    return '\n'.join(lines) + '\n'


# ── /diff ─────────────────────────────────────────────────────────────────────

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
            parts[name_m.group(1)] = content.decode('utf-8', errors='replace')
    return parts

def do_diff(body_bytes, content_type, nc):
    if not body_bytes:
        lines = [sep(nc), cc(BC, '  差分表示', nc), '',
                 cc(D, '  2つのファイルをmultipart/form-dataでPOSTしてください:', nc),
                 cc(BW, '  $ curl -F "a=@old.txt" -F "b=@new.txt" clilap.org/diff', nc),
                 cc(BW, '  $ curl -F "a=@file1" -F "b=@file2" clilap.org/diff', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    try:
        ct = content_type or ''
        if 'multipart' in ct:
            fields = _parse_multipart(body_bytes, ct)
            text_a = fields.get('a', fields.get('file1', fields.get('old', '')))
            text_b = fields.get('b', fields.get('file2', fields.get('new', '')))
        else:
            text = body_bytes.decode('utf-8', errors='replace')
            halves = text.split('\0', 1)
            text_a, text_b = (halves[0], halves[1]) if len(halves) == 2 else ('', text)

        a_lines = text_a.splitlines(keepends=True)
        b_lines = text_b.splitlines(keepends=True)
        diff = list(difflib.unified_diff(a_lines, b_lines, fromfile='a', tofile='b', n=3))

        lines = [sep(nc), cc(BC, '  差分', nc), '']
        if not diff:
            lines.append(cc(BG, '  ファイルは同一です', nc))
        else:
            added = deleted = 0
            for d in diff[:500]:
                d = d.rstrip('\n')
                if d.startswith('+++') or d.startswith('---'):
                    lines.append(cc(DC, '  ' + d, nc))
                elif d.startswith('@@'):
                    lines.append(cc(Y, '  ' + d, nc))
                elif d.startswith('+'):
                    lines.append(cc(BG, '  ' + d, nc)); added += 1
                elif d.startswith('-'):
                    lines.append(cc(BR, '  ' + d, nc)); deleted += 1
                else:
                    lines.append(cc(D, '  ' + d, nc))
            lines += ['', cc(BG, f'  +{added}行追加', nc) + '  ' + cc(BR, f'-{deleted}行削除', nc)]
        lines += [sep(nc),
                  hint('curl -F "a=@old.txt" -F "b=@new.txt" clilap.org/diff', nc)]
        return '\n'.join(lines) + '\n'
    except Exception as e:
        lines = [sep(nc), cc(BR, f'  エラー: {e}', nc), sep(nc)]
        return '\n'.join(lines) + '\n'


# ── /unicode ─────────────────────────────────────────────────────────────────

_FANCY_MAPS = {
    'bold':        _make_unit_map(0x1D400, 0x1D41A, 0x1D7CE),
    'italic':      _make_unit_map(0x1D434, 0x1D44E, lower_exc={'h': 'ℎ'}),
    'bolditalic':  _make_unit_map(0x1D468, 0x1D482),
    'script':      _make_unit_map(0x1D49C, 0x1D4B6,
                     upper_exc={'B':'ℬ','E':'ℰ','F':'ℱ','H':'ℋ',
                                'I':'ℐ','L':'ℒ','M':'ℳ','R':'ℛ'},
                     lower_exc={'e':'ℯ','g':'ℊ','o':'ℴ'}),
    'boldscript':  _make_unit_map(0x1D4D0, 0x1D4EA),
    'gothic':      _make_unit_map(0x1D504, 0x1D51E,
                     upper_exc={'C':'ℭ','H':'ℌ','I':'ℑ',
                                'R':'ℜ','Z':'ℨ'}),
    'boldgothic':  _make_unit_map(0x1D56C, 0x1D586),
    'doublestruck':_make_unit_map(0x1D538, 0x1D552, 0x1D7D8,
                     upper_exc={'C':'ℂ','H':'ℍ','N':'ℕ','P':'ℙ',
                                'Q':'ℚ','R':'ℝ','Z':'ℤ'}),
    'sans':        _make_unit_map(0x1D5A0, 0x1D5BA, 0x1D7E2),
    'sansbold':    _make_unit_map(0x1D5D4, 0x1D5EE, 0x1D7EC),
    'sansitalic':  _make_unit_map(0x1D608, 0x1D622),
    'monospace':   _make_unit_map(0x1D670, 0x1D68A, 0x1D7F6),
    'circled':     dict(zip('abcdefghijklmnopqrstuvwxyz',
                           [chr(0x24D0+i) for i in range(26)])),
    'squared':     dict(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ',
                           [chr(0x1F130+i) for i in range(26)])),
    'bubble':      dict(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789',
                           [chr(0x24B6+i) for i in range(26)] +
                           [chr(0x24D0+i) for i in range(26)] +
                           [chr(0x24EA)] + [chr(0x2460+i) for i in range(9)])),
}

def _apply_fancy(text, style):
    m = _FANCY_MAPS.get(style, {})
    result = []
    for ch in text:
        result.append(m.get(ch, m.get(ch.upper(), m.get(ch.lower(), ch))))
    return ''.join(result)

def do_unicode_char(char, nc):
    if not char:
        return do_unicode_help(nc)
    lines = [sep(nc), cc(BC, f'  Unicode: {char[:1]}', nc), '']
    for ch in char[:8]:
        cp  = ord(ch)
        name = unicodedata.name(ch, '不明')
        cat  = unicodedata.category(ch)
        lines += [
            cc(DC, '  文字        ', nc) + cc(BW, ch, nc),
            cc(DC, '  コードポイント', nc) + cc(BG, f'U+{cp:04X}', nc),
            cc(DC, '  名前        ', nc) + cc(BW, name, nc),
            cc(DC, '  カテゴリ    ', nc) + cc(D, cat, nc),
            cc(DC, '  UTF-8      ', nc) + cc(D, ' '.join(f'{b:02X}' for b in ch.encode('utf-8')), nc),
            cc(DC, '  10進数      ', nc) + cc(D, str(cp), nc),
            '',
        ]
    lines.append(sep(nc))
    return '\n'.join(lines) + '\n'

def do_unicode_inspect(body_bytes, nc):
    if not body_bytes:
        lines = [sep(nc), cc(BC, '  Unicode文字検査', nc), '',
                 cc(D, '  テキストをPOSTして各文字を検査します:', nc),
                 cc(BW, '  $ echo "Hello, 世界" | curl -d @- clilap.org/unicode/inspect', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'
    text = body_bytes.decode('utf-8', errors='replace').strip()[:200]
    lines = [sep(nc), cc(BC, '  Unicode文字検査', nc), '',
             cc(DC, f'  {"文字":<8} {"U+":<8} {"名前":<35} カテゴリ  UTF-8', nc)]
    for ch in text:
        cp   = ord(ch)
        name = unicodedata.name(ch, '?')[:34]
        cat  = unicodedata.category(ch)
        utf8 = ' '.join(f'{b:02X}' for b in ch.encode('utf-8'))
        disp = repr(ch)[1:-1] if ord(ch) < 32 else ch
        lines.append(f'  {cc(BW, disp, nc):<8} {cc(BG, f"U+{cp:04X}", nc):<8} {cc(D, name, nc):<35} {cat:<9}{cc(DC, utf8, nc)}')
    lines.append(sep(nc))
    return '\n'.join(lines) + '\n'

def do_unicode_search(query, nc):
    if not query:
        return do_unicode_help(nc)
    q = query.upper()
    lines = [sep(nc), cc(BC, f'  Unicode検索: {query}', nc), '']
    count = 0
    for cp in range(0x20, 0x10000):
        try:
            name = unicodedata.name(chr(cp))
            if q in name:
                ch = chr(cp)
                lines.append(f'  {cc(BW, ch, nc)}  {cc(BG, f"U+{cp:04X}", nc)}  {cc(D, name, nc)}')
                count += 1
                if count >= 40: break
        except ValueError:
            pass
    if not count:
        lines.append(cc(D, '  結果なし', nc))
    lines += ['', cc(DC, f'  {count}件', nc), sep(nc)]
    return '\n'.join(lines) + '\n'

def do_unicode_fancy(style, text, nc):
    if not text or not style:
        styles = list(_FANCY_MAPS.keys())
        lines = [sep(nc), cc(BC, '  Unicodeファンシーテキスト', nc), '',
                 cc(D, '  使い方: /unicode/fancy/{スタイル}/{テキスト}', nc),
                 cc(BW, '  $ curl clilap.org/unicode/fancy/bold/Hello', nc),
                 '',
                 cc(DC, f'  スタイル一覧:', nc)]
        for s in styles:
            sample = _apply_fancy('Hello', s)
            label = cc(C, s + ':', nc)
            pad = ' ' * max(0, 14 - len(s))
            lines.append(f'  {label}{pad} {sample}')
        lines.append(sep(nc))
        return '\n'.join(lines) + '\n'

    result = _apply_fancy(text, style)
    lines = [sep(nc), cc(BC, f'  ファンシーテキスト: {style}', nc), '',
             cc(D, f'  入力:  {text}', nc),
             f'  出力:  {result}',
             sep(nc),
             hint(f'/unicode/fancy/{style}/{text}', nc)]
    return '\n'.join(lines) + '\n'

def do_regex(pattern, body_bytes, qs, nc):
    if not pattern:
        lines = [sep(nc), cc(BC, '  正規表現テスト (Python re)', nc), '',
                 cc(BW, '  $ curl clilap.org/regex/{パターン}', nc) + cc(D, '           — マッチ例・非マッチ例を表示', nc),
                 cc(BW, '  $ echo "text" | curl -d @- clilap.org/regex/{パターン}', nc) + cc(D, '  — テキストに対してマッチ', nc),
                 cc(BW, '  $ curl -T pattern.txt clilap.org/regex/', nc) + cc(D, '             — ファイルでパターン送信', nc),
                 cc(BW, '  $ curl -T pattern.txt "clilap.org/regex/?text=hello"', nc) + cc(D, '  — ファイル+テキスト', nc),
                 '',
                 cc(DC, '  使用例:', nc),
                 hint(r'curl clilap.org/regex/%5Cd%7B3%7D-%5Cd%7B4%7D          # \d{3}-\d{4}', nc),
                 hint(r'curl clilap.org/regex/%5B0-9a-f%5D%7B6%7D              # [0-9a-f]{6}', nc),
                 hint(r'curl clilap.org/regex/%5Cw%2B%40%5Cw%2B%5C.%5Cw%2B    # \w+@\w+\.\w+', nc),
                 hint(r'echo "Hello World" | curl -d @- clilap.org/regex/hello', nc),
                 hint(r'echo "test@example.com" | curl -d @- clilap.org/regex/%5Cw%2B%40%5Cw%2B%5C.%5Cw%2B', nc),
                 '',
                 cc(DC, '  フラグ (?flags=):', nc),
                 hint('i  — 大文字小文字無視 (ignorecase)', nc),
                 hint('m  — 複数行モード (multiline)', nc),
                 hint('s  — . が改行にもマッチ (dotall)', nc),
                 hint('x  — 拡張モード (verbose)', nc),
                 hint('im — 複数フラグ組み合わせ可', nc),
                 '',
                 cc(DC, '  特殊文字のURLエンコード:', nc),
                 hint(r'\  →  %5C    {  →  %7B    }  →  %7D    ^  →  %5E', nc),
                 hint(r'$  →  %24    +  →  %2B    ?  →  %3F    |  →  %7C', nc),
                 hint(r'[  →  %5B    ]  →  %5D    (  →  %28    )  →  %29', nc),
                 hint(r'→ 複雑なパターンは curl -T でファイルから送ると楽', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    text = body_bytes.decode('utf-8', errors='replace') if body_bytes else ''

    flag_str = ''.join(qs.get('flags', [''])).lower()
    flags = 0
    if 'i' in flag_str: flags |= re.IGNORECASE
    if 'm' in flag_str: flags |= re.MULTILINE
    if 's' in flag_str: flags |= re.DOTALL
    if 'x' in flag_str: flags |= re.VERBOSE

    try:
        compiled = re.compile(pattern, flags)
    except re.error as e:
        lines = [sep(nc),
                 cc(BR, '  エラー: 正規表現が無効です', nc), '',
                 hint(f'パターン: {pattern}', nc),
                 hint(f'エラー:   {e}', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    if not text:
        lines = [sep(nc), cc(BC, '  正規表現パターン確認', nc), '',
                 hint(f'パターン: {pattern}', nc),
                 hint(f'フラグ:   {flag_str or "なし"}', nc), '']

        try:
            import rstr as _rstr
            match_samples = []
            for _ in range(30):
                try:
                    s = _rstr.xeger(pattern)
                    if compiled.search(s) and s not in match_samples and len(s) <= 40:
                        match_samples.append(s)
                    if len(match_samples) >= 5:
                        break
                except Exception:
                    break

            # マッチ例を各種変形して非マッチを生成（1例につき複数の変形を試して最初の成功を採用）
            _transforms = [
                lambda s: re.sub(r'\d', 'X', s, count=1),
                lambda s: re.sub(r'\d+', 'X', s, count=1),
                lambda s: re.sub(r'[a-zA-Z]', '0', s, count=1),
                lambda s: re.sub(r'\w', '!', s, count=1),
                lambda s: s[1:] if len(s) > 1 else None,
                lambda s: s[:-1] if len(s) > 1 else None,
                lambda s: s + '!!',
                lambda s: s.upper() if s != s.upper() else None,
                lambda s: s.replace('-', '_') if '-' in s else None,
                lambda s: re.sub(r'[^\w]', 'Z', s, count=1),
            ]
            nomatch_derived = []
            for idx, s in enumerate(match_samples):
                # 各マッチ例ごとに異なる変形から試す（偏り防止）
                ordered = _transforms[idx % len(_transforms):] + _transforms[:idx % len(_transforms)]
                for fn in ordered:
                    try:
                        broken = fn(s)
                    except Exception:
                        continue
                    if broken and broken != s and not compiled.search(broken) and broken not in nomatch_derived and len(broken) <= 40:
                        nomatch_derived.append(broken)
                        break

            _nomatch_pool = [
                '', 'abc', '123', 'hello world', '!!!',
                '日本語', '2024-01-01', 'test@example.com',
                'http://example.com', 'null', 'あいうえお',
                'xyz789', '!@#$%', '00000', 'HELLO', ' ', '\n',
            ]
            nomatch_from_pool = [s for s in _nomatch_pool
                                 if not compiled.search(s) and s not in nomatch_derived]
            nomatch_samples = (nomatch_derived + nomatch_from_pool)[:5]

            if match_samples:
                lines.append(cc(BG, f'  ✓ マッチする ({len(match_samples)}件):', nc))
                for s in match_samples:
                    lines.append(cc(BG, '    ✓ ', nc) + cc(C, repr(s), nc))
                lines.append('')
            if nomatch_samples:
                lines.append(cc(BR, f'  ✗ マッチしない ({len(nomatch_samples)}件):', nc))
                for s in nomatch_samples:
                    lines.append(cc(BR, '    ✗ ', nc) + cc(DC, repr(s), nc))
                lines.append('')
        except Exception:
            pass

        lines += [cc(D, '  テスト文字列を送信してマッチ確認:', nc),
                  cc(BW, f'  $ echo "Hello World" | curl -d @- clilap.org/regex/{quote(pattern)}', nc),
                  cc(BW, f'  $ curl -T pattern.txt "clilap.org/regex/?text=Hello+World"', nc),
                  sep(nc)]
        return '\n'.join(lines) + '\n'

    matches = list(compiled.finditer(text))
    lines = [sep(nc), cc(BC, '  正規表現テスト結果', nc), '']
    lines.append(hint(f'パターン: {pattern}', nc))
    if flag_str:
        lines.append(hint(f'フラグ:   {flag_str}', nc))
    lines.append('')

    if not matches:
        lines.append(cc(BY, '  マッチなし', nc))
    else:
        lines.append(cc(BG, f'  マッチ数: {len(matches)}', nc))
        lines.append('')
        for i, m in enumerate(matches, 1):
            lines.append(cc(BW, f'  [{i}] ', nc) + cc(C, repr(m.group(0)), nc))
            lines.append(hint(f'位置: {m.start()}-{m.end()}', nc))
            if m.groups():
                for gi, g in enumerate(m.groups(), 1):
                    lines.append(hint(f'グループ {gi}: {repr(g)}', nc))
            if m.groupdict():
                for name, val in m.groupdict().items():
                    lines.append(hint(f'名前付きグループ {name}: {repr(val)}', nc))

    lines.append(sep(nc))
    return '\n'.join(lines) + '\n'


def do_unicode_help(nc):
    lines = [sep(nc), cc(BC, '  Unicodeツール', nc), '',
             cc(BW, '  $ curl clilap.org/unicode/A', nc) + cc(D, '         — 文字情報', nc),
             cc(BW, '  $ echo "Hi世界" | curl -d @- clilap.org/unicode/inspect', nc),
             cc(BW, '  $ curl clilap.org/unicode/search/star', nc) + cc(D, '  — 名前で検索', nc),
             cc(BW, '  $ curl clilap.org/unicode/fancy/bold/Hello', nc),
             cc(BW, '  $ curl clilap.org/unicode/fancy', nc) + cc(D, '  — スタイル一覧', nc),
             '',
             cc(DC, '  スタイル: ' + '  '.join(_FANCY_MAPS.keys()), nc),
             sep(nc)]
    return '\n'.join(lines) + '\n'


# ── Handler ───────────────────────────────────────────────────────────────────

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
        length = min(int(self.headers.get('Content-Length', 0)), 4_194_304)
        return self.rfile.read(length) if length > 0 else b''

    def _dispatch(self, method):
        parsed = urlparse(self.path)
        qs     = parse_qs(parsed.query, keep_blank_values=True)
        ua     = self.headers.get('User-Agent', '')
        browser = is_browser(ua)
        nc     = 'nocolor' in qs or 'nc' in qs

        parts   = [p for p in parsed.path.split('/') if p]
        service = parts[0] if parts else ''
        args    = [unquote(p) for p in parts[1:]]

        body_bytes = self._read_body() if method in ('POST', 'PUT') else b''

        def respond(text):
            if browser:
                self._send(html_wrap(text, f'{service} — Clilap'), html=True)
            else:
                self._send(text)

        if service == 'password':
            respond(do_password(args, qs, nc))
        elif service == 'base':
            respond(do_base(args, nc))
        elif service == 'urlencode':
            text = body_bytes.decode('utf-8', errors='replace') if body_bytes else unquote('/'.join(parts[1:]))
            respond(do_urlencode(text, nc))
        elif service == 'urldecode':
            text = body_bytes.decode('utf-8', errors='replace') if body_bytes else unquote('/'.join(parts[1:]))
            respond(do_urldecode(text, nc))
        elif service == 'cal':
            respond(do_cal(args, nc))
        elif service == 'cron':
            expr = ' '.join(args).replace('_', ' ')
            respond(do_cron(expr, nc))
        elif service == 'json':
            respond(do_json(body_bytes, qs, nc))
        elif service == 'totp':
            respond(do_totp(args[0] if args else '', nc))
        elif service == 'ascii':
            text = unquote('/'.join(parts[1:]))
            respond(do_ascii(text, qs, nc))
        elif service == 'unit':
            respond(do_unit(args, nc))
        elif service == 'mock':
            respond(do_mock(args, nc))
        elif service == 'md':
            respond(do_md(body_bytes, nc))
        elif service == 'gitignore':
            respond(do_gitignore(unquote('/'.join(parts[1:])), nc))
        elif service == 'license':
            respond(do_license(args, qs, nc))
        elif service == 'diff':
            ct = self.headers.get('Content-Type', '')
            respond(do_diff(body_bytes, ct, nc))
        elif service == 'regex':
            if method == 'PUT' and body_bytes:
                # curl -T pattern.txt clilap.org/regex/
                # curl -T pattern.txt "clilap.org/regex/?text=hello+world"
                pattern = body_bytes.decode('utf-8', errors='replace').strip()
                text_param = qs.get('text', [''])[0]
                test_text = text_param.encode('utf-8') if text_param else b''
                respond(do_regex(pattern, test_text, qs, nc))
            else:
                pattern = unquote('/'.join(parts[1:]))
                respond(do_regex(pattern, body_bytes, qs, nc))
        elif service == 'unicode':
            sub = args[0] if args else ''
            if sub == 'inspect':
                respond(do_unicode_inspect(body_bytes, nc))
            elif sub == 'search':
                respond(do_unicode_search(' '.join(args[1:]), nc))
            elif sub == 'fancy':
                style = args[1] if len(args) > 1 else ''
                text  = unquote('/'.join(parts[3:])) if len(parts) > 3 else ''
                respond(do_unicode_fancy(style, text, nc))
            elif sub:
                respond(do_unicode_char(sub, nc))
            else:
                respond(do_unicode_help(nc))
        else:
            self._send('Not found\n', status=404)

    def do_GET(self):
        try: self._dispatch('GET')
        except Exception: self._send('Internal error\n', status=500)

    def do_POST(self):
        try: self._dispatch('POST')
        except Exception: self._send('Internal error\n', status=500)

    def do_PUT(self):
        try: self._dispatch('PUT')
        except Exception: self._send('Internal error\n', status=500)


if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    print(f'tools server listening on 127.0.0.1:{PORT}')
    server.serve_forever()
