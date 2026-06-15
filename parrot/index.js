const fs = require('mz/fs');
const path = require('path');
const http = require('http');
const url = require('url');
const { Readable } = require('stream');
const colors = require('colors/safe');
colors.enabled = true;

let original = [];
let flipped = [];

(async () => {
  const framesPath = 'frames';
  const files = await fs.readdir(framesPath);
  original = await Promise.all(files.map(async (file) => {
    const frame = await fs.readFile(path.join(framesPath, file));
    return frame.toString();
  }));
  flipped = original.map(f => f.toString().split('').reverse().join(''));
})().catch((err) => {
  console.log('Error loading frames');
  console.log(err);
});

const colorsOptions = ['red', 'yellow', 'green', 'blue', 'magenta', 'cyan', 'white'];
const numColors = colorsOptions.length;
const selectColor = previousColor => {
  let color;
  do { color = Math.floor(Math.random() * numColors); } while (color === previousColor);
  return color;
};

function streamer(stream, opts) {
  const frames = opts.flip ? flipped : original;
  let index = 0;
  let lastColor;
  let timer;

  function tick() {
    stream.push('[2J[3J[H');
    const colorIdx = lastColor = selectColor(lastColor);
    const coloredFrame = colors[colorsOptions[colorIdx]](frames[index]);
    const ok = stream.push(coloredFrame);
    index = (index + 1) % frames.length;
    if (ok) {
      timer = setTimeout(tick, 70);
    } else {
      stream.once('drain', () => { timer = setTimeout(tick, 70); });
    }
  }

  tick();
  return () => { clearTimeout(timer); };
}

const validateQuery = ({ flip }) => ({ flip: String(flip).toLowerCase() === 'true' });

const ANSI_COLORS = {
  '31': '#ff5555', '32': '#55ff55', '33': '#ffff55',
  '34': '#5555ff', '35': '#ff55ff', '36': '#55ffff', '37': '#ffffff',
};

const HTML_PAGE = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>parrot - Clilap</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body {
      background: #000;
      width: 100%; height: 100vh;
      display: flex;
      align-items: center; justify-content: center;
      overflow: hidden;
    }
    #screen {
      font-family: "Courier New", Courier, monospace;
      font-size: 15px;
      line-height: 1.25;
      white-space: pre;
      color: #fff;
    }
    #info {
      position: fixed; bottom: 14px; right: 16px;
      color: #333; font-family: "Courier New", monospace; font-size: 12px;
    }
    #info a { color: #4ec9b0; text-decoration: none; }
    #info a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <pre id="screen"></pre>
  <div id="info">
    <a href="https://clilap.org">clilap.org</a>
    &nbsp;&middot;&nbsp;
    <code>curl clilap.org/parrot</code>
  </div>
  <script>
    const COLORS = ${JSON.stringify(ANSI_COLORS)};
    const screen = document.getElementById('screen');
    let es;
    function connect() {
      if (es) es.close();
      es = new EventSource('/parrot/frames');
      es.onmessage = (e) => {
        const raw = atob(e.data);
        const m = raw.match(/^\\x1b\\[(\\d+)m/);
        screen.style.color = m ? (COLORS[m[1]] || '#fff') : '#fff';
        screen.textContent = raw.replace(/\\x1b\\[[^m]*m/g, '');
      };
      es.onerror = () => { es.close(); setTimeout(connect, 2000); };
    }
    connect();
  </script>
</body>
</html>`;

function startStream(res, reqUrl) {
  const opts = validateQuery(url.parse(reqUrl, true).query);
  const stream = new Readable({ read() {} });
  res.writeHead(200, {
    'Content-Type': 'text/plain; charset=utf-8',
    'Cache-Control': 'no-cache',
    'X-Accel-Buffering': 'no',
  });
  stream.pipe(res);
  const cleanupLoop = streamer(stream, opts);
  const onClose = () => { cleanupLoop(); stream.destroy(); };
  res.on('close', onClose);
  res.on('error', onClose);
}

const server = http.createServer((req, res) => {
  if (req.url === '/healthcheck') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    return res.end(JSON.stringify({ status: 'ok' }));
  }

  // /stream endpoint — raw ANSI for curl
  if (req.url === '/stream' || req.url.startsWith('/stream?')) {
    return startStream(res, req.url);
  }

  // /frames endpoint — SSE for browser xterm.js
  if (req.url === '/frames') {
    const opts = { flip: false };
    const frames = original;
    let index = 0;
    let lastColor;

    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'X-Accel-Buffering': 'no',
    });

    const timer = setInterval(() => {
      if (res.writableEnded) return;
      const colorIdx = lastColor = selectColor(lastColor);
      const frame = colors[colorsOptions[colorIdx]](frames[index]);
      index = (index + 1) % frames.length;
      const encoded = Buffer.from(frame).toString('base64');
      res.write(`data: ${encoded}\n\n`);
    }, 70);

    const cleanup = () => { clearInterval(timer); };
    res.on('close', cleanup);
    res.on('error', cleanup);
    return;
  }

  const ua = (req.headers['user-agent'] || '').toLowerCase();
  const isCurl = ua.includes('curl') || ua.includes('wget') || ua.includes('fetch') || ua.includes('python');

  if (!isCurl) {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    return res.end(HTML_PAGE);
  }

  startStream(res, req.url);
});

const port = process.env.PARROT_PORT || 3000;
server.listen(port, err => {
  if (err) throw err;
  console.log(`Listening on http://localhost:${port}`);
});
