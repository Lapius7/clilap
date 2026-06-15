#!/usr/bin/env python3
"""Net server for clilap.org — network utilities on port 3215."""

import json, re, socket, ssl, struct, time
from datetime import datetime, timezone, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from urllib.request import urlopen, Request
from urllib.error import URLError

PORT = 3215

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

def html_wrap(ansi_text, title='Clilap Net'):
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{_CSS}</style></head>'
            f'<body><pre>{ansi_to_html(ansi_text)}</pre>{_FOOTER}</body></html>')

def sep(nc=False): return '═' * 60 if nc else DC + '═' * 60 + R
def cc(code, text, nc): return text if nc else code + text + R
def hint(text, nc): return cc(DC, '  ' + text, nc)


# ── /rate ─────────────────────────────────────────────────────────────────────

_CRYPTO_IDS = {
    'BTC': 'bitcoin', 'ETH': 'ethereum', 'XRP': 'ripple',
    'SOL': 'solana', 'ADA': 'cardano', 'DOGE': 'dogecoin',
    'DOT': 'polkadot', 'MATIC': 'matic-network', 'AVAX': 'avalanche-2',
    'LINK': 'chainlink', 'UNI': 'uniswap', 'LTC': 'litecoin',
    'BCH': 'bitcoin-cash', 'ATOM': 'cosmos', 'XLM': 'stellar',
    'BNB': 'binancecoin', 'TON': 'the-open-network', 'TRX': 'tron',
    'SHIB': 'shiba-inu', 'NEAR': 'near',
}

_FOREX_CURRENCIES = {
    'USD','EUR','JPY','GBP','AUD','CAD','CHF','CNY','HKD','NZD',
    'SEK','NOK','DKK','SGD','MXN','BRL','INR','KRW','ZAR','THB',
    'IDR','MYR','PHP','PLN','CZK','HUF','RON','ILS','AED','SAR',
}

def _fetch_forex(base):
    url = f'https://api.frankfurter.app/latest?from={base}'
    req = Request(url, headers={'User-Agent': 'clilap.org/1.0'})
    try:
        with urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except URLError:
        return None

def _fetch_crypto(symbol, vs_currencies='usd,jpy,eur,gbp'):
    cid = _CRYPTO_IDS.get(symbol.upper())
    if not cid:
        return None
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={cid}&vs_currencies={vs_currencies}&include_24hr_change=true'
    req = Request(url, headers={'User-Agent': 'clilap.org/1.0',
                                 'Accept': 'application/json'})
    try:
        with urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
            return data.get(cid)
    except URLError:
        return None

def do_rate(from_curr, targets_str, nc):
    if not from_curr:
        lines = [sep(nc), cc(BC, '  為替レート', nc), '',
                 cc(D, '  使い方: /rate/{通貨}', nc),
                 cc(D, '          /rate/{通貨1}/{通貨2}', nc),
                 cc(D, '          /rate/{暗号通貨}', nc),
                 cc(BW, '  $ curl clilap.org/rate/USD', nc),
                 cc(BW, '  $ curl clilap.org/rate/USD/JPY', nc),
                 cc(BW, '  $ curl clilap.org/rate/BTC', nc),
                 cc(BW, '  $ curl clilap.org/rate/ETH/USD', nc),
                 '',
                 cc(DC, '  ソース: Frankfurter (ECB)  ・  CoinGecko', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    symbol = from_curr.upper()
    is_crypto = symbol in _CRYPTO_IDS

    if is_crypto:
        if targets_str:
            vs = ','.join(t.lower() for t in targets_str.split(','))
        else:
            vs = 'usd,jpy,eur,gbp,btc'
        data = _fetch_crypto(symbol, vs)
        if not data:
            lines = [sep(nc), cc(BR, f'  レート取得失敗: {symbol}', nc), sep(nc)]
            return '\n'.join(lines) + '\n'

        lines = [sep(nc),
                 cc(BC, f'  {symbol}', nc) + cc(DC, '  暗号通貨  via CoinGecko', nc), '']
        for k, v in data.items():
            if k.endswith('_24h_change'): continue
            upper_k = k.upper()
            change_key = f'{k}_24h_change'
            change = data.get(change_key)
            fmt_v = f'{v:,.2f}' if v >= 1 else f'{v:.8f}'
            change_str = ''
            if change is not None:
                sign = '+' if change >= 0 else ''
                clr = BG if change >= 0 else BR
                change_str = '  ' + cc(clr, f'{sign}{change:.2f}%', nc)
            lines.append(f'  {cc(DC, upper_k+":", nc):<16} {cc(BG, fmt_v, nc)}{change_str}')
        lines += ['', sep(nc),
                  hint(f'/rate/{symbol}         — {symbol}の主要通貨建て価格', nc),
                  hint(f'/rate/{symbol}/USD     — USD建て価格のみ', nc)]
        return '\n'.join(lines) + '\n'

    data = _fetch_forex(symbol)
    if not data:
        lines = [sep(nc), cc(BR, f'  為替レート取得失敗: {symbol}', nc), sep(nc)]
        return '\n'.join(lines) + '\n'

    rates = data.get('rates', {})
    date  = data.get('date', '—')

    if targets_str:
        targets = [t.upper() for t in targets_str.split(',')]
        rates = {k: v for k, v in rates.items() if k in targets}

    lines = [sep(nc),
             cc(BC, f'  {symbol}', nc) + cc(DC, f'  為替レート  {date}  via ECB', nc), '']
    for currency, rate in sorted(rates.items()):
        lines.append(f'  {cc(DC, currency+":", nc):<16} {cc(BG, f"{rate:,.4f}", nc)}')
    lines += ['', sep(nc),
              hint(f'/rate/{symbol}              — {symbol}の全通貨レート', nc),
              hint(f'/rate/{symbol}/JPY          — {symbol}/JPY のみ', nc),
              hint(f'/rate/{symbol}/JPY,EUR,GBP  — 複数通貨', nc),
              hint('/rate/BTC               — ビットコイン価格', nc)]
    return '\n'.join(lines) + '\n'


# ── /time ─────────────────────────────────────────────────────────────────────

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
    _HAS_ZONEINFO = True
except ImportError:
    _HAS_ZONEINFO = False

_CITY_TZ = {
    'tokyo': 'Asia/Tokyo', 'osaka': 'Asia/Tokyo', 'kyoto': 'Asia/Tokyo',
    'sapporo': 'Asia/Tokyo', 'fukuoka': 'Asia/Tokyo', 'nagoya': 'Asia/Tokyo',
    'beijing': 'Asia/Shanghai', 'shanghai': 'Asia/Shanghai',
    'hong kong': 'Asia/Hong_Kong', 'hongkong': 'Asia/Hong_Kong',
    'singapore': 'Asia/Singapore', 'seoul': 'Asia/Seoul',
    'bangkok': 'Asia/Bangkok', 'jakarta': 'Asia/Jakarta',
    'kolkata': 'Asia/Kolkata', 'mumbai': 'Asia/Kolkata', 'delhi': 'Asia/Kolkata',
    'dubai': 'Asia/Dubai', 'riyadh': 'Asia/Riyadh', 'istanbul': 'Europe/Istanbul',
    'moscow': 'Europe/Moscow', 'london': 'Europe/London',
    'paris': 'Europe/Paris', 'berlin': 'Europe/Berlin',
    'amsterdam': 'Europe/Amsterdam', 'madrid': 'Europe/Madrid',
    'rome': 'Europe/Rome', 'zurich': 'Europe/Zurich',
    'stockholm': 'Europe/Stockholm', 'oslo': 'Europe/Oslo',
    'helsinki': 'Europe/Helsinki', 'warsaw': 'Europe/Warsaw',
    'prague': 'Europe/Prague', 'vienna': 'Europe/Vienna',
    'athens': 'Europe/Athens', 'lisbon': 'Europe/Lisbon',
    'new york': 'America/New_York', 'newyork': 'America/New_York',
    'boston': 'America/New_York', 'washington': 'America/New_York',
    'miami': 'America/New_York', 'atlanta': 'America/New_York',
    'chicago': 'America/Chicago', 'dallas': 'America/Chicago',
    'houston': 'America/Chicago', 'denver': 'America/Denver',
    'phoenix': 'America/Phoenix',
    'los angeles': 'America/Los_Angeles', 'losangeles': 'America/Los_Angeles',
    'san francisco': 'America/Los_Angeles', 'sanfrancisco': 'America/Los_Angeles',
    'seattle': 'America/Los_Angeles', 'portland': 'America/Los_Angeles',
    'toronto': 'America/Toronto', 'montreal': 'America/Montreal',
    'vancouver': 'America/Vancouver', 'calgary': 'America/Edmonton',
    'mexico city': 'America/Mexico_City', 'mexicocity': 'America/Mexico_City',
    'sao paulo': 'America/Sao_Paulo', 'buenos aires': 'America/Argentina/Buenos_Aires',
    'sydney': 'Australia/Sydney', 'melbourne': 'Australia/Melbourne',
    'brisbane': 'Australia/Brisbane', 'perth': 'Australia/Perth',
    'auckland': 'Pacific/Auckland', 'honolulu': 'Pacific/Honolulu',
    'cairo': 'Africa/Cairo', 'lagos': 'Africa/Lagos',
    'johannesburg': 'Africa/Johannesburg', 'nairobi': 'Africa/Nairobi',
    'utc': 'UTC', 'gmt': 'UTC',
}

_DEFAULT_CITIES = [
    ('Tokyo', 'Asia/Tokyo'), ('Beijing', 'Asia/Shanghai'),
    ('Dubai', 'Asia/Dubai'), ('Moscow', 'Europe/Moscow'),
    ('London', 'Europe/London'), ('Paris', 'Europe/Paris'),
    ('New York', 'America/New_York'), ('Chicago', 'America/Chicago'),
    ('Los Angeles', 'America/Los_Angeles'), ('Sydney', 'Australia/Sydney'),
]

def _resolve_tz(name):
    if not _HAS_ZONEINFO:
        return None, '対応するタイムゾーンが見つかりません'
    key = name.lower().replace('_', ' ').replace('+', ' ')
    tz_name = _CITY_TZ.get(key)
    if not tz_name:
        tz_name = _CITY_TZ.get(key.replace(' ', ''))
    if not tz_name:
        candidates = ['America/' + name.replace(' ', '_'),
                      'Asia/' + name.replace(' ', '_'),
                      'Europe/' + name.replace(' ', '_'),
                      'Australia/' + name.replace(' ', '_'),
                      'Pacific/' + name.replace(' ', '_'),
                      'Africa/' + name.replace(' ', '_'),
                      name.replace(' ', '_'),
                      name.replace(' ', '/')]
        for c in candidates:
            try:
                tz = ZoneInfo(c)
                tz_name = c
                break
            except ZoneInfoNotFoundError:
                pass
    if not tz_name:
        return None, f'不明なタイムゾーン: {name}'
    try:
        return ZoneInfo(tz_name), None
    except ZoneInfoNotFoundError:
        return None, f'不明なタイムゾーン: {tz_name}'

def _fmt_city_time(label, tz_name, now_utc, nc):
    try:
        if _HAS_ZONEINFO:
            tz = ZoneInfo(tz_name)
            local = now_utc.astimezone(tz)
        else:
            local = now_utc
        offset = local.utcoffset()
        total = int(offset.total_seconds())
        sign = '+' if total >= 0 else '-'
        h, m = divmod(abs(total) // 60, 60)
        off_str = f'UTC{sign}{h:02d}:{m:02d}'
        time_str = local.strftime('%H:%M:%S')
        date_str = local.strftime('%Y-%m-%d %a')
        return (f'  {cc(BW, f"{label:<12}", nc)} {cc(BG, time_str, nc)}  '
                f'{cc(D, date_str, nc)}  {cc(DC, off_str, nc)}')
    except Exception:
        return f'  {label:<20} エラー'

def do_time(args, nc):
    now_utc = datetime.now(timezone.utc)

    if not args:
        lines = [sep(nc), cc(BC, '  世界時計', nc), '',
                 cc(DC, f'  UTC  {now_utc.strftime("%Y-%m-%d %H:%M:%S")}', nc), '']
        for label, tz_name in _DEFAULT_CITIES:
            lines.append(_fmt_city_time(label, tz_name, now_utc, nc))
        lines += ['', sep(nc),
                  hint('/time/Tokyo              — 都市の時刻', nc),
                  hint('/time/Tokyo/London       — 2都市を比較', nc),
                  hint('/time/America/Chicago    — IANAタイムゾーン名', nc)]
        return '\n'.join(lines) + '\n'

    city_names = ' '.join(args).split('/')
    results = []
    for city in city_names:
        city = city.strip()
        if not city: continue
        tz, err = _resolve_tz(city)
        if err:
            results.append((city, None, err))
        else:
            results.append((city, tz, None))

    if len(results) == 1:
        city, tz, err = results[0]
        if err:
            lines = [sep(nc), cc(BR, f'  {err}', nc), sep(nc)]
            return '\n'.join(lines) + '\n'
        local = now_utc.astimezone(tz)
        offset = local.utcoffset()
        total = int(offset.total_seconds())
        sign = '+' if total >= 0 else '-'
        h, m = divmod(abs(total) // 60, 60)
        off_str = f'UTC{sign}{h:02d}:{m:02d}'
        dow_jp = ['月', '火', '水', '木', '金', '土', '日'][local.weekday()]
        lines = [sep(nc),
                 cc(BC, f'  {city.title()}', nc) + cc(DC, f'  {tz.key}  {off_str}', nc),
                 '',
                 cc(BG, f'  {local.strftime("%H:%M:%S")}', nc),
                 cc(D,  f'  {local.strftime("%Y年%m月%d日")} ({dow_jp})', nc),
                 sep(nc),
                 hint(f'/time/{city.replace(" ", "+")}  — {city}の時刻', nc)]
        return '\n'.join(lines) + '\n'

    lines = [sep(nc), cc(BC, '  世界時刻比較', nc), '',
             cc(DC, f'  UTC  {now_utc.strftime("%Y-%m-%d %H:%M:%S")}', nc), '']
    for city, tz, err in results:
        if err:
            lines.append(cc(BR, f'  {err}', nc))
        else:
            lines.append(_fmt_city_time(city.title(), tz.key, now_utc, nc))
    lines.append(sep(nc))
    return '\n'.join(lines) + '\n'


# ── /package ──────────────────────────────────────────────────────────────────

def _fetch_npm(name):
    url = f'https://registry.npmjs.org/{name}'
    req = Request(url, headers={'User-Agent': 'clilap.org/1.0',
                                'Accept': 'application/json'})
    try:
        with urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except URLError:
        return None

def _fetch_pypi(name):
    url = f'https://pypi.org/pypi/{name}/json'
    req = Request(url, headers={'User-Agent': 'clilap.org/1.0'})
    try:
        with urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except URLError:
        return None

def do_package(registry, name, nc):
    if not registry or not name:
        lines = [sep(nc), cc(BC, '  パッケージ情報', nc), '',
                 cc(D, '  使い方: /package/{レジストリ}/{パッケージ名}', nc),
                 cc(BW, '  $ curl clilap.org/package/npm/express', nc),
                 cc(BW, '  $ curl clilap.org/package/npm/@types/node', nc),
                 cc(BW, '  $ curl clilap.org/package/pypi/requests', nc),
                 '',
                 cc(DC, '  レジストリ: npm  pypi', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    reg = registry.lower()

    if reg == 'npm':
        data = _fetch_npm(name)
        if not data:
            lines = [sep(nc), cc(BR, f'  npmパッケージ見つかりません: {name}', nc), sep(nc)]
            return '\n'.join(lines) + '\n'
        latest = data.get('dist-tags', {}).get('latest', '?')
        info = data.get('versions', {}).get(latest, {})
        desc = data.get('description', info.get('description', '—'))[:120]
        homepage = info.get('homepage', data.get('homepage', '—'))
        repo = ''
        repo_data = info.get('repository') or data.get('repository', {})
        if isinstance(repo_data, dict):
            repo = repo_data.get('url', '').replace('git+', '').replace('.git', '')
        elif isinstance(repo_data, str):
            repo = repo_data
        license_ = info.get('license', data.get('license', '—'))
        deps = len(info.get('dependencies', {}))
        peer_deps = len(info.get('peerDependencies', {}))
        time_data = data.get('time', {})
        created  = time_data.get('created', '?')[:10]
        modified = time_data.get('modified', '?')[:10]
        keywords = ', '.join(data.get('keywords', [])[:8])
        lines = [sep(nc),
                 cc(BC, f'  npm: {name}', nc), '',
                 cc(DC, '  バージョン    ', nc) + cc(BG, latest, nc),
                 cc(DC, '  説明          ', nc) + cc(BW, desc, nc),
                 cc(DC, '  ライセンス    ', nc) + cc(D, str(license_), nc),
                 cc(DC, '  依存関係      ', nc) + cc(D, f'{deps}件  (peer: {peer_deps}件)', nc),
                 cc(DC, '  作成日        ', nc) + cc(D, created, nc),
                 cc(DC, '  更新日        ', nc) + cc(D, modified, nc)]
        if homepage and homepage != '—':
            lines.append(cc(DC, '  ホームページ  ', nc) + cc(C, homepage[:80], nc))
        if repo:
            lines.append(cc(DC, '  リポジトリ    ', nc) + cc(C, repo[:80], nc))
        if keywords:
            lines.append(cc(DC, '  キーワード    ', nc) + cc(D, keywords, nc))
        lines += ['', sep(nc),
                  hint(f'npm install {name}', nc),
                  hint(f'/package/npm/{name}   — パッケージ詳細', nc)]
        return '\n'.join(lines) + '\n'

    elif reg == 'pypi':
        data = _fetch_pypi(name)
        if not data:
            lines = [sep(nc), cc(BR, f'  PyPIパッケージ見つかりません: {name}', nc), sep(nc)]
            return '\n'.join(lines) + '\n'
        info = data.get('info', {})
        version = info.get('version', '?')
        desc    = (info.get('summary') or '—')[:120]
        license_ = info.get('license', '—') or '—'
        homepage = info.get('home_page', '') or info.get('project_urls', {}).get('Homepage', '—')
        requires_python = info.get('requires_python', '—') or '—'
        classifiers = [c for c in info.get('classifiers', []) if 'OS' not in c][:5]
        keywords = info.get('keywords', '') or ''
        lines = [sep(nc),
                 cc(BC, f'  PyPI: {name}', nc), '',
                 cc(DC, '  バージョン       ', nc) + cc(BG, version, nc),
                 cc(DC, '  説明             ', nc) + cc(BW, desc, nc),
                 cc(DC, '  ライセンス       ', nc) + cc(D, str(license_)[:60], nc),
                 cc(DC, '  Python対応バージョン', nc) + cc(D, requires_python, nc)]
        if homepage and homepage != '—':
            lines.append(cc(DC, '  ホームページ     ', nc) + cc(C, homepage[:80], nc))
        if keywords:
            lines.append(cc(DC, '  キーワード       ', nc) + cc(D, keywords[:80], nc))
        if classifiers:
            lines.append(cc(DC, '  分類', nc))
            for cl in classifiers:
                lines.append(cc(D, f'    {cl}', nc))
        lines += ['', sep(nc),
                  hint(f'pip install {name}', nc),
                  hint(f'/package/pypi/{name}   — パッケージ詳細', nc)]
        return '\n'.join(lines) + '\n'

    else:
        lines = [sep(nc), cc(BR, f'  不明なレジストリ: {registry}', nc),
                 cc(D, '  対応: npm  pypi', nc), sep(nc)]
        return '\n'.join(lines) + '\n'


# ── /redirect ─────────────────────────────────────────────────────────────────

def do_redirect(url, nc):
    if not url:
        lines = [sep(nc), cc(BC, '  リダイレクトチェーン', nc), '',
                 cc(D, '  使い方: /redirect/{URL}', nc),
                 cc(BW, '  $ curl clilap.org/redirect/https://bit.ly/...', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    if not url.startswith('http'):
        url = 'https://' + url

    import http.client

    _PRIVATE_PREFIXES = ('127.', '10.', '0.', '169.254.', '192.168.',
                         '172.16.', '172.17.', '172.18.', '172.19.',
                         '172.20.', '172.21.', '172.22.', '172.23.',
                         '172.24.', '172.25.', '172.26.', '172.27.',
                         '172.28.', '172.29.', '172.30.', '172.31.',
                         '::1', 'fc', 'fd')

    def _is_private(host):
        try:
            ip = socket.gethostbyname(host)
            return any(ip.startswith(p) for p in _PRIVATE_PREFIXES)
        except Exception:
            return False

    chain = []
    current = url
    max_hops = 15

    for _ in range(max_hops):
        chain.append(current)
        try:
            parsed_c = urlparse(current)
            if _is_private(parsed_c.netloc.split(':')[0]):
                chain.append('エラー: プライベートIPへのアクセスは禁止されています')
                break
            if parsed_c.scheme == 'https':
                conn = http.client.HTTPSConnection(parsed_c.netloc, timeout=5,
                    context=ssl.create_default_context())
            else:
                conn = http.client.HTTPConnection(parsed_c.netloc, timeout=5)
            path = parsed_c.path or '/'
            if parsed_c.query: path += '?' + parsed_c.query
            conn.request('HEAD', path, headers={'User-Agent': 'clilap.org/1.0'})
            resp = conn.getresponse()
            status = resp.status
            location = resp.getheader('Location', '')
            conn.close()
            if status in (301, 302, 303, 307, 308) and location:
                if location.startswith('/'):
                    current = f"{parsed_c.scheme}://{parsed_c.netloc}{location}"
                elif not location.startswith('http'):
                    current = f"{parsed_c.scheme}://{parsed_c.netloc}/{location}"
                else:
                    current = location
            else:
                chain.append(f'✓ {status} {current}')
                chain = chain[:-1]
                break
        except Exception as e:
            chain.append(f'エラー: {e}')
            break

    lines = [sep(nc), cc(BC, '  リダイレクトチェーン', nc), '',
             cc(DC, f'  {len(chain)-1}リダイレクト', nc) if len(chain) > 1 else cc(BG, '  直接URL (リダイレクトなし)', nc),
             '']
    for i, u in enumerate(chain):
        if i == 0:
            lines.append(f'  {cc(Y, "開始  →", nc)} {cc(D, u[:100], nc)}')
        elif u.startswith('✓'):
            lines.append(f'  {cc(BG, "終端  →", nc)} {cc(BW, u[2:].strip()[:100], nc)}')
        elif u.startswith('エラー'):
            lines.append(f'  {cc(BR, u[:100], nc)}')
        else:
            lines.append(f'  {cc(DC, str(i).rjust(4) + "  →", nc)} {cc(D, u[:100], nc)}')
    lines += ['', sep(nc), hint(f'/redirect/{url[:60]}', nc)]
    return '\n'.join(lines) + '\n'


# ── /ssl ──────────────────────────────────────────────────────────────────────

def do_ssl(domain, nc):
    if not domain:
        lines = [sep(nc), cc(BC, '  SSL証明書', nc), '',
                 cc(D, '  使い方: /ssl/{ドメイン}', nc),
                 cc(BW, '  $ curl clilap.org/ssl/github.com', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.create_connection((domain, 443), timeout=8),
                             server_hostname=domain) as s:
            cert = s.getpeercert()

        subject = dict(x[0] for x in cert.get('subject', []))
        issuer  = dict(x[0] for x in cert.get('issuer', []))

        def _parse_date(s):
            try:
                return datetime.strptime(s, '%b %d %H:%M:%S %Y %Z').replace(tzinfo=timezone.utc)
            except ValueError:
                return None

        not_before = _parse_date(cert.get('notBefore', ''))
        not_after  = _parse_date(cert.get('notAfter', ''))
        now = datetime.now(timezone.utc)

        remaining = None
        status_str = cc(BG, '有効', nc)
        if not_after:
            remaining = not_after - now
            if remaining.total_seconds() < 0:
                status_str = cc(BR, '期限切れ', nc)
            elif remaining.days < 30:
                status_str = cc(BY, f'まもなく期限切れ ({remaining.days}日)', nc)
            else:
                status_str = cc(BG, f'有効 (残り{remaining.days}日)', nc)

        sans = []
        for ext_type, data in cert.get('subjectAltName', []):
            if ext_type == 'DNS': sans.append(data)

        lines = [sep(nc),
                 cc(BC, f'  SSL  {domain}', nc) + '  ' + status_str,
                 '',
                 cc(DC, '  発行先   ', nc) + cc(BW, subject.get('commonName', '—'), nc),
                 cc(DC, '  発行者   ', nc) + cc(D, issuer.get('organizationName', '—'), nc),
                 cc(DC, '  開始日   ', nc) + cc(D, not_before.strftime('%Y-%m-%d') if not_before else '—', nc),
                 cc(DC, '  有効期限 ', nc) + cc(D, not_after.strftime('%Y-%m-%d') if not_after else '—', nc),
                 cc(DC, '  SANs     ', nc) + cc(D, str(len(sans)) + '件', nc),
                 '']
        for san in sans[:20]:
            lines.append(cc(D, f'    {san}', nc))
        if len(sans) > 20:
            lines.append(cc(D, f'    ... さらに{len(sans)-20}件', nc))
        lines += [sep(nc), hint(f'/ssl/{domain}', nc)]
        return '\n'.join(lines) + '\n'
    except ssl.SSLError as e:
        lines = [sep(nc), cc(BR, f'  SSLエラー: {e}', nc), sep(nc)]
        return '\n'.join(lines) + '\n'
    except Exception as e:
        lines = [sep(nc), cc(BR, f'  接続エラー: {e}', nc), sep(nc)]
        return '\n'.join(lines) + '\n'


# ── /sec ──────────────────────────────────────────────────────────────────────

_SEC_HEADERS = [
    ('Strict-Transport-Security', 'HSTS',
     'HTTPSを強制する。不可: サイト全体がHTTPSで動作していない可能性'),
    ('Content-Security-Policy', 'CSP',
     'XSS等を防ぐ。不可: インラインスクリプトやサードパーティリソースを制限できていない'),
    ('X-Frame-Options', 'クリックジャッキング防止',
     'クリックジャッキングを防ぐ。不可: iframeで埋め込まれるリスク'),
    ('X-Content-Type-Options', 'MIME Sniffing防止',
     'Content-Typeの推測を防ぐ。不可: ブラウザがスクリプトとして実行する可能性'),
    ('Referrer-Policy', 'リファラーポリシー',
     'リファラー情報の漏洩を制限。不可: URLにプライバシー情報が含まれる場合に漏洩リスク'),
    ('Permissions-Policy', 'Permissions-Policy',
     'ブラウザ機能のアクセスを制限。カメラ・位置情報など'),
    ('X-XSS-Protection', 'XSS-Protection',
     '旧ブラウザ向けXSS対策 (現代ブラウザでは非推奨)'),
    ('Cross-Origin-Opener-Policy', 'COOP',
     'クロスオリジンの分離設定。Spectreなどの攻撃を緩和'),
    ('Cross-Origin-Embedder-Policy', 'COEP',
     'クロスオリジン埋め込みの制限'),
    ('Cross-Origin-Resource-Policy', 'CORP',
     'リソースのクロスオリジン読み込みを制限'),
]

def do_sec(domain, nc):
    if not domain:
        lines = [sep(nc), cc(BC, '  セキュリティヘッダー診断', nc), '',
                 cc(D, '  使い方: /sec/{ドメイン}', nc),
                 cc(BW, '  $ curl clilap.org/sec/github.com', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    try:
        url = f'https://{domain}' if not domain.startswith('http') else domain
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible; clilap.org/1.0)'})
        with urlopen(req, timeout=10) as r:
            headers = {k.lower(): v for k, v in r.headers.items()}
        status = r.status if hasattr(r, 'status') else 200
    except Exception as e:
        lines = [sep(nc), cc(BR, f'  接続エラー: {e}', nc), sep(nc)]
        return '\n'.join(lines) + '\n'

    score = 0
    max_score = 6
    critical = ['strict-transport-security', 'content-security-policy',
                'x-frame-options', 'x-content-type-options']
    for h in critical:
        if h in headers: score += 1
    if 'referrer-policy' in headers: score += 1
    if 'permissions-policy' in headers: score += 1

    pct = score / max_score
    if   pct >= 0.9: grade = cc(BG, 'A+', nc)
    elif pct >= 0.8: grade = cc(BG, 'A',  nc)
    elif pct >= 0.7: grade = cc(BG, 'B',  nc)
    elif pct >= 0.5: grade = cc(BY, 'C',  nc)
    elif pct >= 0.3: grade = cc(BR, 'D',  nc)
    else:            grade = cc(BR, 'F',  nc)

    lines = [sep(nc),
             cc(BC, f'  セキュリティヘッダー  {domain}', nc), '',
             cc(DC, '  グレード  ', nc) + grade +
             cc(DC, f'  スコア {score}/{max_score}', nc),
             '']

    for raw_header, label, tip in _SEC_HEADERS:
        h_lower = raw_header.lower()
        if h_lower in headers:
            val = headers[h_lower][:80]
            lines.append(f'  {cc(BG, "✓", nc)} {cc(BW, label, nc)}')
            lines.append(f'      {cc(D, val, nc)}')
        else:
            lines.append(f'  {cc(BR, "✗", nc)} {cc(D, label, nc)}')
            lines.append(f'      {cc(DC, tip, nc)}')

    lines += ['', sep(nc), hint(f'/sec/{domain}', nc)]
    return '\n'.join(lines) + '\n'


# ── /dnsmap ───────────────────────────────────────────────────────────────────

_RESOLVERS = [
    ('Cloudflare', '1.1.1.1'),
    ('Google',     '8.8.8.8'),
    ('Quad9',      '9.9.9.9'),
    ('OpenDNS',    '208.67.222.222'),
]

def _dns_query(domain, qtype, resolver_ip, timeout=3):
    try:
        import struct, socket, random as _random
        def encode_name(name):
            parts = name.split('.')
            buf = b''
            for p in parts:
                enc = p.encode()
                buf += bytes([len(enc)]) + enc
            return buf + b'\x00'

        qtypes = {'A':1, 'AAAA':28, 'MX':15, 'NS':2, 'TXT':16, 'CNAME':5}
        qtype_id = qtypes.get(qtype.upper(), 1)

        txid = _random.randint(0, 65535)
        flags = 0x0100
        header = struct.pack('!HHHHHH', txid, flags, 1, 0, 0, 0)
        question = encode_name(domain) + struct.pack('!HH', qtype_id, 1)
        packet = header + question

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(timeout)
            s.sendto(packet, (resolver_ip, 53))
            data, _ = s.recvfrom(512)

        an_count = struct.unpack('!H', data[6:8])[0]
        if an_count == 0:
            return []

        results = []
        pos = 12 + len(question)

        def skip_name(pos):
            while pos < len(data):
                length = data[pos]
                if length == 0: return pos + 1
                if (length & 0xC0) == 0xC0: return pos + 2
                pos += length + 1
            return pos

        for _ in range(an_count):
            if pos >= len(data): break
            pos = skip_name(pos)
            if pos + 10 > len(data): break
            rtype, rclass, ttl, rdlen = struct.unpack('!HHIH', data[pos:pos+10])
            pos += 10
            rdata = data[pos:pos+rdlen]
            pos += rdlen

            if rtype == 1 and len(rdata) == 4:
                results.append('.'.join(str(b) for b in rdata))
            elif rtype == 28 and len(rdata) == 16:
                parts = [f'{rdata[i]<<8|rdata[i+1]:04x}' for i in range(0, 16, 2)]
                results.append(':'.join(parts))
            elif rtype in (2, 5):
                name_parts = []
                p = pos - rdlen
                while p < pos:
                    l = data[p]
                    if l == 0: break
                    if (l & 0xC0) == 0xC0:
                        ptr = ((l & 0x3F) << 8) | data[p+1]
                        tmp_p = ptr
                        while tmp_p < len(data):
                            ll = data[tmp_p]
                            if ll == 0: break
                            if (ll & 0xC0) == 0xC0:
                                tmp_p = ((ll & 0x3F) << 8) | data[tmp_p+1]
                            else:
                                name_parts.append(data[tmp_p+1:tmp_p+1+ll].decode('ascii', 'replace'))
                                tmp_p += ll + 1
                        break
                    else:
                        name_parts.append(data[p+1:p+1+l].decode('ascii', 'replace'))
                        p += l + 1
                results.append('.'.join(name_parts))
            elif rtype == 16:
                txt = ''
                p = pos - rdlen
                while p < pos:
                    l = data[p]; p += 1
                    txt += data[p:p+l].decode('utf-8', 'replace'); p += l
                results.append(f'"{txt}"')
        return results
    except Exception:
        return None

def do_dnsmap(domain, nc):
    if not domain:
        lines = [sep(nc), cc(BC, '  DNSマップ', nc), '',
                 cc(D, '  4つのリゾルバーで同時にDNSを照会します', nc),
                 cc(BW, '  $ curl clilap.org/dnsmap/github.com', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    lines = [sep(nc), cc(BC, f'  DNSマップ  {domain}', nc), '',
             cc(DC, f'  {"リゾルバー":<16} {"IP":<16} Aレコード', nc), '']

    all_results = []
    for name, ip in _RESOLVERS:
        results = _dns_query(domain, 'A', ip)
        all_results.append((name, ip, results))
        if results is None:
            val = cc(BR, 'タイムアウト', nc)
        elif not results:
            val = cc(D, '結果なし', nc)
        else:
            val = cc(BG, '  '.join(results[:3]), nc)
        # pad plain text before colorizing so ANSI codes don't break alignment
        lines.append(f'  {cc(BW, f"{name:<12}", nc)} {cc(DC, f"{ip:<18}", nc)} {val}')

    valid = [set(r) for _, _, r in all_results if r is not None and r]
    if valid:
        if all(v == valid[0] for v in valid):
            lines += ['', cc(BG, '  全リゾルバーで一致', nc)]
        else:
            lines += ['', cc(BY, '  リゾルバーによって異なる応答 (GeoDNSまたは伝播中の可能性)', nc)]

    lines += ['', sep(nc), hint(f'/dnsmap/{domain}', nc)]
    return '\n'.join(lines) + '\n'


# ── /portcheck ────────────────────────────────────────────────────────────────

_COMMON_PORTS = {
    21: 'FTP', 22: 'SSH', 23: 'Telnet', 25: 'SMTP', 53: 'DNS',
    80: 'HTTP', 110: 'POP3', 143: 'IMAP', 443: 'HTTPS', 465: 'SMTPS',
    587: 'SMTP', 993: 'IMAPS', 995: 'POP3S', 3306: 'MySQL',
    5432: 'PostgreSQL', 6379: 'Redis', 8080: 'HTTP-alt', 8443: 'HTTPS-alt',
    27017: 'MongoDB', 9200: 'Elasticsearch',
}

def do_portcheck(host, port_str, nc):
    if not host or not port_str:
        lines = [sep(nc), cc(BC, '  ポートチェック', nc), '',
                 cc(D, '  使い方: /portcheck/{ホスト}/{ポート}', nc),
                 cc(BW, '  $ curl clilap.org/portcheck/github.com/443', nc),
                 cc(BW, '  $ curl clilap.org/portcheck/example.com/22', nc),
                 '',
                 cc(DC, '  よく使うポート: 22 (SSH) 80 (HTTP) 443 (HTTPS) 3306 (MySQL)', nc),
                 sep(nc)]
        return '\n'.join(lines) + '\n'

    try:
        port = int(port_str)
    except ValueError:
        lines = [sep(nc), cc(BR, f'  ポート番号が不正: {port_str}', nc), sep(nc)]
        return '\n'.join(lines) + '\n'

    service = _COMMON_PORTS.get(port, '不明')

    # SSRF protection: block private/loopback ranges
    try:
        resolved_ip = socket.gethostbyname(host)
        _private_blocks = [
            ('127.', 8), ('10.', 8), ('0.', 8),
            ('169.254.', 16), ('192.168.', 16),
            ('172.16.', 12), ('172.17.', 12), ('172.18.', 12), ('172.19.', 12),
            ('172.20.', 12), ('172.21.', 12), ('172.22.', 12), ('172.23.', 12),
            ('172.24.', 12), ('172.25.', 12), ('172.26.', 12), ('172.27.', 12),
            ('172.28.', 12), ('172.29.', 12), ('172.30.', 12), ('172.31.', 12),
            ('::1', 0), ('fc', 0), ('fd', 0),
        ]
        for prefix, _ in _private_blocks:
            if resolved_ip.startswith(prefix):
                lines = [sep(nc), cc(BR, '  プライベートIPへのアクセスは禁止されています', nc), sep(nc)]
                return '\n'.join(lines) + '\n'
    except Exception:
        pass

    start = time.time()
    try:
        with socket.create_connection((host, port), timeout=2):
            elapsed = (time.time() - start) * 1000
            status_str = cc(BG, '開放', nc)
            latency = cc(D, f'{elapsed:.1f}ms', nc)
    except (socket.timeout, ConnectionRefusedError, OSError):
        elapsed = (time.time() - start) * 1000
        status_str = cc(BR, '閉鎖', nc)
        latency = cc(D, f'{elapsed:.1f}ms', nc)

    lines = [sep(nc),
             cc(BC, f'  ポートチェック: {host}:{port}', nc), '',
             cc(DC, '  ステータス  ', nc) + status_str,
             cc(DC, '  ポート      ', nc) + cc(BW, str(port), nc),
             cc(DC, '  サービス    ', nc) + cc(D, service, nc),
             cc(DC, '  レイテンシ  ', nc) + latency,
             sep(nc),
             hint(f'/portcheck/{host}/{port}', nc)]
    return '\n'.join(lines) + '\n'


# ── /dns/domain/all ───────────────────────────────────────────────────────────

def do_dns_all(domain, nc):
    import subprocess

    QTYPES = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'CNAME', 'SOA', 'CAA', 'SRV']

    def dig_query(domain, qtype):
        try:
            result = subprocess.run(
                ['dig', '+noall', '+answer', '+nocmd', qtype, domain],
                capture_output=True, text=True, timeout=5)
            return result.stdout.strip()
        except Exception:
            return ''

    lines = [sep(nc), cc(BC, f'  DNSエクスポート: {domain}', nc), '']
    found_any = False

    for qtype in QTYPES:
        output = dig_query(domain, qtype)
        if not output:
            continue
        found_any = True
        lines.append(cc(BC, f'  [{qtype}]', nc))
        for line in output.splitlines():
            parts = line.split()
            if len(parts) >= 5:
                name, ttl, cls, rtype, *rdata = parts
                lines.append(
                    f'  {cc(D, name, nc):<35} '
                    f'{cc(DC, ttl.rjust(6), nc)}  '
                    f'{cc(BW, rtype, nc):<6}  '
                    f'{cc(BG, " ".join(rdata)[:80], nc)}')
            else:
                lines.append(cc(D, "  " + line, nc))
        lines.append('')

    if not found_any:
        lines.append(cc(D, '  レコードなし', nc))

    lines += [sep(nc),
              hint(f'/dns/{domain}/all     — 全レコードエクスポート', nc),
              hint(f'/dns/{domain}/MX      — MXレコードのみ', nc)]
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

    def _dispatch(self):
        parsed = urlparse(self.path)
        qs     = parse_qs(parsed.query, keep_blank_values=True)
        ua     = self.headers.get('User-Agent', '')
        browser = is_browser(ua)
        nc     = 'nocolor' in qs or 'nc' in qs

        parts   = [p for p in parsed.path.split('/') if p]
        service = parts[0] if parts else ''
        args    = [unquote(p) for p in parts[1:]]

        def respond(text):
            if browser:
                self._send(html_wrap(text, f'{service} — Clilap'), html=True)
            else:
                self._send(text)

        if service == 'rate':
            from_curr   = args[0].upper() if args else ''
            targets_str = args[1] if len(args) > 1 else ''
            respond(do_rate(from_curr, targets_str, nc))
        elif service == 'time':
            respond(do_time(args, nc))
        elif service == 'package':
            registry = args[0] if args else ''
            name     = '/'.join(args[1:]) if len(args) > 1 else ''
            respond(do_package(registry, name, nc))
        elif service == 'redirect':
            # preserve double-slash in https:// — don't use parts[] which strips empty segments
            raw = parsed.path[len('/redirect/'):]
            url = unquote(raw)
            respond(do_redirect(url, nc))
        elif service == 'ssl':
            respond(do_ssl(args[0] if args else '', nc))
        elif service == 'sec':
            respond(do_sec(args[0] if args else '', nc))
        elif service == 'dnsmap':
            respond(do_dnsmap(args[0] if args else '', nc))
        elif service == 'portcheck':
            host     = args[0] if args else ''
            port_str = args[1] if len(args) > 1 else ''
            respond(do_portcheck(host, port_str, nc))
        elif service == 'dns' and len(args) >= 2 and args[-1] == 'all':
            domain = args[0] if args else ''
            respond(do_dns_all(domain, nc))
        else:
            self._send('Not found\n', status=404)

    def do_GET(self):
        try: self._dispatch()
        except Exception: self._send('Internal error\n', status=500)

    def do_POST(self):
        try: self._dispatch()
        except Exception: self._send('Internal error\n', status=500)


if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    print(f'net server listening on 127.0.0.1:{PORT}')
    server.serve_forever()
