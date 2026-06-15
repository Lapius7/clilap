# clilap

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

---

## Common Options

| Option     | Effect              |
|------------|---------------------|
| `?nocolor` | Disable ANSI colors |
| `?ja`      | Japanese output     |
| `?en`      | English output      |

---

## Data Sources

- Weather: [Open-Meteo](https://open-meteo.com/) (free, no API key)
- Geocoding: [Nominatim](https://nominatim.org/) / [ip-api.com](https://ip-api.com/)
- Cheat sheets: [tldr-pages](https://github.com/tldr-pages/tldr) (CC BY 4.0)
- IP geolocation: [geoip-lite](https://github.com/geoip-lite/node-geoip-lite)
- GitHub info: [GitHub REST API](https://docs.github.com/en/rest)
- QR codes: [libqrencode](https://github.com/fukuchi/libqrencode) via [qrenco.de](https://github.com/chubin/qrenco.de)
- Parrot animation: [terminal-parrot](https://github.com/jmhobbs/terminal-parrot)

---

## Author

**Lapius7** — [github.com/Lapius7](https://github.com/Lapius7)

## License

MIT
