```
      _ _ _ _ _ _
    /    I  ( )  I _ _ _ _
   I  (  I   I   I  /  _ _  \
    \ _ _ I   I   I  \(_ _  /
                     |_|
```

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

---

## 作者

**Lapius7** — [github.com/Lapius7](https://github.com/Lapius7)

## ライセンス

MIT
