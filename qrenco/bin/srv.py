#!/usr/bin/env python

import gevent
from gevent.pywsgi import WSGIServer
from gevent.queue import Queue
from gevent.monkey import patch_all

patch_all()

import sys
import logging
import os
import re
import requests
import socket
import subprocess
import time
import traceback
import dateutil.parser
import json

import jinja2
from flask import (
    Flask,
    request,
    render_template,
    send_from_directory,
    send_file,
    make_response,
    redirect,
)

app = Flask(__name__)

MYDIR = os.path.abspath(os.path.dirname(os.path.dirname("__file__")))
sys.path.append("%s/lib/" % MYDIR)

from globals import FILE_QUERIES_LOG, LOG_FILE, TEMPLATES, STATIC, log, error

from qrencode_wrapper import qrencode_wrapper

if not os.path.exists(os.path.dirname(LOG_FILE)):
    os.makedirs(os.path.dirname(LOG_FILE))
logging.basicConfig(
    filename=LOG_FILE, level=logging.DEBUG, format="%(asctime)s %(message)s"
)

my_loader = jinja2.ChoiceLoader(
    [
        app.jinja_loader,
        jinja2.FileSystemLoader(TEMPLATES),
    ]
)
app.jinja_loader = my_loader


def is_html_needed(user_agent):
    plaintext_clients = [
        "curl",
        "wget",
        "fetch",
        "httpie",
        "lwp-request",
        "python-requests",
    ]
    if any([x in user_agent for x in plaintext_clients]):
        return False
    return True


def parse_args(args):
    result = {}

    q = ""
    for key, val in list(args.items()):
        if len(val) == 0:
            q += key
            continue

    if q is None:
        return result
    if "T" in q:
        result["no-terminal"] = True
    if "q" in q:
        result["quiet"] = True

    for key, val in list(args.items()):
        if val == "True":
            val = True
        if val == "False":
            val = False
        result[key] = val

    return result


@app.route("/files/<path:path>")
def send_static(path):
    return send_from_directory(STATIC, path)


@app.route("/favicon.ico")
def send_favicon():
    return send_from_directory(STATIC, "favicon.ico")


@app.route("/malformed-response.html")
def send_malformed():
    return send_from_directory(STATIC, "malformed-response.html")


def log_query(ip, found, topic, user_agent):
    log_entry = "%s %s %s %s" % (ip, found, topic, user_agent)
    with open(FILE_QUERIES_LOG, "a") as my_file:
        my_file.write(log_entry + "\n")


@app.route("/help", methods=["GET"])
def help_page():
    ua = request.headers.get("User-Agent", "").lower()
    no_color = "nocolor" in request.args or "nc" in request.args
    is_curl = any(x in ua for x in ("curl", "wget", "python", "httpie"))

    ESC = "\x1b"
    def c(code, text):
        return text if no_color else f"{ESC}[{code}m{text}{ESC}[0m"

    W = 60
    SEP = c("2;36", "═" * W)
    div = c("2;36", "  " + "─" * (W - 2))
    lines = [
        SEP,
        f"  {c('1;37', 'cli.lapius7.com/qr')}  {c('2', '🔲 QRコード生成')}",
        div, "",
        f"  {c('1;36', 'curl cli.lapius7.com/qr/Hello')}",
        f"  {c('1;36', 'curl cli.lapius7.com/qr/https://lapius7.com')}",
        "", div,
        f"  {c('1;37', 'オプション:')}",
        f"  {c('36', '?size=N')}     セルサイズ 1-10 (デフォルト1)",
        f"  {c('36', '?margin=N')}   余白サイズ 0-10 (デフォルト1)",
        f"  {c('36', '?level=L|M|Q|H')}  誤り訂正レベル (デフォルトM)",
        f"  {c('36', '?compact')}    コンパクト表示 (半ブロック文字)",
        f"  {c('36', '?invert')}     色反転 (白背景ターミナル用)",
        "",
        f"  {c('2', '例: curl cli.lapius7.com/qr/Hello?size=3&level=H')}",
        "",
        SEP,
        c("2;36", "  ?size=N  ?margin=N  ?level=L|M|Q|H  ?compact  ?invert"),
    ]
    body = "\n".join(lines) + "\n"
    return body, 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.route("/", methods=["GET", "POST"])
@app.route("/<path:topic>", methods=["GET", "POST"])
def answer(topic=None):
    """
    Main rendering function, it processes incoming weather queries.
    Depending on user agent it returns output in HTML or ANSI format.

    Incoming data:
        request.args
        request.headers
        request.remote_addr
        request.referrer
        request.query_string
    """

    user_agent = request.headers.get("User-Agent", "").lower()
    html_needed = is_html_needed(user_agent)
    options = parse_args(request.args)

    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
        if ip.startswith("::ffff:"):
            ip = ip[7:]
    else:
        ip = request.remote_addr
    if request.headers.getlist("X-Forwarded-For"):
        ip = request.headers.getlist("X-Forwarded-For")[0]
        if ip.startswith("::ffff:"):
            ip = ip[7:]
    else:
        ip = request.remote_addr

    if request.method == "POST":
        data = ""
        for k, v in list(request.form.items()):
            if k == "":
                if topic is None:
                    topic_name = "UNNAMED"
                else:
                    topic_name = topic
                data = v
            else:
                if v == "":
                    if topic is None:
                        topic_name = "UNNAMED"
                    else:
                        topic_name = topic
                    cheatsheet = k
                else:
                    topic_name = k
                    data = v

            answer, found = qrencode_wrapper(
                query_string=data, html=is_html_needed(user_agent)
            )

        return answer
        # if html_needed:
        #     return redirect("/")
        # else:
        #     return "OK\n"

    if "topic" in request.args:
        return redirect("/%s" % request.args.get("topic"))

    query_string = request.url
    if query_string.startswith("http://"):
        query_string = query_string[7:]
    elif query_string.startswith("https://"):
        query_string = query_string[8:]

    query_string = query_string[query_string.index("/") + 1 :]
    # Strip service query params from QR content (e.g. ?size=2&level=H)
    if "?" in query_string:
        query_string = query_string[:query_string.index("?")]

    answer, found = qrencode_wrapper(
        query_string=query_string,
        request_options=options,
        html=is_html_needed(user_agent),
    )

    log_query(ip, found, topic, user_agent)
    return answer


server = WSGIServer(("127.0.0.1", 3207), app)  # log=None)
server.serve_forever()
