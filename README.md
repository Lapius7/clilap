<div align="center">

<p align="center"><b>English</b> | <a href="README.ja.md">日本語</a></p>

<h1 align="center">Clilap</h1>

<h3 align="center">Developer tools you can use with just curl.</h3>

<p align="center">No-install developer tools reached through <code>curl clilap.org</code>. Weather, cheat sheets, GitHub info, DNS lookup, hashing and more, straight from your terminal.</p>

<p align="center">
  <a href="https://github.com/Lapius7/clilap.org/releases"><img alt="Release" src="https://img.shields.io/github/v/release/Lapius7/clilap.org?label=release&style=flat-square&color=e8833a&logo=github"></a>
  <a href="https://www.npmjs.com/package/@lapius/clilap"><img alt="npm" src="https://img.shields.io/npm/v/@lapius/clilap?style=flat-square&color=cb3837&logo=npm"></a>
  <a href="LICENSE"><img alt="License" src="https://img.shields.io/github/license/Lapius7/clilap.org?style=flat-square&color=97ca00"></a>
  <a href="https://clilap.org"><img alt="curl clilap.org" src="https://img.shields.io/badge/try%20it-curl%20clilap.org-4ec9b0?style=flat-square"></a>
  <a href="https://github.com/Lapius7/clilap.org/stargazers"><img alt="Stars" src="https://img.shields.io/github/stars/Lapius7/clilap.org?style=flat-square&color=e3b341&logo=github"></a>
  <a href="https://github.com/Lapius7/clilap.org/commits/master"><img alt="Last commit" src="https://img.shields.io/github/last-commit/Lapius7/clilap.org?label=last%20commit&style=flat-square&color=2f81f7"></a>
</p>

<p align="center"><a href="#install">Install</a> · <a href="#services">Services</a> · <a href="#common-options">Common Options</a> · <a href="#data-sources">Data Sources</a></p>

</div>

---

## Install

### pnpm (recommended)

> This package assumes **pnpm**. Installing it with both npm and pnpm creates duplicate commands, so use `pnpm add -g` only.

```bash
pnpm add -g @lapius/clilap
```

This installs the `clilap` command (Node.js 18+). Every service below works the same way with either `curl` or `clilap`: the path segments after `clilap.org/` become the arguments.

| curl | clilap |
|---|---|
| `curl clilap.org` | `clilap` |
| `curl clilap.org/mock/json` | `clilap mock json` |
| `curl clilap.org/weather/Tokyo` | `clilap weather Tokyo` |
| `curl "clilap.org/cheat/tar?en"` | `clilap cheat tar --en` |
| `curl "clilap.org/json?compact" -d @data.json` | `clilap json '?compact' -d @data.json` |
| `echo hello \| curl -d @- clilap.org/hash/sha256` | `echo hello \| clilap hash sha256` |
| `curl -F "a=@old.txt" -F "b=@new.txt" clilap.org/diff` | `clilap diff old.txt new.txt` |

Options are listed below.

| Option | Effect |
|---|---|
| `-d, --data <text\|@file\|@->` | Send a request body (`@-` = stdin; piped stdin is sent automatically) |
| `--en` / `--ja` | Output language (same as `?en` / `?ja`) |
| `?<query>` | Add a query parameter, e.g. `'?compact'` |
| `--no-color` | Disable colors (automatic when stdout is not a terminal) |
| `-h, --help` / `-v, --version` | Help / version |

Update with the same `pnpm add -g @lapius/clilap`. The server can be changed with the `CLILAP_URL` environment variable. The exit code is 1 when the server returns an error.

### No install

Just use `curl` — all examples below are written with `curl`.

[日本語 README](README.ja.md)

## Services

> [!NOTE]
> Service behavior below is carried over from the previous README. Each service was not re-run against clilap.org for this rewrite (unverified).

<details>
<summary><b>Weather</b> — <code>/weather</code></summary>

Real-time weather forecast using [Open-Meteo](https://open-meteo.com/) and [Nominatim](https://nominatim.org/).

```bash
curl clilap.org/weather              # Auto-detect location from IP
curl clilap.org/weather/Tokyo        # City name
curl clilap.org/weather/東京都/新宿区  # Prefecture / ward
curl clilap.org/weather/Tokyo?en     # English output
```

</details>

<details>
<summary><b>Cheat Sheets</b> — <code>/cheat</code></summary>

Command reference powered by [tldr-pages](https://github.com/tldr-pages/tldr).

```bash
curl clilap.org/cheat/git            # Git cheat sheet
curl clilap.org/cheat/docker         # Docker cheat sheet
curl clilap.org/cheat/:list          # List all available commands
curl clilap.org/cheat/git?ja         # Japanese (default)
curl clilap.org/cheat/git?en         # English
```

</details>

<details>
<summary><b>GitHub</b> — <code>/github</code></summary>

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

</details>

<details>
<summary><b>IP Info</b> — <code>/ipinfo</code></summary>

IP address geolocation and metadata.

```bash
curl clilap.org/ipinfo               # Your current IP
curl clilap.org/ipinfo/8.8.8.8       # Specific IP lookup
```

</details>

<details>
<summary><b>Request Headers</b> — <code>/headers</code></summary>

Inspect the HTTP headers your client is sending.

```bash
curl clilap.org/headers
```

</details>

<details>
<summary><b>UUID Generator</b> — <code>/uuid</code></summary>

Generate random UUIDs (v4).

```bash
curl clilap.org/uuid                 # One UUID
curl clilap.org/uuid/5               # Five UUIDs
```

</details>

<details>
<summary><b>Base64</b> — <code>/b64</code></summary>

Encode and decode Base64.

```bash
curl clilap.org/b64/encode/hello
curl clilap.org/b64/decode/aGVsbG8=
echo "hello world" | curl -d @- clilap.org/b64/encode
```

</details>

<details>
<summary><b>Hash</b> — <code>/hash</code></summary>

Compute cryptographic hashes.

Supported algorithms: `md5`, `sha1`, `sha256`, `sha512`, `sha3_256`, `sha3_512`

```bash
curl clilap.org/hash/sha256/hello
echo "hello" | curl -d @- clilap.org/hash/sha256
```

</details>

<details>
<summary><b>Epoch</b> — <code>/epoch</code></summary>

Convert between Unix timestamps and human-readable dates.

```bash
curl clilap.org/epoch                # Current time (UTC + local)
curl clilap.org/epoch/1700000000     # Unix timestamp → date
curl clilap.org/epoch/2024-01-01     # Date → Unix timestamp
curl clilap.org/epoch/2024-01-01T12:00:00
```

</details>

<details>
<summary><b>DNS Lookup</b> — <code>/dns</code></summary>

Query DNS records for any domain.

Supported types: `A`, `AAAA`, `MX`, `NS`, `TXT`, `CNAME`, `SOA`, `PTR`

```bash
curl clilap.org/dns/google.com       # A record (default)
curl clilap.org/dns/google.com/MX    # MX records
curl clilap.org/dns/github.com/NS
```

</details>

<details>
<summary><b>WHOIS</b> — <code>/whois</code></summary>

Domain registration info.

```bash
curl clilap.org/whois/github.com
```

</details>

<details>
<summary><b>Color</b> — <code>/color</code></summary>

Convert and inspect colors.

```bash
curl clilap.org/color/ff6b6b         # Hex → RGB, HSL + terminal swatch
curl clilap.org/color/255,107,107    # RGB input
```

</details>

<details>
<summary><b>QR Code</b> — <code>/qr</code></summary>

Generate QR codes in the terminal.

```bash
curl clilap.org/qr/https://example.com
curl clilap.org/qr/Hello+World
```

</details>

<details>
<summary><b>Parrot</b> — <code>/parrot</code></summary>

A colorful party parrot animation.

```bash
curl clilap.org/parrot
```

</details>

<details>
<summary><b>Password Generator</b> — <code>/password</code></summary>

Cryptographically secure password or passphrase generation.

```bash
curl clilap.org/password              # 20-char password
curl clilap.org/password/32           # 32-char password
curl clilap.org/password?no-symbols   # letters + digits only
curl clilap.org/password/phrase       # passphrase
curl clilap.org/password/phrase/5     # 5-word passphrase
```

</details>

<details>
<summary><b>Unit Converter</b> — <code>/unit</code></summary>

Convert between units of length, weight, time, data, speed, and temperature.

```bash
curl clilap.org/unit/100km/mi         # distance
curl clilap.org/unit/1024MB/GiB       # data size
curl clilap.org/unit/100C/F           # temperature
curl clilap.org/unit/3600s/h          # time
```

</details>

<details>
<summary><b>Exchange Rate</b> — <code>/rate</code></summary>

Real-time forex rates (ECB via Frankfurter) and crypto prices (CoinGecko).

```bash
curl clilap.org/rate/USD              # all rates for USD
curl clilap.org/rate/USD/JPY          # USD → JPY
curl clilap.org/rate/USD/JPY,EUR,GBP  # multiple targets
curl clilap.org/rate/BTC              # Bitcoin price
curl clilap.org/rate/ETH/USD          # ETH → USD
```

</details>

<details>
<summary><b>World Time</b> — <code>/time</code></summary>

Current time in cities around the world.

```bash
curl clilap.org/time                  # major city clocks
curl clilap.org/time/Tokyo
curl clilap.org/time/New+York
curl clilap.org/time/Tokyo/London     # compare two cities
curl clilap.org/time/America/Chicago  # IANA timezone name
```

</details>

<details>
<summary><b>SSL Certificate</b> — <code>/ssl</code></summary>

SSL/TLS certificate details including expiry and SANs.

```bash
curl clilap.org/ssl/github.com
curl clilap.org/ssl/lapius7.com
```

</details>

<details>
<summary><b>Security Headers</b> — <code>/sec</code></summary>

HTTP security header audit with grade (A+ to F).

```bash
curl clilap.org/sec/github.com
curl clilap.org/sec/lapius7.com
```

</details>

<details>
<summary><b>DNS Map</b> — <code>/dnsmap</code></summary>

Query a domain across 4 resolvers (Cloudflare, Google, Quad9, OpenDNS) simultaneously.

```bash
curl clilap.org/dnsmap/github.com
```

</details>

<details>
<summary><b>DNS All Records</b> — <code>/dns/{domain}/all</code></summary>

Export all DNS record types (A/AAAA/MX/NS/TXT/CNAME/SOA/CAA/SRV) at once.

```bash
curl clilap.org/dns/github.com/all
curl clilap.org/dns/lapius7.com/all
```

</details>

<details>
<summary><b>Port Check</b> — <code>/portcheck</code></summary>

Check if a port is open on a remote host.

```bash
curl clilap.org/portcheck/github.com/443
curl clilap.org/portcheck/example.com/22
```

</details>

<details>
<summary><b>Redirect Chain</b> — <code>/redirect</code></summary>

Trace all HTTP redirects for a URL.

```bash
curl clilap.org/redirect/https://bit.ly/...
curl clilap.org/redirect/https://t.co/...
```

</details>

<details>
<summary><b>Package Info</b> — <code>/package</code></summary>

npm and PyPI package metadata.

```bash
curl clilap.org/package/npm/express
curl clilap.org/package/npm/@types/node
curl clilap.org/package/pypi/requests
```

</details>

<details>
<summary><b>ASCII Art</b> — <code>/ascii</code></summary>

Generate ASCII art via figlet.

```bash
curl clilap.org/ascii/Hello
curl "clilap.org/ascii/Hi?font=slant"
```

</details>

<details>
<summary><b>Base Converter</b> — <code>/base</code></summary>

Convert between any base from 2 to 36.

```bash
curl clilap.org/base/10/255           # decimal → common bases (2,8,16,36)
curl clilap.org/base/16/ff            # hex → common bases
curl clilap.org/base/10/2/255         # decimal → binary
curl clilap.org/base/10/255?all       # decimal → all bases 2-36
```

</details>

<details>
<summary><b>URL Encode/Decode</b> — <code>/urlencode</code> <code>/urldecode</code></summary>

```bash
curl clilap.org/urlencode/hello+world
curl clilap.org/urldecode/hello%20world
echo "hello world" | curl -d @- clilap.org/urlencode
```

</details>

<details>
<summary><b>Calendar</b> — <code>/cal</code></summary>

Terminal calendar with today highlighted.

```bash
curl clilap.org/cal                   # current year
curl clilap.org/cal/2026              # full year
curl clilap.org/cal/2026/6            # specific month
```

</details>

<details>
<summary><b>⏰ Cron Parser</b> — <code>/cron</code></summary>

Translate cron expressions into human-readable descriptions.

```bash
curl clilap.org/cron/0_9_%2A_%2A_1-5  # weekdays at 9:00
curl clilap.org/cron/@daily
curl clilap.org/cron/@weekly
```

</details>

<details>
<summary><b>TOTP Generator</b> — <code>/totp</code></summary>

Generate TOTP one-time passwords from a Base32 secret.

```bash
curl clilap.org/totp/JBSWY3DPEHPK3PXP
```

> [!WARNING]
> Do not use with real secrets over HTTP — for testing only.

</details>

<details>
<summary><b>Mock Data</b> — <code>/mock</code></summary>

Generate fake JSON user data or Lorem Ipsum text.

```bash
curl clilap.org/mock/json             # 1 fake user
curl clilap.org/mock/json/10          # 10 fake users
curl clilap.org/mock/lorem            # 1 Lorem paragraph
curl clilap.org/mock/lorem/3          # 3 paragraphs
```

</details>

<details>
<summary><b>.gitignore Generator</b> — <code>/gitignore</code></summary>

Fetch GitHub gitignore templates. Combine multiple languages.

```bash
curl clilap.org/gitignore/node
curl clilap.org/gitignore/python
curl clilap.org/gitignore/node,python,macos,vscode
```

</details>

<details>
<summary><b>License Text</b> — <code>/license</code></summary>

Open source license templates with auto-filled year and holder.

```bash
curl clilap.org/license/mit
curl "clilap.org/license/mit?holder=Lapius7"
curl clilap.org/license/apache
curl clilap.org/license/gpl-3
```

Supported: `mit` `apache` `gpl-3` `gpl-2` `lgpl` `mpl` `isc` `bsd-2` `bsd-3` `unlicense` `agpl` `cc0`

</details>

<details>
<summary><b>{} JSON Formatter</b> — <code>/json</code></summary>

Format and validate JSON. POST body.

```bash
echo '{"a":1}' | curl -d @- clilap.org/json
curl -d @data.json clilap.org/json
curl -d @data.json "clilap.org/json?compact"
```

</details>

<details>
<summary><b>Diff</b> — <code>/diff</code></summary>

Colored unified diff of two files.

```bash
curl -F "a=@old.txt" -F "b=@new.txt" clilap.org/diff
```

</details>

<details>
<summary><b>Markdown Renderer</b> — <code>/md</code></summary>

Render Markdown as ANSI-colored terminal output.

```bash
cat README.md | curl -d @- clilap.org/md
curl -d @README.md clilap.org/md
```

</details>

<details>
<summary><b>Unicode Tools</b> — <code>/unicode</code></summary>

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

</details>

<details>
<summary><b>Regex Tester</b> — <code>/regex</code></summary>

Test regular expressions using Python's `re` engine. Shows match count, positions, and capture groups.

```bash
curl clilap.org/regex/\d+                                      # pattern info
echo "abc 123 def 456" | curl -d @- clilap.org/regex/\\d+     # match against text
echo "Hello World" | curl -d @- "clilap.org/regex/hello?flags=i"
echo "2024-01-15" | curl -d @- "clilap.org/regex/(\d{4})-(\d{2})-(\d{2})"
```

| Flag | Effect |
|------|--------|
| `?flags=i` | Case-insensitive |
| `?flags=m` | Multiline (`^`/`$` match line boundaries) |
| `?flags=s` | Dotall (`.` matches newlines) |
| `?flags=x` | Verbose (whitespace ignored) |
| `?flags=im` | Combine flags |

</details>

<details>
<summary><b>Dependency Visualizer</b> — <code>/dep</code></summary>

Upload a `package.json`, get a dependency tree at a shareable URL. Detects circular dependencies, ranks heaviest packages, and audits licenses.

```bash
curl -F "file=@package.json" clilap.org/dep
cat package.json | curl --data-binary @- clilap.org/dep

curl dep.clilap.org/ab12cd            # tree view
curl dep.clilap.org/ab12cd/cycles     # circular dependency detection
curl dep.clilap.org/ab12cd/heavy      # heaviest packages ranking
curl dep.clilap.org/ab12cd/licenses   # license audit
```

Also viewable in a browser: `https://dep.clilap.org/ab12cd`. Stored indefinitely.

</details>

<details>
<summary><b>Realtime Log Sharing</b> — <code>/log</code></summary>

Stream any command output or log file to a shareable URL. ANSI colors are preserved. Two-step flow — get an upload token first, then stream to it (works even for processes that never exit, like long-running servers):

```bash
RES=$(curl -s clilap.org/log/new)
UPLOAD=$(echo "$RES" | grep ^upload: | awk '{print $2}')
tail -f app.log | curl -T - "$UPLOAD"
npm run dev 2>&1 | curl -T - "$UPLOAD"
```

```bash
curl log.clilap.org/abc123                  # plain text
curl "log.clilap.org/abc123?grep=ERROR"     # filter by regex
```

Open `https://log.clilap.org/abc123` in a browser for a realtime live-updating view (WebSocket-backed, ANSI rendered as color).

</details>

<details>
<summary><b>CIDR Calculator</b> — <code>/cidr</code></summary>

```bash
curl clilap.org/cidr/192.168.1.0/24
curl clilap.org/cidr/10.0.0.0/8
curl clilap.org/cidr/2001:db8::/32
```

</details>

<details>
<summary><b>ASN Lookup</b> — <code>/asn</code></summary>

```bash
curl clilap.org/asn/8.8.8.8
curl clilap.org/asn/1.1.1.1
```

Uses Team Cymru's DNS-based lookup. IPv4 only.

</details>

<details>
<summary><b>robots.txt Inspector</b> — <code>/robots</code></summary>

```bash
curl clilap.org/robots/github.com
```

</details>

<details>
<summary><b>User-Agent Parser</b> — <code>/useragent</code></summary>

```bash
curl clilap.org/useragent                          # parse your own UA
curl -A "Mozilla/5.0 ..." clilap.org/useragent     # parse a given UA
```

</details>

<details>
<summary><b>JWT Decoder</b> — <code>/jwt</code></summary>

```bash
curl clilap.org/jwt/{token}
echo "{token}" | curl -d @- clilap.org/jwt
```

> [!WARNING]
> Signature is not verified. Don't trust untrusted token contents blindly.

</details>

<details>
<summary><b>Morse Code</b> — <code>/morse</code></summary>

```bash
curl clilap.org/morse/encode/SOS
curl clilap.org/morse/decode/..._---_...
echo "Hello" | curl -d @- clilap.org/morse/encode
```

Use `_` to separate letters and `/` to separate words when decoding.

</details>

<details>
<summary><b>Format Converter</b> — <code>/convert</code></summary>

```bash
curl --data-binary @data.json clilap.org/convert/json/yaml
curl --data-binary @data.yaml clilap.org/convert/yaml/json
curl --data-binary @data.csv  clilap.org/convert/csv/json
curl --data-binary @data.toml clilap.org/convert/toml/json
curl --data-binary @data.ini  clilap.org/convert/ini/json
```

Supported formats: `json` `yaml` `toml` `ini` `csv`. Use `--data-binary` (not `-d`) to preserve newlines/indentation. YAML support is a minimal subset (nesting, lists, scalars only).

</details>

<details>
<summary><b>Moon Phase</b> — <code>/moon</code></summary>

```bash
curl clilap.org/moon                # today's phase
curl clilap.org/moon/2026-01-01     # phase on a given date
```

</details>

<details>
<summary><b>Sunrise/Sunset</b> — <code>/sunrise</code></summary>

```bash
curl clilap.org/sunrise/Tokyo
curl clilap.org/sunrise             # auto-detect from IP
```

</details>

## Common Options

| Option | Effect          |
|--------|-----------------|
| `?ja`  | Japanese output |
| `?en`  | English output  |

With the `clilap` client, use `--ja` / `--en`.

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

## Author

**Lapius7** — [github.com/Lapius7](https://github.com/Lapius7)

## License

MIT
