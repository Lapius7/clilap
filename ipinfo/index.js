#!/usr/bin/env node
'use strict';

const http = require('http');
const dns  = require('dns');
const { URL } = require('url');

const PORT = 3208;

const R   = '\x1b[0m';
const B   = '\x1b[1m';
const BC  = '\x1b[1;36m';
const C   = '\x1b[36m';
const DC  = '\x1b[2;36m';
const D   = '\x1b[2m';

function getClientIp(req) {
  return (
    req.headers['x-real-ip'] ||
    (req.headers['x-forwarded-for'] || '').split(',')[0].trim() ||
    req.socket.remoteAddress ||
    ''
  ).replace(/^::ffff:/, '');
}

function isPrivate(ip) {
  return /^(127\.|10\.|172\.(1[6-9]|2\d|3[01])\.|192\.168\.|::1$|localhost)/.test(ip);
}

function lnk(url, inner) {
  return `\x1b]8;;${url}\x1b\\${inner}\x1b]8;;\x1b\\`;
}

function lookupGeo(ip) {
  return new Promise((resolve) => {
    if (!ip || isPrivate(ip)) {
      return resolve({ ip, city:'', region:'', country:'', countryCode:'',
                       postal:'', timezone:'', org:'', as:'', ll:'' });
    }
    const url = `http://ip-api.com/json/${encodeURIComponent(ip)}` +
      `?fields=query,status,country,countryCode,regionName,city,zip,lat,lon,timezone,isp,org,as`;
    http.get(url, (res) => {
      let buf = '';
      res.on('data', c => buf += c);
      res.on('end', () => {
        try {
          const g = JSON.parse(buf);
          resolve({
            ip:          g.query       || ip,
            city:        g.city        || '',
            region:      g.regionName  || '',
            country:     g.country     || '',
            countryCode: g.countryCode || '',
            postal:      g.zip         || '',
            timezone:    g.timezone    || '',
            org:         g.org         || g.isp || '',
            as:          g.as          || '',
            ll:          (g.lat && g.lon) ? `${g.lat},${g.lon}` : '',
          });
        } catch (_) {
          resolve({ ip, city:'', region:'', country:'', countryCode:'',
                    postal:'', timezone:'', org:'', as:'', ll:'' });
        }
      });
      res.on('error', () => resolve({ ip, city:'', region:'', country:'', countryCode:'',
                                       postal:'', timezone:'', org:'', as:'', ll:'' }));
    }).on('error', () => resolve({ ip, city:'', region:'', country:'', countryCode:'',
                                    postal:'', timezone:'', org:'', as:'', ll:'' }));
  });
}

function lookupHostname(ip) {
  return new Promise((resolve) => {
    if (!ip || isPrivate(ip)) return resolve('');
    dns.reverse(ip, (err, hosts) => resolve(err ? '' : (hosts[0] || '')));
  });
}

function isBrowser(ua) {
  return /mozilla|webkit|trident|opera/i.test(ua);
}

const A2H = {
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
};

function ansiToHtml(text) {
  let out = '', depth = 0, i = 0;
  while (i < text.length) {
    if (text[i] === '\x1b' && i+1 < text.length && text[i+1] === ']') {
      // OSC hyperlink: \x1b]8;;URL\x1b\TEXT\x1b]8;;\x1b\
      const st = text.indexOf('\x1b\\', i+2);
      if (st === -1) { out += text[i++]; continue; }
      const osc = text.slice(i+2, st);
      i = st + 2;
      if (osc.startsWith('8;;')) {
        const url = osc.slice(3);
        if (url) {
          const closeIdx = text.indexOf('\x1b]8;;\x1b\\', i);
          const inner = closeIdx !== -1 ? text.slice(i, closeIdx) : '';
          i = closeIdx !== -1 ? closeIdx + 7 : i;
          const safeUrl = url.replace(/&/g,'&amp;').replace(/"/g,'&quot;');
          out += `<a href="${safeUrl}">${ansiToHtml(inner)}</a>`;
        }
      }
    } else if (text[i] === '\x1b' && i+1 < text.length && text[i+1] === '[') {
      const j = text.indexOf('m', i+2);
      if (j === -1) { out += text[i++]; continue; }
      const code = text.slice(i+2, j);
      i = j + 1;
      if (code === '0') { out += '</span>'.repeat(depth); depth = 0; }
      else if (A2H[code]) { out += `<span style="${A2H[code]}">`, depth++; }
    } else {
      const ch = text[i++];
      out += ch === '&' ? '&amp;' : ch === '<' ? '&lt;' : ch === '>' ? '&gt;' : ch;
    }
  }
  return out + '</span>'.repeat(depth);
}

function htmlWrap(ansiText, title = 'IPInfo') {
  const css = '*{box-sizing:border-box;margin:0;padding:0}' +
    'body{background:#000;color:#aaa;font-family:"Courier New",Consolas,monospace;' +
    'font-size:12px;line-height:1.5;padding:16px}' +
    'pre{font-family:inherit;white-space:pre;margin:0}' +
    'a{color:#4ec9b0;text-decoration:none}a:hover{text-decoration:underline}';
  return `<!DOCTYPE html><html><head><meta charset="utf-8">` +
    `<meta name="viewport" content="width=device-width,initial-scale=1">` +
    `<title>${title}</title><style>${css}</style></head>` +
    `<body><pre>${ansiToHtml(ansiText)}</pre></body></html>`;
}

function renderHelp(noColor) {
  const c = noColor ? (_, t) => t : (code, t) => `${code}${t}\x1b[0m`;
  const W = 60;
  const SEP = c(DC, '═'.repeat(W));
  const div = c(DC, '  ' + '─'.repeat(W - 2));
  const pad = (s, n) => s + ' '.repeat(Math.max(0, n - s.replace(/\x1b\[[^m]*m/g, '').length));
  const ex = (path, desc) => `  ${pad(c(BC, path), 44)} ${c(D, desc)}`;
  const op = (flag, desc) => `  ${pad(c(C, flag), 14)} ${c(D, desc)}`;
  return [
    SEP,
    `  ${c('\x1b[1;37m', 'cli.lapius7.com/ipinfo')}  ${c(D, '🌐 IP情報')}`,
    div, '',
    ex('curl cli.lapius7.com/ipinfo',         '自分のIPを調べる'),
    ex('curl cli.lapius7.com/ipinfo/1.2.3.4', '特定IPを調べる'),
    ex('curl cli.lapius7.com/ipinfo/8.8.8.8', '例: Google DNS'),
    '', div,
    `  ${c('\x1b[1;37m', 'オプション:')}`,
    op('?json',    'JSON形式で出力'),
    op('?nocolor', 'カラー無効'),
    '',
    SEP,
    c(DC, '  ?json  ?nocolor'),
  ].join('\n') + '\n';
}

function buildText(geo, hostname, noColor) {
  const c = noColor
    ? (_, t) => t
    : (code, t) => `${code}${t}${R}`;

  const fields = [
    ['ip',       geo.ip,                  null],
    ['hostname', hostname || '-',          null],
    ['city',     geo.city     || '-',      null],
    ['region',   geo.region   || '-',      null],
    ['country',  geo.countryCode || geo.country || '-', null],
    ['loc',      geo.ll || '-', geo.ll ? `https://maps.google.com/?q=${geo.ll}` : null],
    ['postal',   geo.postal   || '-',      null],
    ['timezone', geo.timezone || '-',      null],
    ['org',      geo.org      || '-',      null],
  ];

  const maxK = Math.max(...fields.map(([k]) => k.length)) + 1;
  const sep  = noColor ? '═'.repeat(45) : `${DC}${'═'.repeat(45)}${R}`;
  const hint = noColor ? '  ?json  ?nocolor' : `${DC}  ?json  ?nocolor${R}`;

  const renderVal = (v, url) => {
    if (!url || noColor) return v;
    return lnk(url, `${C}${v}${R}`);
  };

  const rows = fields.map(([k, v, url]) =>
    `${c(BC, (k + ':').padEnd(maxK))} ${renderVal(v, url)}`
  );

  return sep + '\n' + rows.join('\n') + '\n' + sep + '\n' + hint + '\n';
}

const server = http.createServer(async (req, res) => {
  const reqUrl = new URL(req.url, 'http://localhost');
  const query  = Object.fromEntries(reqUrl.searchParams.entries());
  const ua     = req.headers['user-agent'] || '';
  const browser  = isBrowser(ua);
  const noColor  = 'nocolor' in query || 'nc' in query || browser;
  const jsonMode = 'json' in query || (req.headers['accept'] || '').includes('application/json');

  const send = (body, type) => {
    res.writeHead(200, { 'Content-Type': type, 'Cache-Control': 'no-store' });
    res.end(body);
  };

  if (reqUrl.pathname === '/help') {
    if (browser) {
      send(htmlWrap(renderHelp(false), 'IPInfo - Help'), 'text/html; charset=utf-8');
    } else {
      send(renderHelp(noColor), 'text/plain; charset=utf-8');
    }
    return;
  }

  const rawIp   = decodeURIComponent(reqUrl.pathname.replace(/^\/+/, ''));
  const targetIp = (rawIp === 'me' || !rawIp) ? getClientIp(req) : rawIp;

  const [geo, hostname] = await Promise.all([
    lookupGeo(targetIp),
    lookupHostname(targetIp),
  ]);

  if (jsonMode) {
    const data = {
      ip:       geo.ip || targetIp,
      hostname: hostname || '',
      city:     geo.city,
      region:   geo.region,
      country:  geo.countryCode,
      loc:      geo.ll,
      postal:   geo.postal,
      timezone: geo.timezone,
      org:      geo.org,
    };
    send(JSON.stringify(data, null, 2) + '\n', 'application/json; charset=utf-8');
    return;
  }

  const text = buildText(geo, hostname, false);
  if (browser) {
    send(htmlWrap(text, `IPInfo - ${targetIp}`), 'text/html; charset=utf-8');
  } else {
    send(buildText(geo, hostname, noColor), 'text/plain; charset=utf-8');
  }
});

server.listen(PORT, '127.0.0.1', () => {
  console.log(`ipinfo listening on 127.0.0.1:${PORT}`);
});
