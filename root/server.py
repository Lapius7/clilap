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

_FOOTER = '<div style="margin-top:16px;padding-top:6px;border-top:1px solid #1a1a1a;color:#333;font-size:11px;">©2025 CLI Lap by Lapius7. All rights reserved.</div>'

def html_wrap(ansi_text, title='clilap.org'):
    return (f'<!DOCTYPE html><html><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{title}</title><style>{_CSS}</style></head>'
            f'<body><pre>{ansi_to_html(ansi_text)}</pre>{_FOOTER}</body></html>')

def render_index(nc):
    def c(code, text): return text if nc else code + text + R
    W   = 80
    SEP = c(DC, '═' * W)
    div = c(DC, '  ' + '─' * (W - 2))

    art_lines = [
        "  ___ _ _ _           ",
        " / __| (_) |__ _ _ __ ",
        "| (__| | | / _` | '_ \\",
        " \\___|_|_|_\\__,_| .__/",
        "                |_|   ",
    ]

    examples = [
        (
            'clilap.org/weather/Tokyo',
            [
                c(BC, '  東京都 東京 JP') + '  ⛅ 曇り  ' + c(BW, '23°C') + c(D, '  (体感 21°C)'),
                c(D,  '  湿度 65%  風 12km/h N  視程 10km  UV 4'),
                c(DC, '  月 ⛅ 23/18°C') + '   ' + c(DC, '火 ☁ 22/17°C') + '   ' + c(DC, '水 🌧 20/15°C'),
            ]
        ),
        (
            'clilap.org/ipinfo',
            [
                c(BC, '  IP      ') + c(C, '203.0.113.1'),
                c(BC, '  City    ') + 'Tokyo · Tokyo · JP 🇯🇵',
                c(BC, '  Org     ') + c(D, 'AS2518 BIGLOBE Inc.'),
                c(BC, '  TZ      ') + c(D, 'Asia/Tokyo  UTC+9'),
            ]
        ),
        (
            'clilap.org/qr/https://lapius7.com',
            [
                c(DC, '  → ターミナルにQRコードを表示'),
                c(D,  '    スマートフォンで直接スキャン可能'),
            ]
        ),
        (
            'clilap.org/cheat/git',
            [
                c(BW, '  git') + c(D, '  ─  分散型バージョン管理システム'),
                '',
                c(D,  '  $ git init') + c(DC, '                # 新規リポジトリ'),
                c(D,  '  $ git clone <url>') + c(DC, '          # クローン'),
                c(D,  '  $ git commit -m "msg"') + c(DC, '      # コミット'),
            ]
        ),
        (
            'clilap.org/dep -F file=@package.json',
            [
                c(DC, '  → 依存関係ツリーを解析しURLを発行'),
                c(BC, '  curl:    ') + c(BW, 'curl dep.clilap.org/ab12cd'),
                c(BC, '  browser: ') + c(C, 'https://dep.clilap.org/ab12cd'),
            ]
        ),
    ]

    services = [
        '/weather',   '/ipinfo',    '/cheat',     '/qr',
        '/hash',      '/b64',       '/uuid',       '/epoch',
        '/dns',       '/whois',     '/color',      '/github',
        '/headers',   '/parrot',    '/password',   '/unit',
        '/rate',      '/time',      '/ssl',        '/sec',
        '/dnsmap',    '/portcheck', '/redirect',   '/package',
        '/ascii',     '/base',      '/urlencode',  '/urldecode',
        '/cal',       '/cron',      '/totp',       '/mock',
        '/gitignore', '/license',   '/json',       '/diff',
        '/md',        '/unicode',   '/regex',      '/dep',
        '/log',
    ]
    svc_cols = []
    for i in range(0, len(services), 4):
        row = services[i:i+4]
        svc_cols.append('  ' + ''.join(pad_to(c(BC, s), 14) for s in row))

    lines = [SEP]
    for a in art_lines:
        lines.append(c(BC, a))
    lines += [
        c(D, '  curl から使えるAPIツール集  —  clilap.org'),
        SEP,
        '',
        f'  {c(BW, "$ curl")} {c(C, "clilap.org/help")}  {c(DC, "# 全サービスの完全ドキュメント")}',
        '',
        SEP,
        '',
    ]
    for cmd, resp in examples:
        lines.append(f'  {c(BW, "$ curl")} {c(C, cmd)}')
        lines.extend(resp)
        lines.append('')
    lines += [
        '  ' + c(BW, '$') + ' ' + c(C, 'tail -f app.log | curl -T - "$UPLOAD"'),
        c(DC, '  → ログをリアルタイムでURL共有 (ANSI色保持、ブラウザでライブ表示)'),
        '',
        div,
        f'  {c(D, "サービス一覧:")}  {c(DC, "詳細 → curl clilap.org/help")}',
        '',
        *svc_cols,
        '',
        f'  {c(DC, "共通オプション:")}  {c(DC, "?ja  ?en")}',
        div,
        f'  {c(C, "github.com/Lapius7/clilap")}  {c(D, "by")} {c(C, "@Lapius7")}',
        SEP,
    ]
    return '\n'.join(str(l) for l in lines) + '\n'

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
        c(BC, '    /hash      /b64       /uuid      /epoch'),
        c(BC, '    /dns       /whois     /color     /github'),
        c(BC, '    /headers   /parrot    /password  /unit'),
        c(BC, '    /rate      /time      /ssl       /sec'),
        c(BC, '    /dnsmap    /portcheck /redirect  /package'),
        c(BC, '    /ascii     /base      /urlencode /urldecode'),
        c(BC, '    /cal       /cron      /totp      /mock'),
        c(BC, '    /gitignore /license   /json      /diff'),
        c(BC, '    /md        /unicode   /regex     /dep'),
        c(BC, '    /log'),
        '',
        c(DC, '  curl clilap.org/help') + c(D, '  for full documentation'),
        SEP,
    ]) + '\n'

def render_help(nc):
    def c(code, text): return text if nc else code + text + R
    W   = 80
    SEP = c(DC, '═' * W)
    div = c(DC, '  ' + '─' * (W - 2))
    def h(title):       return f'\n{SEP}\n  {c(BW, title)}\n{SEP}'
    def sec(name, desc):return f'\n  {c(BC, name)}\n  {c(D, desc)}'
    def ex(cmd):        return f'    {c(BW, cmd)}'
    def opt(flag, desc):return f'    {c(C, flag):<36}{c(D, desc)}'
    def note(text):     return f'  {c(D, text)}'

    lines = [
        SEP,
        f'  {c(BW, "clilap.org/help")}  {c(DC, "完全ドキュメント")}',
        div,
        note('すべてのサービスはブラウザでもcurlでも同じURLでアクセスできます。'),
        note('HTTP (https://なし) でも動作します。例: curl clilap.org/ipinfo'),
        SEP,

        h('/parrot  🦜 カラフルアニメーション'),
        '',
        sec('概要', 'ターミナルにカラフルなオウムのアニメーションを表示します。'),
        '',
        ex('curl clilap.org/parrot'),
        ex('curl clilap.org/parrot/stream   # ストリーム再生'),
        '',
        note('ブラウザでアクセスするとリアルタイムアニメーションが表示されます。'),

        h('/qr  🔲 QRコード生成'),
        '',
        sec('概要', 'テキスト・URLをターミナル上でQRコードに変換します。スマートフォンで読み取り可能。'),
        '',
        ex('curl clilap.org/qr/Hello'),
        ex('curl clilap.org/qr/https://lapius7.com'),
        ex('curl clilap.org/qr/あいうえお'),
        '',
        note('オプション:'),
        opt('?size=N',       'セルサイズ 1〜10 (デフォルト: 1)'),
        opt('?margin=N',     '余白サイズ 0〜10 (デフォルト: 1)'),
        opt('?level=L|M|Q|H','誤り訂正レベル (デフォルト: M)'),
        opt('?compact',      '半ブロック文字でコンパクト表示'),
        opt('?invert',       '色反転 (白背景ターミナル用)'),
        '',
        ex('curl "clilap.org/qr/Hello?size=3&level=H"'),

        h('/ipinfo  🌐 IP情報'),
        '',
        sec('概要', 'IPアドレスから位置情報・組織・タイムゾーンなどを取得します。'),
        '',
        ex('curl clilap.org/ipinfo              # 自分のIP (自動判定)'),
        ex('curl clilap.org/ipinfo/me           # 自分のIP (明示)'),
        ex('curl clilap.org/ipinfo/1.1.1.1      # Cloudflare DNS'),
        ex('curl clilap.org/ipinfo/8.8.8.8      # Google DNS'),
        '',
        note('取得できる情報: ip · hostname · city · region · country · timezone · org'),
        '',
        note('オプション:'),
        opt('?json',  'JSON形式で出力 (API連携・スクリプト向け)'),

        h('/weather  ⛅ 天気予報'),
        '',
        sec('概要', '世界中の都市の現在の天気と7日間予報をターミナルで表示します。'),
        '',
        ex('curl clilap.org/weather              # 現在地 (IP位置情報を使用)'),
        ex('curl clilap.org/weather/Tokyo'),
        ex('curl clilap.org/weather/Osaka'),
        ex('curl clilap.org/weather/Sapporo'),
        ex('curl clilap.org/weather/New+York'),
        ex('curl clilap.org/weather/東京都/新宿区  # 都道府県/市区町村で精度UP'),
        '',
        note('取得できる情報: 気温・体感温度・天気・湿度・風速・降水量・UV指数 + 7日間予報'),
        '',
        note('オプション:'),
        opt('?lang=en', '英語表示'),
        opt('?lang=ja', '日本語表示 (デフォルト)'),

        h('/cheat  📖 コマンドチートシート'),
        '',
        sec('概要', '3,000以上のコマンドのチートシートを表示します。tldr-pagesをベースにしています。'),
        '',
        ex('curl clilap.org/cheat/git'),
        ex('curl clilap.org/cheat/curl'),
        ex('curl clilap.org/cheat/docker'),
        ex('curl clilap.org/cheat/vim'),
        ex('curl clilap.org/cheat/ls'),
        ex('curl clilap.org/cheat/tar'),
        ex('curl clilap.org/cheat/:list        # 全コマンド一覧'),
        '',
        note('オプション:'),
        opt('?en', '英語表示'),
        opt('?ja', '日本語表示 (デフォルト)'),
        '',
        note('データソース: github.com/tldr-pages/tldr'),

        h('/hash  #️⃣  ハッシュ計算'),
        '',
        sec('概要', 'テキスト・データのハッシュ値を計算します。ファイル改ざん検知・パスワード確認などに。'),
        '',
        ex('curl clilap.org/hash/md5/hello'),
        ex('curl clilap.org/hash/sha1/hello'),
        ex('curl clilap.org/hash/sha256/hello'),
        ex('curl clilap.org/hash/sha512/hello'),
        ex('echo -n "hello" | curl -d @- clilap.org/hash/sha256  # stdin から'),
        ex('cat file.txt | curl -d @- clilap.org/hash/md5         # ファイルのハッシュ'),
        '',
        note('対応アルゴリズム:'),
        note('  md5    (128bit) 高速・広く普及。衝突リスクあり、互換用途のみ推奨'),
        note('  sha1   (160bit) 後方互換用途向け'),
        note('  sha256 (256bit) 現在の標準。セキュリティ用途に推奨'),
        note('  sha512 (512bit) より高いセキュリティが必要な場面に'),

        h('/b64  🔒 Base64 エンコード/デコード'),
        '',
        sec('概要', 'バイナリデータをテキスト形式で扱う変換方式。URLやHTTPヘッダーでのデータ送信に便利。'),
        '',
        ex('curl clilap.org/b64/encode/hello'),
        ex('curl clilap.org/b64/decode/aGVsbG8='),
        ex('echo "hello world" | curl -d @- clilap.org/b64/encode'),
        ex('echo "aGVsbG8=" | curl -d @- clilap.org/b64/decode'),
        ex('cat binary.bin | curl -d @- clilap.org/b64/encode     # バイナリも可'),

        h('/uuid  🔑 UUID生成'),
        '',
        sec('概要', 'ランダムなUUID v4を生成します。データベースID・一意識別子の生成に。'),
        '',
        ex('curl clilap.org/uuid          # 1件生成'),
        ex('curl clilap.org/uuid/5        # 5件生成'),
        ex('curl clilap.org/uuid/100      # 最大100件'),
        ex('curl clilap.org/uuid?n=10     # クエリパラメータでも指定可'),

        h('/epoch  🕐 UNIXタイム変換'),
        '',
        sec('概要', 'UNIXタイムスタンプと人間が読める日時を相互変換します。引数なしで現在時刻を表示。'),
        '',
        ex('curl clilap.org/epoch                        # 現在時刻'),
        ex('curl clilap.org/epoch/1700000000             # タイムスタンプ → 日時'),
        ex('curl clilap.org/epoch/2024-01-01             # 日付 → タイムスタンプ'),
        ex('curl clilap.org/epoch/2024-01-01T12:00:00   # 日時 → タイムスタンプ'),
        '',
        note('対応入力フォーマット: unix timestamp, YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS'),

        h('/dns  🌍 DNS Lookup'),
        '',
        sec('概要', 'DNSレコードを照会します。ドメインのIPアドレス・メール設定・ネームサーバなどを確認できます。'),
        '',
        ex('curl clilap.org/dns/google.com          # Aレコード (デフォルト)'),
        ex('curl clilap.org/dns/google.com/MX       # メールサーバ'),
        ex('curl clilap.org/dns/google.com/NS       # ネームサーバ'),
        ex('curl clilap.org/dns/google.com/TXT      # TXTレコード (SPF等)'),
        ex('curl clilap.org/dns/google.com/AAAA     # IPv6アドレス'),
        ex('curl clilap.org/dns/google.com/CNAME    # CNAMEレコード'),
        ex('curl clilap.org/dns/8.8.8.8/PTR         # 逆引き'),
        '',
        note('対応タイプ: A  AAAA  MX  NS  TXT  CNAME  SOA  PTR'),

        h('/whois  📋 WHOIS Lookup'),
        '',
        sec('概要', 'ドメインの登録情報を照会します。登録者・レジストラ・有効期限・ネームサーバを確認できます。'),
        '',
        ex('curl clilap.org/whois/google.com'),
        ex('curl clilap.org/whois/github.com'),
        ex('curl clilap.org/whois/lapius7.com'),
        '',
        note('取得できる情報: Registrar · Created · Expires · Updated · Status · Name Servers'),

        h('/color  🎨 カラー変換'),
        '',
        sec('概要', 'HEXコードやRGB値からhex/rgb/hslに変換します。ターミナルにカラースウォッチも表示します。'),
        '',
        ex('curl clilap.org/color/ff6b6b            # HEX → hex/rgb/hsl'),
        ex('curl clilap.org/color/255,107,107        # RGB → hex/rgb/hsl'),
        ex('curl clilap.org/color/3498db'),
        ex('curl clilap.org/color/1a1a2e'),
        ex('curl clilap.org/color/fff               # 3桁HEXも可'),

        h('/github  🐙 GitHub 情報'),
        '',
        sec('概要', 'GitHub APIを使ってリポジトリ・ユーザー情報をターミナルで表示します。'),
        '',
        ex('curl clilap.org/github/torvalds              # ユーザープロフィール'),
        ex('curl clilap.org/github/torvalds/linux         # リポジトリ概要'),
        ex('curl clilap.org/github/torvalds/linux/readme  # README表示'),
        ex('curl clilap.org/github/torvalds/linux/commits # 最新コミット'),
        ex('curl clilap.org/github/torvalds/linux/releases# リリース履歴'),
        ex('curl clilap.org/github/torvalds/linux/issues  # オープンなIssue'),
        ex('curl clilap.org/github/torvalds/linux/prs     # プルリクエスト'),
        '',
        note('ビュー: (なし)=概要  readme  commits  releases  issues  prs'),

        h('/headers  🔍 リクエストヘッダー確認'),
        '',
        sec('概要', 'サーバーが受け取ったHTTPリクエストヘッダーをそのまま返します。'),
        note('デバッグや、プロキシ・CDNの設定確認に使えます。'),
        '',
        ex('curl clilap.org/headers'),
        ex('curl -H "X-Custom: hello" clilap.org/headers  # カスタムヘッダー確認'),

        h('/password  🔐 パスワード生成'),
        '',
        sec('概要', '暗号学的に安全なランダムパスワードまたはパスフレーズを生成します。'),
        '',
        ex('curl clilap.org/password             # 20文字パスワード'),
        ex('curl clilap.org/password/32          # 32文字'),
        ex('curl clilap.org/password?no-symbols  # 記号なし'),
        ex('curl clilap.org/password/phrase      # パスフレーズ'),
        ex('curl clilap.org/password/phrase/5    # 5ワードのパスフレーズ'),

        h('/unit  📐 単位変換'),
        '',
        sec('概要', '長さ・重さ・時間・データ・速度・温度の単位を変換します。'),
        '',
        ex('curl clilap.org/unit/100km/mi        # 距離'),
        ex('curl clilap.org/unit/1024MB/GiB      # データサイズ'),
        ex('curl clilap.org/unit/100C/F          # 温度'),
        ex('curl clilap.org/unit/3600s/h         # 時間'),
        ex('curl clilap.org/unit/1kg/lb          # 重さ'),
        '',
        note('カテゴリ: length  weight  time  data  speed  temperature'),

        h('/rate  💱 為替レート'),
        '',
        sec('概要', '法定通貨の為替レートと暗号資産の価格をリアルタイムで取得します。'),
        '',
        ex('curl clilap.org/rate/USD             # ドルのレート一覧'),
        ex('curl clilap.org/rate/USD/JPY         # USD → JPY'),
        ex('curl clilap.org/rate/USD/JPY,EUR,GBP # 複数通貨'),
        ex('curl clilap.org/rate/BTC             # Bitcoinの価格'),
        ex('curl clilap.org/rate/ETH/USD         # ETH → USD'),
        '',
        note('Forex: Frankfurter (ECB)  Crypto: CoinGecko'),

        h('/time  🕐 世界時計'),
        '',
        sec('概要', '世界中の都市の現在時刻を表示します。都市名またはIANAタイムゾーン名で指定。'),
        '',
        ex('curl clilap.org/time                 # 主要都市の一覧'),
        ex('curl clilap.org/time/Tokyo           # 東京の時刻'),
        ex('curl clilap.org/time/New+York        # ニューヨーク'),
        ex('curl clilap.org/time/Tokyo/London    # 2都市を比較'),
        ex('curl clilap.org/time/America/Chicago # IANAタイムゾーン名'),

        h('/ssl  🔒 SSL証明書確認'),
        '',
        sec('概要', 'ドメインのSSL/TLS証明書の詳細を取得します。有効期限・発行者・SANsを確認できます。'),
        '',
        ex('curl clilap.org/ssl/github.com'),
        ex('curl clilap.org/ssl/lapius7.com'),
        '',
        note('取得できる情報: Subject · Issuer · Expires (残日数) · SANs'),

        h('/sec  🛡 HTTPセキュリティヘッダー'),
        '',
        sec('概要', 'ウェブサイトのHTTPセキュリティヘッダーを確認してスコアを表示します。'),
        '',
        ex('curl clilap.org/sec/github.com'),
        ex('curl clilap.org/sec/lapius7.com'),
        '',
        note('確認項目: HSTS · CSP · X-Content-Type · X-Frame · Referrer-Policy · Permissions-Policy'),
        note('グレード: A+ (6/6) A (5/6) B (4/6) C (3/6) D (2/6) F'),

        h('/dnsmap  🗺 DNSマップ'),
        '',
        sec('概要', '4つのDNSリゾルバー (Cloudflare/Google/Quad9/OpenDNS) で同時にAレコードを照会します。'),
        '',
        ex('curl clilap.org/dnsmap/github.com'),
        ex('curl clilap.org/dnsmap/lapius7.com'),
        '',
        note('GeoDNSや伝播中のドメインで異なる結果が出た場合に警告を表示します。'),

        h('/portcheck  🔌 ポートチェック'),
        '',
        sec('概要', '外部ホストの指定ポートが開いているか確認します。レスポンスタイムも表示。'),
        '',
        ex('curl clilap.org/portcheck/github.com/443'),
        ex('curl clilap.org/portcheck/example.com/22   # SSH'),
        ex('curl clilap.org/portcheck/example.com/3306 # MySQL'),
        '',
        note('既知のサービス名を自動判定: HTTP/HTTPS/SSH/FTP/MySQL/Redis/MongoDB...'),

        h('/redirect  🔗 リダイレクトチェーン'),
        '',
        sec('概要', 'URLのリダイレクトチェーンを全て追跡して表示します。短縮URLの展開に。'),
        '',
        ex('curl clilap.org/redirect/https://bit.ly/...'),
        ex('curl clilap.org/redirect/https://t.co/...'),
        '',
        note('最大10ホップを追跡。各ステップのHTTPステータスコードを表示。'),

        h('/package  📦 パッケージ情報'),
        '',
        sec('概要', 'npmとPyPIのパッケージ情報を取得します。バージョン・ライセンス・依存関係を確認。'),
        '',
        ex('curl clilap.org/package/npm/express'),
        ex('curl clilap.org/package/npm/react'),
        ex('curl clilap.org/package/npm/@types/node'),
        ex('curl clilap.org/package/pypi/requests'),
        ex('curl clilap.org/package/pypi/numpy'),
        '',
        note('レジストリ: npm  pypi'),

        h('/ascii  🎨 ASCIIアート'),
        '',
        sec('概要', 'figletを使ってテキストをASCIIアートに変換します。'),
        '',
        ex('curl clilap.org/ascii/Hello'),
        ex('curl "clilap.org/ascii/Hi?font=banner"'),
        ex('curl "clilap.org/ascii/Code?font=slant"'),
        '',
        note(f'フォント: banner big block lean mini script slant small standard ...'),

        h('/base  🔢 進数変換'),
        '',
        sec('概要', '2〜36進数を相互変換します。'),
        '',
        ex('curl clilap.org/base/10/255           # 10進 → 主要進数(2,8,16,36)'),
        ex('curl clilap.org/base/16/ff            # 16進 → 主要進数'),
        ex('curl clilap.org/base/10/2/255         # 10進 → 2進'),
        ex('curl clilap.org/base/2/10/11111111    # 2進 → 10進'),
        ex('curl clilap.org/base/10/255?all       # 2〜36進数 全件表示'),
        '',
        note('対応進数: 2〜36'),

        h('/urlencode  /urldecode  🔗 URLエンコード'),
        '',
        sec('概要', 'テキストをURLエンコード・デコードします。'),
        '',
        ex('curl clilap.org/urlencode/hello world'),
        ex('curl clilap.org/urlencode/こんにちは'),
        ex('curl clilap.org/urldecode/hello%20world'),
        ex('echo "hello world" | curl -d @- clilap.org/urlencode'),

        h('/cal  📅 カレンダー'),
        '',
        sec('概要', 'カレンダーをターミナルに表示します。今日の日付はハイライト、週末は黄色で表示。'),
        '',
        ex('curl clilap.org/cal                   # 今年のカレンダー'),
        ex('curl clilap.org/cal/2026              # 指定年'),
        ex('curl clilap.org/cal/2026/6            # 指定月'),

        h('/cron  ⏰ cron式パーサー'),
        '',
        sec('概要', 'cron式を人間が読める説明文に変換します。'),
        '',
        ex('curl clilap.org/cron/0_9_%2A_%2A_1-5  # 平日9時 (スペースは_)'),
        ex('curl clilap.org/cron/%2A/2_%2A_%2A_%2A # 2時間おき'),
        ex('curl clilap.org/cron/@daily'),
        ex('curl clilap.org/cron/@weekly'),
        '',
        note('URLではスペースを_かURLエンコードで置換してください。'),

        h('/totp  🔑 TOTP生成'),
        '',
        sec('概要', 'Base32シークレットからTOTP (Time-based One-Time Password) を生成します。'),
        '',
        ex('curl clilap.org/totp/JBSWY3DPEHPK3PXP'),
        '',
        note('⚠ 実際の認証コードをHTTP経由で送信しないでください (テスト用のみ)。'),

        h('/mock  🎲 モックデータ生成'),
        '',
        sec('概要', 'テスト用のダミーデータ (JSONユーザーデータ / Loremテキスト) を生成します。'),
        '',
        ex('curl clilap.org/mock/json             # 偽ユーザー1件'),
        ex('curl clilap.org/mock/json/10          # 10件'),
        ex('curl clilap.org/mock/lorem            # Loremテキスト1段落'),
        ex('curl clilap.org/mock/lorem/3          # 3段落'),

        h('/gitignore  🚫 .gitignore生成'),
        '',
        sec('概要', 'GitHub gitignoreテンプレートを取得します。複数言語を組み合わせ可能。'),
        '',
        ex('curl clilap.org/gitignore/node'),
        ex('curl clilap.org/gitignore/python'),
        ex('curl clilap.org/gitignore/node,python,macos,vscode'),
        '',
        note('対応言語: node python rust go java ruby php macos windows vscode jetbrains ...'),

        h('/license  📜 ライセンステキスト'),
        '',
        sec('概要', 'オープンソースライセンスのテキストを取得します。著作者名と年を自動挿入。'),
        '',
        ex('curl clilap.org/license/mit'),
        ex('curl "clilap.org/license/mit?holder=Lapius7"'),
        ex('curl clilap.org/license/apache'),
        ex('curl clilap.org/license/gpl-3'),
        '',
        note('対応: mit  apache  gpl-3  gpl-2  lgpl  mpl  isc  bsd-2  bsd-3  unlicense  agpl  cc0'),

        h('/json  {} JSONフォーマッター'),
        '',
        sec('概要', 'JSONをフォーマット・バリデートします。POSTでJSONを送信してください。'),
        '',
        ex('echo \'{"a":1,"b":2}\' | curl -d @- clilap.org/json'),
        ex('curl -d @data.json clilap.org/json'),
        ex('curl -d @data.json "clilap.org/json?indent=4"'),
        ex('curl -d @data.json "clilap.org/json?compact"'),
        '',
        note('オプション: ?indent=N (デフォルト2)  ?compact  ?keys (キーをソート)'),

        h('/diff  📝 差分表示'),
        '',
        sec('概要', '2つのファイルの差分をカラーで表示します (unified diff形式)。'),
        '',
        ex('curl -F "a=@old.txt" -F "b=@new.txt" clilap.org/diff'),
        ex('curl -F "a=@file1" -F "b=@file2" clilap.org/diff'),

        h('/md  📄 Markdownレンダリング'),
        '',
        sec('概要', 'MarkdownをANSI付きのターミナル向けテキストに変換します。'),
        '',
        ex('curl -d @README.md clilap.org/md'),
        ex('cat README.md | curl -d @- clilap.org/md'),

        h('/dns/{domain}/all  🌐 DNS全レコードエクスポート'),
        '',
        sec('概要', 'ドメインの全DNS レコードタイプ (A/AAAA/MX/NS/TXT/CNAME/SOA/CAA/SRV) を一括取得。'),
        '',
        ex('curl clilap.org/dns/github.com/all'),
        ex('curl clilap.org/dns/lapius7.com/all'),

        h('/unicode  🔡 Unicode ツール'),
        '',
        sec('概要', 'Unicodeの情報表示・テキスト検索・ファンシーテキスト変換を行います。'),
        '',
        ex('curl clilap.org/unicode/A             # 文字情報'),
        ex('curl clilap.org/unicode/あ'),
        ex('echo "Hello, 世界" | curl -d @- clilap.org/unicode/inspect'),
        ex('curl clilap.org/unicode/search/star   # 名前で検索'),
        ex('curl clilap.org/unicode/fancy/bold/Hello'),
        ex('curl clilap.org/unicode/fancy/script/Hello'),
        ex('curl clilap.org/unicode/fancy          # スタイル一覧'),
        '',
        note('ファンシースタイル: bold italic bolditalic script boldscript gothic doublestruck'),
        note('                    sans sansbold monospace circled bubble ...'),

        h('/regex  🔍 正規表現テスト'),
        '',
        sec('概要', 'Pythonの正規表現エンジンでパターンをテストします。マッチ位置・グループを表示。'),
        '',
        ex('curl clilap.org/regex/\\d+'),
        ex('echo "abc 123 def 456" | curl -d @- clilap.org/regex/\\\\d+'),
        ex('echo "Hello World" | curl -d @- "clilap.org/regex/hello?flags=i"'),
        ex('echo "foo\\nbar" | curl -d @- "clilap.org/regex/^bar?flags=m"'),
        ex('echo "2024-01-15" | curl -d @- "clilap.org/regex/(\\\\d{4})-(\\\\d{2})-(\\\\d{2})"'),
        '',
        note('フラグ: ?flags=i (大文字小文字無視)  ?flags=m (複数行)  ?flags=s (dotall)  ?flags=im (組み合わせ)'),
        note('使用エンジン: Python re  — グループ・名前付きグループに対応'),

        h('/dep  📦 依存関係可視化'),
        '',
        sec('概要', 'package.jsonをアップロードして依存関係ツリーを解析・URLで共有します。'),
        '',
        ex('curl -F "file=@package.json" clilap.org/dep'),
        ex('cat package.json | curl --data-binary @- clilap.org/dep'),
        ex('curl dep.clilap.org/ab12cd            # ツリー表示'),
        ex('curl dep.clilap.org/ab12cd/cycles      # 循環依存検出'),
        ex('curl dep.clilap.org/ab12cd/heavy       # 巨大依存ランキング'),
        ex('curl dep.clilap.org/ab12cd/licenses    # ライセンス検査'),
        '',
        note('発行されたURLはブラウザでも確認可能: https://dep.clilap.org/ab12cd'),
        note('解析データは無期限保存されます。'),

        h('/log  📡 リアルタイムログ共有'),
        '',
        sec('概要', 'コマンド出力やログファイルをリアルタイムでURL共有します。ANSI色は保持されます。'),
        '',
        note('2段階方式 (go run等、永久に終了しないプロセスでも確実にURLが手に入ります):'),
        ex('RES=$(curl -s clilap.org/log/new)'),
        ex('UPLOAD=$(echo "$RES" | grep ^upload: | awk \'{print $2}\')'),
        ex('tail -f app.log | curl -T - "$UPLOAD"'),
        ex('npm run dev 2>&1 | curl -T - "$UPLOAD"'),
        '',
        note('発行されたURLをブラウザで開くとリアルタイムに更新が表示されます: https://log.clilap.org/abc123'),
        note('curlでも閲覧可能: curl log.clilap.org/abc123'),
        note('オプション:'),
        opt('?grep=pattern', '正規表現でログ行をフィルタ'),

        '',
        SEP,
        f'  {c(DC, "共通オプション:")}  {c(DC, "?ja  ?en")}',
        div,
        f'  {c(C, "github.com/Lapius7/clilap")}  {c(D, "by")} {c(C, "@Lapius7")}',
        SEP,
    ]
    return '\n'.join(str(l) for l in lines) + '\n'


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a): pass

    def do_GET(self):
        parsed  = urlparse(self.path)
        qs      = parse_qs(parsed.query, keep_blank_values=True)
        ua      = self.headers.get('User-Agent', '')
        browser = is_browser(ua)
        nc      = 'nocolor' in qs or 'nc' in qs or browser

        path = parsed.path.rstrip('/') or '/'

        if path == '/help':
            status = 200
            body_ansi = render_help(nc if not browser else False)
            ct = 'text/html; charset=utf-8' if browser else 'text/plain; charset=utf-8'
            body = html_wrap(body_ansi, 'help - Clilap') if browser else body_ansi
        elif path == '/':
            status = 200
            body_ansi = render_index(nc if not browser else False)
            ct = 'text/html; charset=utf-8' if browser else 'text/plain; charset=utf-8'
            body = html_wrap(body_ansi, 'Clilap - curl tools') if browser else body_ansi
        else:
            status = 404
            body_ansi = render_not_found(path, nc if not browser else False)
            ct = 'text/html; charset=utf-8' if browser else 'text/plain; charset=utf-8'
            body = html_wrap(body_ansi, '404 - Clilap') if browser else body_ansi

        self.send_response(status)
        self.send_header('Content-Type', ct)
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body.encode('utf-8'))

if __name__ == '__main__':
    server = HTTPServer(('127.0.0.1', PORT), Handler)
    print(f'root server listening on 127.0.0.1:{PORT}')
    server.serve_forever()
