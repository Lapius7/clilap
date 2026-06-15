import gevent
from gevent.monkey import patch_all
from gevent.subprocess import Popen, PIPE, STDOUT

patch_all()

import sys
import os

MYDIR = os.path.abspath(os.path.dirname(os.path.dirname("__file__")))
sys.path.append("%s/lib/" % MYDIR)
from buttons import GITHUB_BUTTON_FOOTER

INTERNAL_TOPICS = [":firstpage"]


def github_button(button):
    repository = {
        "qrenco.de": "chubin/qrenco.de",
        "libqrencode": "fukuchi/libqrencode",
    }

    full_name = repository.get(button, "")
    if not full_name:
        return ""

    short_name = full_name.split("/", 1)[1]
    button = (
        "<!-- Place this tag where you want the button to render. -->"
        '<a aria-label="Star %(full_name)s on GitHub" data-count-aria-label="# stargazers on GitHub"'
        ' data-count-api="/repos/%(full_name)s#stargazers_count"'
        ' data-count-href="/%(full_name)s/stargazers"'
        ' data-icon="octicon-star"'
        ' href="https://github.com/%(full_name)s"'
        '  class="github-button">%(short_name)s</a>'
    ) % locals()
    return button


def html_wrapper(answer):
    if isinstance(answer, bytes):
        answer = answer.decode('utf-8', errors='replace')
    answer = answer.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    css = ('*{box-sizing:border-box;margin:0;padding:0}'
           'body{background:#000;color:#fff;'
           'font-family:"Courier New",Consolas,Monaco,"Lucida Console",monospace;'
           'font-size:14px;line-height:1.2;padding:16px}'
           'pre{font-family:inherit;white-space:pre;margin:0}'
           '.footer{margin-top:16px;padding-top:6px;border-top:1px solid #1a1a1a;'
           'color:#333;font-size:11px}')
    return (
        '<!DOCTYPE html><html><head>'
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>qr - Clilap</title>'
        f'<style>{css}</style></head>'
        f'<body><pre>{answer}</pre>'
        '<div class="footer">©2025 CLI Lap by Lapius7. All rights reserved.</div>'
        '</body></html>'
    )


def get_internal(topic):
    return open(os.path.join(MYDIR, "share", topic[1:] + ".txt"), "r").read()


def qrencode_wrapper(query_string="", request_options=None, html=False):
    opts = request_options or {}

    if query_string == "":
        query_string = ":firstpage"

    if query_string in INTERNAL_TOPICS:
        answer = get_internal(query_string)
    else:
        # Output format
        fmt = "ANSIUTF8" if "compact" in opts else "UTF8"
        cmd = ["qrencode", "-t", fmt, "-o", "-"]

        # Size: 1-10, default 1 for terminal
        try:
            size = max(1, min(10, int(opts.get("size", 1))))
        except (ValueError, TypeError):
            size = 1
        cmd += ["-s", str(size)]

        # Margin: 0-10, default 1
        try:
            margin = max(0, min(10, int(opts.get("margin", 1))))
        except (ValueError, TypeError):
            margin = 1
        cmd += ["-m", str(margin)]

        # Error correction: L/M/Q/H, default M
        level = str(opts.get("level", "M")).upper()
        if level not in ("L", "M", "Q", "H"):
            level = "M"
        cmd += ["-l", level]

        # Invert colors
        if "invert" in opts:
            cmd += ["--foreground=FFFFFF", "--background=000000"]

        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT)
        answer = p.communicate(query_string.encode("utf-8"))[0]

    if html:
        return html_wrapper(answer), True
    else:
        return answer, True
