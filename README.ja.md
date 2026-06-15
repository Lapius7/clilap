<div align="center">
<pre>
        __ _ _            
  _____/ /(_) /___ _____  
 / ___/ / / / / __ `/ __ \ 
/ /__/ / / / / /_/ / /_/ / 
\___/_/_/_/_/\__,_/ .___/  
                 /_/       
</pre>
</div>

[![Stars](https://img.shields.io/github/stars/Lapius7/clilap?style=flat-square&color=yellow)](https://github.com/Lapius7/clilap/stargazers)
[![Forks](https://img.shields.io/github/forks/Lapius7/clilap?style=flat-square&color=blue)](https://github.com/Lapius7/clilap/network/members)
[![Issues](https://img.shields.io/github/issues/Lapius7/clilap?style=flat-square)](https://github.com/Lapius7/clilap/issues)
[![Last Commit](https://img.shields.io/github/last-commit/Lapius7/clilap?style=flat-square)](https://github.com/Lapius7/clilap/commits)
[![Repo Size](https://img.shields.io/github/repo-size/Lapius7/clilap?style=flat-square)](https://github.com/Lapius7/clilap)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-3776ab?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Node.js](https://img.shields.io/badge/node.js-18+-339933?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org/)
[![curl](https://img.shields.io/badge/試す-curl%20clilap.org-4ec9b0?style=flat-square)](https://clilap.org)

インストール不要で `curl` から使える開発者向けツール集。天気予報・コマンドチートシート・GitHub情報・DNS・ハッシュ計算など、ターミナルから直接アクセスできる。

```
curl clilap.org
```

[English README](README.md)

---

## サービス一覧

### 🌤 天気予報 — `/weather`
[Open-Meteo](https://open-meteo.com/) と [Nominatim](https://nominatim.org/) を使ったリアルタイム天気予報。

```bash
curl clilap.org/weather              # IPから自動検出
curl clilap.org/weather/Tokyo        # 都市名
curl clilap.org/weather/東京都/新宿区  # 都道府県/市区町村
curl clilap.org/weather/Tokyo?en     # 英語表示
```

### 📖 チートシート — `/cheat`
[tldr-pages](https://github.com/tldr-pages/tldr) によるコマンドリファレンス。

```bash
curl clilap.org/cheat/git            # git チートシート
curl clilap.org/cheat/docker         # docker チートシート
curl clilap.org/cheat/:list          # 対応コマンド一覧
curl clilap.org/cheat/git?ja         # 日本語（デフォルト）
curl clilap.org/cheat/git?en         # 英語
```

### 🐙 GitHub — `/github`
GitHub リポジトリ情報を curl で取得。

```bash
curl clilap.org/github/torvalds              # ユーザー情報 + リポジトリ一覧
curl clilap.org/github/curl/curl             # リポジトリ概要（stars/forks/言語/ライセンス）
curl clilap.org/github/curl/curl/readme      # README表示
curl clilap.org/github/curl/curl/readme/ja   # 日本語README（なければデフォルトにフォールバック）
curl clilap.org/github/curl/curl/releases    # リリース一覧
curl clilap.org/github/curl/curl/commits     # コミット履歴
curl clilap.org/github/curl/curl/issues      # オープンなIssue
curl clilap.org/github/curl/curl/prs         # オープンなPR
curl clilap.org/github/curl/curl/stars       # スター数のみ
```

### 🌐 IP情報 — `/ipinfo`
IPアドレスの位置情報とメタデータ。

```bash
curl clilap.org/ipinfo               # 現在のIP
curl clilap.org/ipinfo/8.8.8.8       # 特定IPを調べる
```

### 🔍 リクエストヘッダー確認 — `/headers`
送信中のHTTPヘッダーを確認。

```bash
curl clilap.org/headers
```

### 🔑 UUID生成 — `/uuid`
ランダムUUID (v4) を生成。

```bash
curl clilap.org/uuid                 # 1件
curl clilap.org/uuid/5               # 5件
```

### 🔒 Base64 — `/b64`
Base64のエンコード・デコード。

```bash
curl clilap.org/b64/encode/hello
curl clilap.org/b64/decode/aGVsbG8=
echo "hello world" | curl -d @- clilap.org/b64/encode
```

### #️⃣ ハッシュ計算 — `/hash`
暗号学的ハッシュを計算。

対応アルゴリズム: `md5` `sha1` `sha256` `sha512` `sha3_256` `sha3_512`

```bash
curl clilap.org/hash/sha256/hello
echo "hello" | curl -d @- clilap.org/hash/sha256
```

### 🕐 Epoch変換 — `/epoch`
UNIXタイムスタンプと日時を相互変換。

```bash
curl clilap.org/epoch                # 現在時刻（UTC + ローカル時刻）
curl clilap.org/epoch/1700000000     # UNIXタイム → 日時
curl clilap.org/epoch/2024-01-01     # 日付 → UNIXタイム
```

### 🌍 DNS Lookup — `/dns`
DNSレコードを調べる。

対応タイプ: `A` `AAAA` `MX` `NS` `TXT` `CNAME` `SOA` `PTR`

```bash
curl clilap.org/dns/google.com       # Aレコード（デフォルト）
curl clilap.org/dns/google.com/MX    # MXレコード
```

### 📋 WHOIS — `/whois`
ドメイン登録情報。

```bash
curl clilap.org/whois/github.com
```

### 🎨 カラー変換 — `/color`
カラーコードを変換・確認。

```bash
curl clilap.org/color/ff6b6b         # hex → RGB, HSL + ターミナルスウォッチ
curl clilap.org/color/255,107,107    # RGB入力
```

### 🔲 QRコード — `/qr`
ターミナルでQRコードを生成。

```bash
curl clilap.org/qr/https://example.com
curl clilap.org/qr/Hello+World
```

### 🦜 Parrot — `/parrot`
カラフルなオウムのアニメーション。

```bash
curl clilap.org/parrot
```

### 🔐 パスワード生成 — `/password`
暗号学的に安全なランダムパスワード・パスフレーズを生成します。

```bash
curl clilap.org/password              # 20文字パスワード
curl clilap.org/password/32           # 32文字
curl clilap.org/password?no-symbols   # 記号なし
curl clilap.org/password/phrase       # パスフレーズ
curl clilap.org/password/phrase/5     # 5ワード
```

### 📐 単位変換 — `/unit`
長さ・重さ・時間・データ・速度・温度の単位を変換します。

```bash
curl clilap.org/unit/100km/mi         # 距離
curl clilap.org/unit/1024MB/GiB       # データサイズ
curl clilap.org/unit/100C/F           # 温度
curl clilap.org/unit/3600s/h          # 時間
```

### 💱 為替レート — `/rate`
法定通貨の為替レートと暗号資産の価格をリアルタイムで取得します。

```bash
curl clilap.org/rate/USD              # USDのレート一覧
curl clilap.org/rate/USD/JPY          # USD → JPY
curl clilap.org/rate/USD/JPY,EUR,GBP  # 複数通貨
curl clilap.org/rate/BTC              # Bitcoin価格
curl clilap.org/rate/ETH/USD          # ETH → USD
```

### 🕐 世界時計 — `/time`
世界中の都市の現在時刻を表示します。

```bash
curl clilap.org/time                  # 主要都市一覧
curl clilap.org/time/Tokyo
curl clilap.org/time/New+York
curl clilap.org/time/Tokyo/London     # 2都市を比較
```

### 🔒 SSL証明書確認 — `/ssl`
ドメインのSSL証明書の詳細を取得します。有効期限・SANsを確認。

```bash
curl clilap.org/ssl/github.com
curl clilap.org/ssl/lapius7.com
```

### 🛡 セキュリティヘッダー — `/sec`
HTTPセキュリティヘッダーを確認してグレード（A+〜F）を表示します。

```bash
curl clilap.org/sec/github.com
curl clilap.org/sec/lapius7.com
```

### 🗺 DNSマップ — `/dnsmap`
4つのDNSリゾルバー（Cloudflare/Google/Quad9/OpenDNS）で同時にAレコードを照会します。

```bash
curl clilap.org/dnsmap/github.com
```

### 🌐 DNS全レコード — `/dns/{domain}/all`
全DNS レコードタイプを一括取得します。

```bash
curl clilap.org/dns/github.com/all
curl clilap.org/dns/lapius7.com/all
```

### 🔌 ポートチェック — `/portcheck`
外部ホストの指定ポートが開いているか確認します。

```bash
curl clilap.org/portcheck/github.com/443
curl clilap.org/portcheck/example.com/22
```

### 🔗 リダイレクトチェーン — `/redirect`
URLのリダイレクトチェーンを全て追跡して表示します。

```bash
curl clilap.org/redirect/https://bit.ly/...
curl clilap.org/redirect/https://t.co/...
```

### 📦 パッケージ情報 — `/package`
npmとPyPIのパッケージ情報を取得します。

```bash
curl clilap.org/package/npm/express
curl clilap.org/package/npm/@types/node
curl clilap.org/package/pypi/requests
```

### 🎨 ASCIIアート — `/ascii`
figletを使ってテキストをASCIIアートに変換します。

```bash
curl clilap.org/ascii/Hello
curl "clilap.org/ascii/Hi?font=slant"
```

### 🔢 進数変換 — `/base`
2進数・8進数・10進数・16進数を相互変換します。

```bash
curl clilap.org/base/10/255           # 10進 → 全進数
curl clilap.org/base/16/ff            # 16進 → 全進数
curl clilap.org/base/10/2/255         # 10進 → 2進
```

### 🔗 URLエンコード — `/urlencode` `/urldecode`

```bash
curl clilap.org/urlencode/hello+world
curl clilap.org/urldecode/hello%20world
echo "hello world" | curl -d @- clilap.org/urlencode
```

### 📅 カレンダー — `/cal`
ターミナルにカレンダーを表示します。今日の日付はハイライト表示。

```bash
curl clilap.org/cal                   # 今年のカレンダー
curl clilap.org/cal/2026              # 指定年
curl clilap.org/cal/2026/6            # 指定月
```

### ⏰ cron式パーサー — `/cron`
cron式を人間が読める説明文に変換します。

```bash
curl clilap.org/cron/0_9_%2A_%2A_1-5  # 平日9時 (スペースは_)
curl clilap.org/cron/@daily
curl clilap.org/cron/@weekly
```

### 🔑 TOTP生成 — `/totp`
Base32シークレットからTOTPを生成します。

```bash
curl clilap.org/totp/JBSWY3DPEHPK3PXP
```

> ⚠ 実際の認証コードをHTTP経由で送信しないでください（テスト用のみ）。

### 🎲 モックデータ生成 — `/mock`
テスト用のダミーデータ（JSONユーザー / Lorem）を生成します。

```bash
curl clilap.org/mock/json             # 偽ユーザー1件
curl clilap.org/mock/json/10          # 10件
curl clilap.org/mock/lorem            # Loremテキスト
curl clilap.org/mock/lorem/3          # 3段落
```

### 🚫 .gitignore生成 — `/gitignore`
GitHubのgitignoreテンプレートを取得します。複数言語を組み合わせ可能。

```bash
curl clilap.org/gitignore/node
curl clilap.org/gitignore/python
curl clilap.org/gitignore/node,python,macos,vscode
```

### 📜 ライセンステキスト — `/license`
オープンソースライセンスのテキストを取得します。

```bash
curl clilap.org/license/mit
curl "clilap.org/license/mit?holder=Lapius7"
curl clilap.org/license/apache
curl clilap.org/license/gpl-3
```

対応: `mit` `apache` `gpl-3` `gpl-2` `lgpl` `mpl` `isc` `bsd-2` `bsd-3` `unlicense` `agpl` `cc0`

### {} JSONフォーマッター — `/json`
JSONをフォーマット・バリデートします。POSTでJSONを送信してください。

```bash
echo '{"a":1}' | curl -d @- clilap.org/json
curl -d @data.json clilap.org/json
curl -d @data.json "clilap.org/json?compact"
```

### 📝 差分表示 — `/diff`
2つのファイルの差分をカラーで表示します。

```bash
curl -F "a=@old.txt" -F "b=@new.txt" clilap.org/diff
```

### 📄 Markdownレンダリング — `/md`
MarkdownをANSI付きのターミナル向けテキストに変換します。

```bash
cat README.md | curl -d @- clilap.org/md
curl -d @README.md clilap.org/md
```

### 🔡 Unicodeツール — `/unicode`
文字情報・テキスト検査・名前検索・ファンシーテキスト変換。

```bash
curl clilap.org/unicode/A                     # 文字情報
curl clilap.org/unicode/あ
echo "Hello, 世界" | curl -d @- clilap.org/unicode/inspect
curl clilap.org/unicode/search/star           # 名前で検索
curl clilap.org/unicode/fancy/bold/Hello      # ファンシーテキスト
curl clilap.org/unicode/fancy                 # スタイル一覧
```

ファンシースタイル: `bold` `italic` `bolditalic` `script` `gothic` `doublestruck` `monospace` `circled` `bubble` ...

---

## 共通オプション

| オプション | 効果 |
|-----------|------|
| `?ja`     | 日本語表示 |
| `?en`     | 英語表示 |

---

## データソース

- 天気: [Open-Meteo](https://open-meteo.com/)（無料・APIキー不要）
- ジオコーディング: [Nominatim](https://nominatim.org/) / [ip-api.com](https://ip-api.com/)
- チートシート: [tldr-pages](https://github.com/tldr-pages/tldr)（CC BY 4.0）
- IP位置情報: [geoip-lite](https://github.com/geoip-lite/node-geoip-lite)
- GitHub情報: [GitHub REST API](https://docs.github.com/en/rest)
- QRコード: [libqrencode](https://github.com/fukuchi/libqrencode)
- Parrot: [terminal-parrot](https://github.com/jmhobbs/terminal-parrot)
- 為替レート: [Frankfurter (ECB)](https://frankfurter.app/)
- 暗号資産: [CoinGecko](https://www.coingecko.com/)
- npmパッケージ: [npmjs.org](https://www.npmjs.com/)
- PyPIパッケージ: [pypi.org](https://pypi.org/)
- .gitignoreテンプレート: [github/gitignore](https://github.com/github/gitignore)
- ライセンステキスト: [GitHub Licenses API](https://docs.github.com/en/rest/licenses)

---

## 作者

**Lapius7** — [github.com/Lapius7](https://github.com/Lapius7)

## ライセンス

MIT
