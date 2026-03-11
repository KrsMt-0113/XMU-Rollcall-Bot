import json
import threading
import uuid
import time
import socket
import os
from queue import Queue, Empty

from flask import Flask, request, jsonify, render_template
try:
    from pyngrok import ngrok
    _ngrok_available = True
except ImportError:
    ngrok = None
    _ngrok_available = False
from .parse_code import parse_sign_qr_code
from urllib.parse import urlparse, parse_qs

base_url = "https://lnt.xmu.edu.cn"

SESSION_TIMEOUT = 180

# Flask app with templates from this package's templates directory
_template_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
app = Flask(__name__, template_folder=_template_dir)
sessions = {}


def scan_url_analysis(e: str):
    if "/j?p=" in e and not e.startswith("http"):
        e = base_url + e

    if not e.startswith("http"):
        return e

    try:
        n = urlparse(e)
    except Exception:
        return e

    if n.path in ["/j", "/scanner-jumper"]:
        o = parse_qs(n.query)
        r = None
        try:
            a = o.get("_p", [None])[0]
            if a:
                r = json.loads(a)
        except Exception:
            pass

        if not r:
            p_value = o.get("p", [""])[0]
            r = parse_sign_qr_code(p_value)

        return json.dumps(r) if r and isinstance(r, dict) and r else e

    return e


@app.route("/scan/<sid>")
def scan_page(sid):
    if sid not in sessions:
        return "会话不存在或过期", 404
    return render_template("scan.html", sid=sid)


@app.route("/submit/<sid>", methods=["POST"])
def submit(sid):
    if sid not in sessions:
        return jsonify({"ok": False, "message": "会话无效或已过期"}), 404
    data = request.get_json(force=True)
    text = data.get("text")
    if not text:
        return jsonify({"ok": False, "message": "没有二维码内容"}), 400
    sessions[sid].put(text)
    return jsonify({"ok": True, "message": "已收到二维码内容"})


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def create_session(timeout=SESSION_TIMEOUT):
    sid = uuid.uuid4().hex
    q = Queue()
    sessions[sid] = q

    def expire():
        time.sleep(timeout)
        if sid in sessions:
            try:
                sessions[sid].put(None)
            except Exception:
                pass
            sessions.pop(sid, None)

    threading.Thread(target=expire, daemon=True).start()
    return sid, q


def _run_flask(port):
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


def send_qr(in_session, rollcall_id, ngrok_token, session_timeout=SESSION_TIMEOUT, max_retries=3):
    """
    Handle QR code rollcall by starting a local Flask server with ngrok tunnel.
    Returns True if rollcall was answered successfully, False otherwise.
    """
    global SESSION_TIMEOUT
    SESSION_TIMEOUT = session_timeout

    if not _ngrok_available:
        print("pyngrok 不可用（当前环境不支持 ngrok），无法进行二维码签到。")
        return False

    if not ngrok_token:
        print("ngrok token 未配置，无法进行二维码签到。")
        print("请运行 xmu config 并配置 ngrok token。")
        return False

    ngrok.set_auth_token(ngrok_token)

    port = 5001

    # Start Flask server in background thread
    flask_thread = threading.Thread(target=_run_flask, args=(port,), daemon=True)
    flask_thread.start()
    time.sleep(1)

    try:
        tunnel = ngrok.connect(str(port))

        tunnels = ngrok.get_tunnels()
        https_url = None
        http_url = None

        for t in tunnels:
            if t.public_url.startswith("https://"):
                https_url = t.public_url
            elif t.public_url.startswith("http://"):
                http_url = t.public_url

        if https_url:
            public_base = https_url.rstrip("/")
        elif http_url:
            public_base = http_url.rstrip("/")
            print("警告：使用 HTTP，浏览器可能无法访问摄像头。")
        else:
            public_base = tunnel.public_url.rstrip("/")

        attempts = 0
        while attempts < max_retries:
            attempts += 1
            sid, q = create_session()
            link = f"{public_base}/scan/{sid}"
            print(f"\n一次性扫码链接（有效期 {session_timeout}s，第 {attempts}/{max_retries} 次尝试）：")
            print(link)
            print("等待扫码并回传数据...")

            try:
                result = q.get(timeout=session_timeout + 5)
            except Empty:
                print("超时，未收到扫码数据。")
                continue

            if result is None:
                print("会话被过期或取消。")
                continue

            if result:
                try:
                    data = json.loads(scan_url_analysis(result))
                except (json.JSONDecodeError, TypeError):
                    print("二维码内容解析失败，请重新扫码。")
                    continue

                if "data" not in data:
                    print("二维码内容缺少签到数据字段，请重新扫码。")
                    continue

                rollcall_url = f"{base_url}/api/rollcall/{rollcall_id}/answer_qr_rollcall"
                body = {
                    "data": data["data"],
                    "deviceId": str(uuid.uuid4()),
                }
                headers = {
                    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) "
                                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                                  "Chrome/141.0.0.0 Mobile Safari/537.36 Edg/141.0.0.0",
                    "Content-Type": "application/json",
                }

                res = in_session.put(rollcall_url, headers=headers, json=body)

                if res.status_code == 200:
                    print("二维码签到成功!")
                    return True
                else:
                    print("签到失败，服务器返回状态码:", res.status_code)
                    try:
                        print(res.json())
                    except Exception:
                        pass
                    # Will retry with a new link if attempts remain
                    continue

        print(f"已达到最大重试次数 ({max_retries})，二维码签到失败。")
        return False

    finally:
        try:
            ngrok.kill()
        except Exception:
            pass
