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
[![curl](https://img.shields.io/badge/try%20it-curl%20clilap.org-4ec9b0?style=flat-square)](https://clilap.org)

No-install developer tools accessible via `curl`. Weather forecasts, cheat sheets, GitHub info, DNS lookup, hashing, and more — all from your terminal.

```
curl clilap.org
```

[日本語 README](README.ja.md)

---

## Services

### 🌤 Weather — `/weather`
Real-time weather forecast using [Open-Meteo](https://open-meteo.com/) and [Nominatim](https://nominatim.org/).

```bash
curl clilap.org/weather              # Auto-detect location from IP
curl clilap.org/weather/Tokyo        # City name
curl clilap.org/weather/東京都/新宿区  # Prefecture / ward
curl clilap.org/weather/Tokyo?en     # English output
```

### 📖 Cheat Sheets — `/cheat`
Command reference powered by [tldr-pages](https://github.com/tldr-pages/tldr).

```bash
curl clilap.org/cheat/git            # Git cheat sheet
curl clilap.org/cheat/docker         # Docker cheat sheet
curl clilap.org/cheat/:list          # List all available commands
curl clilap.org/cheat/git?ja         # Japanese (default)
curl clilap.org/cheat/git?en         # English
```

### 🐙 GitHub — `/github`
Explore GitHub repos and users from the terminal.

```bash
curl clilap.org/github/torvalds              # User profile + repo list
curl clilap.org/github/curl/curl             # Repo overview (stars/forks/language/license)
curl clilap.org/github/curl/curl/readme      # README content
curl clilap.org/github/curl/curl/readme/ja   # Japanese README (falls back to default)
curl clilap.org/github/curl/curl/releases    # Release history
curl clilap.org/github/curl/curl/commits     # Recent commits
curl clilap.org/github/curl/curl/issues      # Open issues
curl clilap.org/github/curl/curl/prs         # Open pull requests
curl clilap.org/github/curl/curl/stars       # Star count only
```

### 🌐 IP Info — `/ipinfo`
IP address geolocation and metadata.

```bash
curl clilap.org/ipinfo               # Your current IP
curl clilap.org/ipinfo/8.8.8.8       # Specific IP lookup
```

### 🔍 Request Headers — `/headers`
Inspect the HTTP headers your client is sending.

```bash
curl clilap.org/headers
```

### 🔑 UUID Generator — `/uuid`
Generate random UUIDs (v4).

```bash
curl clilap.org/uuid                 # One UUID
curl clilap.org/uuid/5               # Five UUIDs
```

### 🔒 Base64 — `/b64`
Encode and decode Base64.

```bash
curl clilap.org/b64/encode/hello
curl clilap.org/b64/decode/aGVsbG8=
echo "hello world" | curl -d @- clilap.org/b64/encode
```

### #️⃣ Hash — `/hash`
Compute cryptographic hashes.

Supported algorithms: `md5`, `sha1`, `sha256`, `sha512`, `sha3_256`, `sha3_512`

```bash
curl clilap.org/hash/sha256/hello
echo "hello" | curl -d @- clilap.org/hash/sha256
```

### 🕐 Epoch — `/epoch`
Convert between Unix timestamps and human-readable dates.

```bash
curl clilap.org/epoch                # Current time (UTC + local)
curl clilap.org/epoch/1700000000     # Unix timestamp → date
curl clilap.org/epoch/2024-01-01     # Date → Unix timestamp
curl clilap.org/epoch/2024-01-01T12:00:00
```

### 🌍 DNS Lookup — `/dns`
Query DNS records for any domain.

Supported types: `A`, `AAAA`, `MX`, `NS`, `TXT`, `CNAME`, `SOA`, `PTR`

```bash
curl clilap.org/dns/google.com       # A record (default)
curl clilap.org/dns/google.com/MX    # MX records
curl clilap.org/dns/github.com/NS
```

### 📋 WHOIS — `/whois`
Domain registration info.

```bash
curl clilap.org/whois/github.com
```

### 🎨 Color — `/color`
Convert and inspect colors.

```bash
curl clilap.org/color/ff6b6b         # Hex → RGB, HSL + terminal swatch
curl clilap.org/color/255,107,107    # RGB input
```

### 🔲 QR Code — `/qr`
Generate QR codes in the terminal.

```bash
curl clilap.org/qr/https://example.com
curl clilap.org/qr/Hello+World
```

### 🦜 Parrot — `/parrot`
A colorful party parrot animation.

```bash
curl clilap.org/parrot
```

### 🔐 Password Generator — `/password`

Cryptographically secure password or passphrase generation.

```bash
curl clilap.org/password              # 20-char password
curl clilap.org/password/32           # 32-char password
curl clilap.org/password?no-symbols   # letters + digits only
curl clilap.org/password/phrase       # passphrase
curl clilap.org/password/phrase/5     # 5-word passphrase
```

### 📐 Unit Converter — `/unit`

Convert between units of length, weight, time, data, speed, and temperature.

```bash
curl clilap.org/unit/100km/mi         # distance
curl clilap.org/unit/1024MB/GiB       # data size
curl clilap.org/unit/100C/F           # temperature
curl clilap.org/unit/3600s/h          # time
```

### 💱 Exchange Rate — `/rate`

Real-time forex rates (ECB via Frankfurter) and crypto prices (CoinGecko).

```bash
curl clilap.org/rate/USD              # all rates for USD
curl clilap.org/rate/USD/JPY          # USD → JPY
curl clilap.org/rate/USD/JPY,EUR,GBP  # multiple targets
curl clilap.org/rate/BTC              # Bitcoin price
curl clilap.org/rate/ETH/USD          # ETH → USD
```

### 🕐 World Time — `/time`

Current time in cities around the world.

```bash
curl clilap.org/time                  # major city clocks
curl clilap.org/time/Tokyo
curl clilap.org/time/New+York
curl clilap.org/time/Tokyo/London     # compare two cities
curl clilap.org/time/America/Chicago  # IANA timezone name
```

### 🔒 SSL Certificate — `/ssl`

SSL/TLS certificate details including expiry and SANs.

```bash
curl clilap.org/ssl/github.com
curl clilap.org/ssl/lapius7.com
```

### 🛡 Security Headers — `/sec`

HTTP security header audit with grade (A+ to F).

```bash
curl clilap.org/sec/github.com
curl clilap.org/sec/lapius7.com
```

### 🗺 DNS Map — `/dnsmap`

Query a domain across 4 resolvers (Cloudflare, Google, Quad9, OpenDNS) simultaneously.

```bash
curl clilap.org/dnsmap/github.com
```

### 🌐 DNS All Records — `/dns/{domain}/all`

Export all DNS record types (A/AAAA/MX/NS/TXT/CNAME/SOA/CAA/SRV) at once.

```bash
curl clilap.org/dns/github.com/all
curl clilap.org/dns/lapius7.com/all
```

### 🔌 Port Check — `/portcheck`

Check if a port is open on a remote host.

```bash
curl clilap.org/portcheck/github.com/443
curl clilap.org/portcheck/example.com/22
```

### 🔗 Redirect Chain — `/redirect`

Trace all HTTP redirects for a URL.

```bash
curl clilap.org/redirect/https://bit.ly/...
curl clilap.org/redirect/https://t.co/...
```

### 📦 Package Info — `/package`

npm and PyPI package metadata.

```bash
curl clilap.org/package/npm/express
curl clilap.org/package/npm/@types/node
curl clilap.org/package/pypi/requests
```

### 🎨 ASCII Art — `/ascii`

Generate ASCII art via figlet.

```bash
curl clilap.org/ascii/Hello
curl "clilap.org/ascii/Hi?font=slant"
```

### 🔢 Base Converter — `/base`

Convert between binary, octal, decimal, and hexadecimal.

```bash
curl clilap.org/base/10/255           # decimal → all
curl clilap.org/base/16/ff            # hex → all
curl clilap.org/base/10/2/255         # decimal → binary
```

### 🔗 URL Encode/Decode — `/urlencode` `/urldecode`

```bash
curl clilap.org/urlencode/hello+world
curl clilap.org/urldecode/hello%20world
echo "hello world" | curl -d @- clilap.org/urlencode
```

### 📅 Calendar — `/cal`

Terminal calendar with today highlighted.

```bash
curl clilap.org/cal                   # current year
curl clilap.org/cal/2026              # full year
curl clilap.org/cal/2026/6            # specific month
```

### ⏰ Cron Parser — `/cron`

Translate cron expressions into human-readable descriptions.

```bash
curl clilap.org/cron/0_9_%2A_%2A_1-5  # weekdays at 9:00
curl clilap.org/cron/@daily
curl clilap.org/cron/@weekly
```

### 🔑 TOTP Generator — `/totp`

Generate TOTP one-time passwords from a Base32 secret.

```bash
curl clilap.org/totp/JBSWY3DPEHPK3PXP
```

> ⚠ Do not use with real secrets over HTTP — for testing only.

### 🎲 Mock Data — `/mock`

Generate fake JSON user data or Lorem Ipsum text.

```bash
curl clilap.org/mock/json             # 1 fake user
curl clilap.org/mock/json/10          # 10 fake users
curl clilap.org/mock/lorem            # 1 Lorem paragraph
curl clilap.org/mock/lorem/3          # 3 paragraphs
```

### 🚫 .gitignore Generator — `/gitignore`

Fetch GitHub gitignore templates. Combine multiple languages.

```bash
curl clilap.org/gitignore/node
curl clilap.org/gitignore/python
curl clilap.org/gitignore/node,python,macos,vscode
```

### 📜 License Text — `/license`

Open source license templates with auto-filled year and holder.

```bash
curl clilap.org/license/mit
curl "clilap.org/license/mit?holder=Lapius7"
curl clilap.org/license/apache
curl clilap.org/license/gpl-3
```

Supported: `mit` `apache` `gpl-3` `gpl-2` `lgpl` `mpl` `isc` `bsd-2` `bsd-3` `unlicense` `agpl` `cc0`

### {} JSON Formatter — `/json`

Format and validate JSON. POST body.

```bash
echo '{"a":1}' | curl -d @- clilap.org/json
curl -d @data.json clilap.org/json
curl -d @data.json "clilap.org/json?compact"
```

### 📝 Diff — `/diff`

Colored unified diff of two files.

```bash
curl -F "a=@old.txt" -F "b=@new.txt" clilap.org/diff
```

### 📄 Markdown Renderer — `/md`

Render Markdown as ANSI-colored terminal output.

```bash
cat README.md | curl -d @- clilap.org/md
curl -d @README.md clilap.org/md
```

### 🔡 Unicode Tools — `/unicode`

Character info, text inspection, name search, and fancy text styles.

```bash
curl clilap.org/unicode/A                     # char info
curl clilap.org/unicode/あ
echo "Hello, 世界" | curl -d @- clilap.org/unicode/inspect
curl clilap.org/unicode/search/star           # search by name
curl clilap.org/unicode/fancy/bold/Hello      # fancy text
curl clilap.org/unicode/fancy                 # list all styles
```

Fancy styles: `bold` `italic` `bolditalic` `script` `boldscript` `gothic` `doublestruck` `sans` `monospace` `circled` `bubble` ...

---

## Common Options

| Option | Effect          |
|--------|-----------------|
| `?ja`  | Japanese output |
| `?en`  | English output  |

---

## Data Sources

- Weather: [Open-Meteo](https://open-meteo.com/) (free, no API key)
- Geocoding: [Nominatim](https://nominatim.org/) / [ip-api.com](https://ip-api.com/)
- Cheat sheets: [tldr-pages](https://github.com/tldr-pages/tldr) (CC BY 4.0)
- IP geolocation: [geoip-lite](https://github.com/geoip-lite/node-geoip-lite)
- GitHub info: [GitHub REST API](https://docs.github.com/en/rest)
- QR codes: [libqrencode](https://github.com/fukuchi/libqrencode)
- Parrot animation: [terminal-parrot](https://github.com/jmhobbs/terminal-parrot)
- Exchange rates: [Frankfurter (ECB)](https://frankfurter.app/)
- Crypto prices: [CoinGecko](https://www.coingecko.com/)
- npm packages: [npmjs.org](https://www.npmjs.com/)
- PyPI packages: [pypi.org](https://pypi.org/)
- .gitignore templates: [github/gitignore](https://github.com/github/gitignore)
- License text: [GitHub Licenses API](https://docs.github.com/en/rest/licenses)

---

## Author

**Lapius7** — [github.com/Lapius7](https://github.com/Lapius7)

## License

MIT
