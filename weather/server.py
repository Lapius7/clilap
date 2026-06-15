#!/usr/bin/env python3
"""Terminal weather service using Open-Meteo + Nominatim. No API keys needed."""

import json
import re
import unicodedata
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
from datetime import datetime

PORT = 3210
UA   = 'clilap.org/weather'

# ---------- ANSI ----------
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
BR  = '\x1b[1;31m'

BROWSER_KEYS = ('mozilla', 'webkit', 'trident', 'opera')

def is_browser(ua_str):
    u = ua_str.lower()
    return any(k in u for k in BROWSER_KEYS)

# ---------- WMO codes ----------
WMO_CODES = {
    0:  ('☀',  '快晴',           'Clear sky'),
    1:  ('🌤', 'ほぼ晴れ',       'Mainly clear'),
    2:  ('⛅', '一部曇り',       'Partly cloudy'),
    3:  ('☁',  '曇り',           'Overcast'),
    45: ('🌫', '霧',             'Fog'),
    48: ('🌫', '氷霧',           'Icy fog'),
    51: ('🌦', '小雨',           'Light drizzle'),
    53: ('🌦', '霧雨',           'Drizzle'),
    55: ('🌧', '強い霧雨',       'Heavy drizzle'),
    61: ('🌧', '弱い雨',         'Slight rain'),
    63: ('🌧', '雨',             'Moderate rain'),
    65: ('🌧', '大雨',           'Heavy rain'),
    71: ('🌨', '弱い雪',         'Slight snow'),
    73: ('🌨', '雪',             'Moderate snow'),
    75: ('❄',  '大雪',           'Heavy snow'),
    77: ('🌨', '細雪',           'Snow grains'),
    80: ('🌦', 'にわか雨',       'Slight showers'),
    81: ('🌧', '強にわか雨',     'Moderate showers'),
    82: ('⛈',  '激しいにわか雨', 'Violent showers'),
    85: ('🌨', 'にわか雪',       'Slight snow showers'),
    86: ('🌨', '強いにわか雪',   'Heavy snow showers'),
    95: ('⛈',  '雷雨',           'Thunderstorm'),
    96: ('⛈',  '雷雨(雹)',       'Thunderstorm w/ hail'),
    99: ('⛈',  '激しい雷雨',     'Thunderstorm w/ heavy hail'),
}

# ---------- ASCII art (each line: 13 display cols) ----------
ASCII_ART = {
    'sun': [
        '    \\   /    ',
        '     .-.     ',
        '  -- (   ) --',
        '     \`-\'     ',
        '    /   \\    ',
    ],
    'clear': [
        '  \\       /  ',
        '   .-(   )-, ',
        '  (   ) -(   )',
        '   \`- (  ) -\'',
        '        \'    ',
    ],
    'cloudy': [
        '             ',
        '     .--.    ',
        '  .-(    ).  ',
        ' (___.__)__) ',
        '             ',
    ],
    'rain': [
        '     .--.    ',
        '  .-(    ).  ',
        ' (___.__)__) ',
        "  ' ' ' ' '  ",
        "  ' ' ' ' '  ",
    ],
    'snow': [
        '     .--.    ',
        '  .-(    ).  ',
        ' (___.__)__) ',
        '   *  *  *   ',
        '  *  *  *    ',
    ],
    'fog': [
        '             ',
        ' _ - _ - _ - ',
        '  _ - _ - _  ',
        ' _ - _ - _ - ',
        '             ',
    ],
    'thunder': [
        '     .--.    ',
        '  .-(    ).  ',
        ' (___.__)__) ',
        '      /      ',
        '     /       ',
    ],
}

def wmo_art(code):
    if code == 0:                          return 'sun'
    if code in (1, 2):                     return 'clear'
    if code == 3:                          return 'cloudy'
    if code in (45, 48):                   return 'fog'
    if code in (51,53,55,61,63,65,80,81,82): return 'rain'
    if code in (71,73,75,77,85,86):        return 'snow'
    if code in (95,96,99):                 return 'thunder'
    return 'cloudy'

WIND_ARROWS = ['↑','↗','→','↘','↓','↙','←','↖']

def wind_arrow(deg):
    if deg is None: return '?'
    return WIND_ARROWS[round(float(deg) / 45) % 8]

# ---------- Display width helpers ----------
def disp_width(s):
    plain = re.sub(r'\x1b\[[^m]*m', '', s)
    plain = re.sub(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)', '', plain)
    w = 0
    for ch in plain:
        cp  = ord(ch)
        eaw = unicodedata.east_asian_width(ch)
        if eaw in ('W', 'F'):
            w += 2
        elif 0x2600 <= cp <= 0x27FF:    # Misc symbols / Dingbats
            w += 2
        elif 0x1F000 <= cp <= 0x1FFFF:  # Emoji
            w += 2
        else:
            w += 1
    return w

def pad_to(s, width):
    return s + ' ' * max(0, width - disp_width(s))

def center_in(s, width):
    dw = disp_width(s)
    total = max(0, width - dw)
    left  = total // 2
    return ' ' * left + s + ' ' * (total - left)

def temp_color(t, no_color):
    t = round(float(t))
    if no_color: return str(t)
    if t >= 35:  return f'{BR}{t}{R}'
    if t >= 25:  return f'{BY}{t}{R}'
    if t >= 15:  return f'{BG}{t}{R}'
    if t >= 5:   return f'{BC}{t}{R}'
    return f'{C}{t}{R}'

# ---------- Data fetching ----------
def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=8) as r:
        return json.loads(r.read())

def geocode(location):
    q    = urllib.parse.quote(location)
    url  = f'https://nominatim.openstreetmap.org/search?q={q}&format=json&limit=1'
    data = fetch_json(url)
    if not data:
        return None, None, None
    return (float(data[0]['lat']),
            float(data[0]['lon']),
            data[0].get('display_name', location).split(',')[0].strip())

def geocode_ip(ip):
    """Geo-locate an IP via ip-api.com → (lat, lon, city) or (None, None, None)."""
    if not ip:
        return None, None, None
    try:
        import ipaddress
        _ip = ipaddress.ip_address(ip)
        if _ip.is_private or _ip.is_loopback or _ip.is_link_local:
            return None, None, None
    except ValueError:
        return None, None, None
    try:
        url = f'http://ip-api.com/json/{ip}?fields=status,city,regionName,country,lat,lon'
        req = urllib.request.Request(url, headers={'User-Agent': UA})
        with urllib.request.urlopen(req, timeout=4) as r:
            g = json.loads(r.read())
        if g.get('status') == 'success' and g.get('lat'):
            city = g.get('city') or g.get('regionName') or g.get('country', ip)
            return float(g['lat']), float(g['lon']), city
    except Exception:
        pass
    return None, None, None

def get_weather(lat, lon):
    url = (
        'https://api.open-meteo.com/v1/forecast'
        f'?latitude={lat}&longitude={lon}'
        '&current=temperature_2m,apparent_temperature,weathercode,'
        'windspeed_10m,winddirection_10m,relativehumidity_2m,precipitation,uv_index'
        '&hourly=temperature_2m,apparent_temperature,weathercode,'
        'windspeed_10m,winddirection_10m,precipitation_probability,visibility'
        '&daily=weathercode,temperature_2m_max,temperature_2m_min,'
        'precipitation_sum,precipitation_probability_max,windspeed_10m_max,'
        'uv_index_max,sunrise,sunset'
        '&timezone=auto&forecast_days=4'
    )
    return fetch_json(url)

# ---------- Labels ----------
JA_DAYS = ['月','火','水','木','金','土','日']

LABELS = {
    'ja': {
        'feels':    '体感',
        'slots':    ['朝', '昼', '夕', '夜'],
        'slot_hrs': [6, 12, 18, 21],
        'hint':     '  ?nocolor  ?lang=en',
        'error':    'エラー',
        'usage':    '使い方: curl clilap.org/weather/Tokyo',
    },
    'en': {
        'feels':    'feels',
        'slots':    ['Morn', 'Noon', 'Eve', 'Night'],
        'slot_hrs': [6, 12, 18, 21],
        'hint':     '  ?nocolor  ?lang=ja',
        'error':    'Error:',
        'usage':    'Usage: curl clilap.org/weather/Tokyo',
    },
}

# ---------- Layout constants ----------
SEP_W  = 80
CELL_W = 17  # display cols per time-slot column

# ---------- Hourly slot extraction ----------
def get_slot(hourly, date_str, hour):
    target = f'{date_str}T{hour:02d}:00'
    times  = hourly['time']
    try:
        i = times.index(target)
    except ValueError:
        return None
    vis_arr = hourly.get('visibility', [])
    return {
        'temp':  hourly['temperature_2m'][i],
        'feels': hourly['apparent_temperature'][i],
        'code':  hourly['weathercode'][i],
        'wind':  hourly['windspeed_10m'][i],
        'wdir':  hourly['winddirection_10m'][i],
        'prob':  hourly['precipitation_probability'][i],
        'vis':   vis_arr[i] if i < len(vis_arr) else None,
    }

def render_col(slot, no_color, lang):
    """One time-slot column: list of lines padded to CELL_W display cols."""
    def c(code, text): return text if no_color else code + text + R
    if slot is None:
        return [' ' * CELL_W] * 9

    code  = slot['code']
    wmo   = WMO_CODES.get(code, ('?', '不明', 'Unknown'))
    icon  = wmo[0]
    desc  = wmo[1] if lang == 'ja' else wmo[2]
    art   = ASCII_ART[wmo_art(code)]
    temp  = slot['temp']
    feels = slot['feels']
    wind  = slot['wind']
    wdir  = slot['wdir']
    prob  = slot['prob'] if slot['prob'] is not None else 0
    vis   = slot['vis']

    lines = []
    for a in art:
        lines.append(pad_to(c(BY, a) if not no_color else a, CELL_W))

    lines.append(pad_to(c(BY, f'{icon} {desc}'), CELL_W))
    tc = temp_color(temp, no_color)
    fc = temp_color(feels, no_color)
    lines.append(pad_to(f'{tc}({fc})°', CELL_W))
    arrow = wind_arrow(wdir)
    lines.append(pad_to(c(C, f'{arrow} {round(wind)}km/h'), CELL_W))
    prob_s = c(BC, f'{round(prob)}%')
    if vis is not None:
        vis_km = round(vis / 1000)
        lines.append(pad_to(c(D, f'{vis_km}km ') + prob_s, CELL_W))
    else:
        lines.append(pad_to(prob_s, CELL_W))

    return lines

# ---------- Main render ----------
def render(location_name, lat, lon, data, no_color, lang='ja'):
    def c(code, text): return text if no_color else code + text + R
    L      = LABELS.get(lang, LABELS['ja'])
    cur    = data['current']
    daily  = data['daily']
    hourly = data['hourly']
    SEP    = c(DC, '═' * SEP_W)
    div    = c(DC, '  ' + '─' * (SEP_W - 2))
    vbar   = c(DC, '│')

    code   = cur['weathercode']
    wmo    = WMO_CODES.get(code, ('?', '不明', 'Unknown'))
    icon   = wmo[0]
    desc   = wmo[1] if lang == 'ja' else wmo[2]
    art    = ASCII_ART[wmo_art(code)]
    temp   = cur['temperature_2m']
    feels  = cur['apparent_temperature']
    humid  = cur['relativehumidity_2m']
    wind   = cur['windspeed_10m']
    wdir   = cur.get('winddirection_10m')
    precip = cur['precipitation']
    uv     = cur.get('uv_index')
    arrow  = wind_arrow(wdir)

    lines = [SEP]
    now   = datetime.now().strftime('%H:%M')
    lines.append(f'  {c(BW, location_name)}  {c(DC, now)}')
    lines.append(div)

    uv_s = f'  {c(BC,"UV:")} {c(BW, str(round(uv, 1)))}' if uv is not None else ''
    if lang == 'ja':
        info = [
            f'{c(BY, desc)}  {icon}',
            f'{c(BC,"気温:")}   {temp_color(temp,no_color)}°C  {c(D,L["feels"])} {temp_color(feels,no_color)}°C',
            f'{c(BC,"湿度:")}   {c(BW, str(round(humid)))}%',
            f'{c(BC,"風速:")}   {c(BW, f"{arrow} {round(wind)}")} km/h',
            f'{c(BC,"降水量:")} {c(BW, str(round(precip,1)))} mm{uv_s}',
        ]
    else:
        info = [
            f'{c(BY, desc)}  {icon}',
            f'{c(BC,"Temp:")}   {temp_color(temp,no_color)}°C  {c(D,L["feels"])} {temp_color(feels,no_color)}°C',
            f'{c(BC,"Humid:")}  {c(BW, str(round(humid)))}%',
            f'{c(BC,"Wind:")}   {c(BW, f"{arrow} {round(wind)}")} km/h',
            f'{c(BC,"Precip:")} {c(BW, str(round(precip,1)))} mm{uv_s}',
        ]

    for i, a in enumerate(art):
        right = info[i] if i < len(info) else ''
        lines.append(f'  {c(BY, a) if not no_color else a}  {right}')

    # 3-day time-slot blocks
    for day_i in range(min(3, len(daily['time']))):
        date_str = daily['time'][day_i]
        lines.append('')
        lines.append(div)

        # Day header line
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            day_label = (f'{JA_DAYS[dt.weekday()]}曜 {dt.month}月{dt.day}日'
                         if lang == 'ja' else dt.strftime('%A, %b %d'))
        except Exception:
            day_label = date_str

        d_code = daily['weathercode'][day_i]
        d_wmo  = WMO_CODES.get(d_code, ('?', '不明', 'Unknown'))
        d_max  = daily['temperature_2m_max'][day_i]
        d_min  = daily['temperature_2m_min'][day_i]
        d_rain = daily['precipitation_sum'][day_i]
        d_prob = (daily.get('precipitation_probability_max') or [None]*10)[day_i]
        d_uv   = (daily.get('uv_index_max') or [None]*10)[day_i]
        sunrise_raw = (daily.get('sunrise') or [None]*10)[day_i]
        sunset_raw  = (daily.get('sunset')  or [None]*10)[day_i]
        sunrise_s   = sunrise_raw[11:16] if sunrise_raw else '?'
        sunset_s    = sunset_raw[11:16]  if sunset_raw  else '?'

        d_icon = d_wmo[0]
        d_desc = d_wmo[1] if lang == 'ja' else d_wmo[2]
        prob_s = f' {c(BC, str(round(d_prob))+"%")}' if d_prob is not None else ''
        uv_d_s = f'  {c(DC,"UV")}{c(BW,str(round(d_uv,1)))}' if d_uv is not None else ''
        sun_s  = f'  {c(DC,"↑"+sunrise_s+" ↓"+sunset_s)}'

        lines.append(
            f'  {c(BW, day_label)}  '
            f'{c(Y, d_icon)} {c(Y, d_desc)}  '
            f'{temp_color(d_max,no_color)}°/{temp_color(d_min,no_color)}°C'
            f'{prob_s}{uv_d_s}{sun_s}'
        )

        # Slot header row
        slot_labels = L['slots']
        hdr_cells = [pad_to(center_in(c(BW, lbl), CELL_W), CELL_W) for lbl in slot_labels]
        lines.append('  ' + vbar.join(hdr_cells))

        # Divider
        lines.append('  ' + c(DC, '┼'.join(['─' * CELL_W] * 4)))

        # Slot data columns
        slot_hrs = L['slot_hrs']
        slots    = [get_slot(hourly, date_str, hr) for hr in slot_hrs]
        cols     = [render_col(s, no_color, lang) for s in slots]

        n_rows = max(len(col) for col in cols)
        for row_i in range(n_rows):
            cells = [col[row_i] if row_i < len(col) else ' ' * CELL_W for col in cols]
            lines.append('  ' + vbar.join(cells))

    lines += ['', SEP, c(DC, L['hint'])]
    return '\n'.join(lines) + '\n'

# ---------- Index / error ----------
def render_help(no_color, lang='ja'):
    def c(code, text): return text if no_color else code + text + R
    W   = SEP_W
    SEP = c(DC, '═' * W)
    div = c(DC, '  ' + '─' * (W - 2))

    def ex(path, desc): return f'  {pad_to(c(BC, path), 42)} {c(D, desc)}'
    def op(flag, desc): return f'  {pad_to(c(C, flag), 14)} {c(D, desc)}'

    if lang == 'ja':
        return '\n'.join([
            SEP,
            f'  {c(BW, "clilap.org/weather")}  {c(Y, "⛅")} {c(D, "天気予報")}',
            div, '',
            ex('curl clilap.org/weather/Tokyo',      '東京の天気'),
            ex('curl clilap.org/weather/Osaka',      '大阪の天気'),
            ex('curl clilap.org/weather/東京都/新宿区', '市区町村も指定可'),
            '', div,
            f'  {c(BW, "オプション:")}',
            op('?lang=en',  '英語表示'),
            op('?nocolor',  'カラー無効'),
            '',
            SEP,
            c(DC, '  ?nocolor  ?lang=en'),
        ]) + '\n'
    else:
        return '\n'.join([
            SEP,
            f'  {c(BW, "clilap.org/weather")}  {c(Y, "⛅")} {c(D, "Weather forecast")}',
            div, '',
            ex('curl clilap.org/weather/Tokyo',      'Tokyo weather'),
            ex('curl clilap.org/weather/Osaka',      'Osaka weather'),
            ex('curl clilap.org/weather/Osaka/Ibaraki', 'City/district lookup'),
            '', div,
            f'  {c(BW, "Options:")}',
            op('?lang=ja',  'Japanese output'),
            op('?nocolor',  'Disable colors'),
            '',
            SEP,
            c(DC, '  ?nocolor  ?lang=ja'),
        ]) + '\n'

def render_error(msg, no_color, lang='ja'):
    def c(code, text): return text if no_color else code + text + R
    L   = LABELS.get(lang, LABELS['ja'])
    SEP = c(DC, '═' * 60)
    return f"{SEP}\n  {c(BR, L['error'])} {msg}\n  {c(DC, L['usage'])}\n{SEP}\n"

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

_BASE_CSS = ('*{box-sizing:border-box;margin:0;padding:0}'
             'body{background:#000;color:#aaa;'
             'font-family:"Courier New",Consolas,Monaco,"Lucida Console",monospace;'
             'font-size:12px;line-height:1.5;padding:16px}'
             'pre{font-family:inherit;white-space:pre;margin:0}'
             'a{color:#4ec9b0;text-decoration:none}a:hover{text-decoration:underline}')

def html_wrap(ansi_text, title='Weather'):
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{_BASE_CSS}</style></head>'
            f'<body><pre>{ansi_to_html(ansi_text)}</pre></body></html>')

# ---------- Full HTML weather page ----------
def render_html(location_name, data, lang='ja'):
    L      = LABELS.get(lang, LABELS['ja'])
    cur    = data['current']
    daily  = data['daily']
    hourly = data['hourly']
    now    = datetime.now().strftime('%H:%M')
    code   = cur['weathercode']
    wmo    = WMO_CODES.get(code, ('?','不明','Unknown'))
    art    = ASCII_ART[wmo_art(code)]

    def he(s): return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
    def tc(t):
        t = round(float(t))
        if t >= 35: return f'<b class="h">{t}</b>'
        if t >= 25: return f'<b class="w">{t}</b>'
        if t >= 15: return f'<b class="m">{t}</b>'
        if t >= 5:  return f'<b class="c">{t}</b>'
        return f'<b class="fr">{t}</b>'

    icon  = wmo[0]; desc = wmo[1] if lang=='ja' else wmo[2]
    temp  = cur['temperature_2m']; feels = cur['apparent_temperature']
    humid = cur['relativehumidity_2m']; wind = cur['windspeed_10m']
    precip= cur['precipitation']; uv = cur.get('uv_index')
    arrow = wind_arrow(cur.get('winddirection_10m'))
    art_h = '\n'.join(he(a) for a in art)
    uv_h  = f'<span class="lb">UV:</span> <b>{round(uv,1)}</b>' if uv is not None else ''

    if lang == 'ja':
        ih = (f'<div class="cd">{icon} <span class="d">{he(desc)}</span></div>'
              f'<div><span class="lb">気温:</span> {tc(temp)}°C <span class="dim">体感 {tc(feels)}°C</span></div>'
              f'<div><span class="lb">湿度:</span> <b>{round(humid)}%</b></div>'
              f'<div><span class="lb">風速:</span> <b>{arrow} {round(wind)} km/h</b></div>'
              f'<div><span class="lb">降水量:</span> <b>{round(precip,1)} mm</b> {uv_h}</div>')
    else:
        ih = (f'<div class="cd">{icon} <span class="d">{he(desc)}</span></div>'
              f'<div><span class="lb">Temp:</span> {tc(temp)}°C <span class="dim">feels {tc(feels)}°C</span></div>'
              f'<div><span class="lb">Humid:</span> <b>{round(humid)}%</b></div>'
              f'<div><span class="lb">Wind:</span> <b>{arrow} {round(wind)} km/h</b></div>'
              f'<div><span class="lb">Precip:</span> <b>{round(precip,1)} mm</b> {uv_h}</div>')

    days_h = ''
    for day_i in range(min(3, len(daily['time']))):
        date_str = daily['time'][day_i]
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            dl = (f'{JA_DAYS[dt.weekday()]}曜 {dt.month}月{dt.day}日' if lang=='ja'
                  else dt.strftime('%A, %b %d'))
        except Exception:
            dl = date_str
        d_code = daily['weathercode'][day_i]
        d_wmo  = WMO_CODES.get(d_code, ('?','不明','Unknown'))
        d_max  = daily['temperature_2m_max'][day_i]
        d_min  = daily['temperature_2m_min'][day_i]
        d_prob = (daily.get('precipitation_probability_max') or [None]*10)[day_i]
        d_uv   = (daily.get('uv_index_max') or [None]*10)[day_i]
        sr     = (daily.get('sunrise') or [None]*10)[day_i]
        ss     = (daily.get('sunset')  or [None]*10)[day_i]
        ph     = f'<span class="prob">{round(d_prob)}%</span>' if d_prob is not None else ''
        uvh    = f'<span class="dim">UV{round(d_uv,1)}</span>' if d_uv is not None else ''
        snh    = f'<span class="sun">↑{sr[11:16] if sr else "?"} ↓{ss[11:16] if ss else "?"}</span>'

        slots = [get_slot(hourly, date_str, hr) for hr in L['slot_hrs']]
        cells = ''
        for lbl, s in zip(L['slots'], slots):
            if s is None:
                cells += f'<td><div class="sl">{lbl}</div></td>'
                continue
            sc   = s['code']; sw = WMO_CODES.get(sc,('?','不明','Unknown'))
            sa   = ASCII_ART[wmo_art(sc)]
            svis = s['vis']
            svc  = f'{round(svis/1000)}km ' if svis is not None else ''
            cells += (f'<td><div class="sl">{lbl}</div>'
                      f'<div class="sc">'
                      f'<pre class="sa">{chr(10).join(he(a) for a in sa)}</pre>'
                      f'<div class="si">'
                      f'<div>{sw[0]} <span class="d">{he(sw[1] if lang=="ja" else sw[2])}</span></div>'
                      f'<div class="st2">{tc(s["temp"])}({tc(s["feels"])})°</div>'
                      f'<div class="sw2">{wind_arrow(s["wdir"])} {round(s["wind"])}km/h</div>'
                      f'<div class="se">{svc}</div>'
                      f'<div class="se"><span class="prob">{round(s["prob"] or 0)}%</span></div>'
                      f'</div></div>'
                      f'</td>')

        days_h += (f'<div class="day"><div class="dh">'
                   f'<span class="dn">{dl}</span> <span>{d_wmo[0]}</span>'
                   f' <span class="d">{he(d_wmo[1] if lang=="ja" else d_wmo[2])}</span>'
                   f' <span class="dt">{tc(d_max)}°/{tc(d_min)}°C</span>'
                   f' {ph} {uvh} {snh}</div>'
                   f'<table class="gt"><tr>{cells}</tr></table></div>')

    sw_url = '?lang=en' if lang=='ja' else '?lang=ja'
    sw_lbl = 'English' if lang=='ja' else '日本語'
    css = ('*{box-sizing:border-box;margin:0;padding:0}'
           'body{background:#000;color:#aaa;'
           'font-family:"Courier New",Consolas,Monaco,"Lucida Console",monospace;'
           'font-size:12px;line-height:1.4;padding:16px}'
           'a{color:#4ec9b0;text-decoration:none}a:hover{text-decoration:underline}'
           '.wrap{max-width:980px;margin:0 auto}'
           '.hd{display:flex;align-items:baseline;gap:10px;'
           'border-bottom:1px solid #1a3a4a;padding-bottom:8px;margin-bottom:14px}'
           '.cn{font-size:1.3em;font-weight:bold;color:#4ec9b0}.ct{color:#333;margin-left:8px}'
           '.cur{display:flex;gap:14px;border:1px solid #1a3a4a;padding:12px;margin-bottom:14px}'
           '.ca{color:#e5c07b;flex-shrink:0;line-height:1.3}'
           '.ci{flex:1;padding-top:2px}'
           '.cd{font-size:.95em;margin-bottom:5px}'
           '.d{color:#e5c07b}.lb{color:#4ec9b0}.dim{color:#444}'
           'b{color:#ddd}'
           '.day{margin-bottom:12px}'
           '.dh{border:1px solid #1a3a4a;border-bottom:none;padding:5px 10px;'
           'display:flex;align-items:center;gap:8px;flex-wrap:wrap}'
           '.dn{color:#e6edf3;font-weight:bold}.dt{margin-left:auto}'
           '.prob{color:#4ec9b0}.sun{color:#333}'
           '.gt{width:100%;border-collapse:collapse;border:1px solid #1a3a4a}'
           '.gt td{border:1px solid #1a3a4a;padding:8px 10px;vertical-align:top;width:25%}'
           '.sl{text-align:center;color:#3a4a5a;font-size:.85em;'
           'padding-bottom:5px;border-bottom:1px solid #1a3a4a;margin-bottom:7px}'
           '.sc{display:flex;gap:8px;align-items:flex-start}'
           '.sa{color:#e5c07b;font-size:.9em;line-height:1.25;flex-shrink:0}'
           '.si{flex:1;font-size:.9em;min-width:0}'
           '.st2{font-weight:bold;margin-bottom:2px}'
           '.sw2{color:#4ec9b0;margin-bottom:2px}'
           '.se{color:#555;font-size:.85em}'
           '.h{color:#e06c75}.w{color:#e5c07b}.m{color:#98c379}'
           '.c{color:#4ec9b0}.fr{color:#79c0ff}'
           '.ft{color:#333;border-top:1px solid #1a3a4a;'
           'margin-top:14px;padding-top:8px;font-size:.8em}')

    return (f'<!DOCTYPE html><html lang="{lang}"><head>'
            f'<meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{he(location_name)} - 天気</title>'
            f'<style>{css}</style></head><body><div class="wrap">'
            f'<div class="hd"><span class="cn">{he(location_name)}</span>'
            f'<span class="ct">{now}</span></div>'
            f'<div class="cur"><pre class="ca">{art_h}</pre>'
            f'<div class="ci">{ih}</div></div>'
            f'{days_h}'
            f'<div class="ft"><a href="{sw_url}">{sw_lbl}</a> · '
            f'<a href="https://open-meteo.com" target="_blank">Open-Meteo</a>'
            f'</div></div></body></html>')

# ---------- HTTP handler ----------
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def do_GET(self):
        parsed   = urlparse(self.path)
        qs       = parse_qs(parsed.query)
        ua       = self.headers.get('User-Agent', '')
        browser  = is_browser(ua)
        no_color = 'nocolor' in qs or 'nc' in qs or browser
        _lang_raw = qs.get('lang', ['ja'])[0]
        lang      = _lang_raw if re.match(r'^[a-z]{2,5}$', _lang_raw) else 'ja'

        path     = parsed.path.rstrip('/')
        location = re.sub(r'[\x00-\x1f\x7f]', '', unquote(path.lstrip('/')).replace('/', ' ').strip())[:200]

        def send(body, html=False):
            ct = 'text/html; charset=utf-8' if html else 'text/plain; charset=utf-8'
            self.send_response(200)
            self.send_header('Content-Type', ct)
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body.encode('utf-8'))

        if path == '/help':
            if browser:
                send(html_wrap(render_help(False, lang), 'Weather Help'), html=True)
            else:
                send(render_help(no_color, lang))
            return

        if path == '/auto':
            client_ip = (self.headers.get('X-Real-IP') or
                         (self.headers.get('X-Forwarded-For') or '').split(',')[0].strip())
            lat, lon, city = geocode_ip(client_ip)
            if lat is not None:
                try:
                    data = get_weather(lat, lon)
                    if browser:
                        send(render_html(city, data, lang), html=True)
                    else:
                        send(render(city, lat, lon, data, no_color, lang))
                except Exception:
                    err = render_error('Service temporarily unavailable.', False, lang)
                    send(html_wrap(err, 'Error - Weather') if browser
                         else render_error('Service temporarily unavailable.', no_color, lang), html=browser)
            else:
                send(render_help(no_color, lang) if not browser
                     else html_wrap(render_help(False, lang), 'Weather Help'), html=browser)
            return

        try:
            lat, lon, display_name = geocode(location)
            if lat is None:
                err = render_error(f'Location not found: {location}', False, lang)
                send(html_wrap(err, 'Error - Weather') if browser
                     else render_error(f'Location not found: {location}', no_color, lang),
                     html=browser)
                return
            data = get_weather(lat, lon)
            if browser:
                send(render_html(display_name, data, lang), html=True)
            else:
                send(render(display_name, lat, lon, data, no_color, lang))
        except Exception:
            err = render_error('Service temporarily unavailable.', False, lang)
            send(html_wrap(err, 'Error - Weather') if browser
                 else render_error('Service temporarily unavailable.', no_color, lang),
                 html=browser)

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    print(f'weather server listening on 127.0.0.1:{PORT}')
    server.serve_forever()
